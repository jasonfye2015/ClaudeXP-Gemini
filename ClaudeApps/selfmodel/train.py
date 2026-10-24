"""Fine-tuning Gemma 3 4B on your chats (selfmodel/export.py's data): QLoRA on one GTX 1080 Ti.

Run with the training environment's Python (Local Storage/LLM Models/selfmodel/env):

    env\\Scripts\\python.exe -m selfmodel.train --bench          a short run: speed, memory, and the time the whole set takes
    env\\Scripts\\python.exe -m selfmodel.train --hours 8        the real run (stops at the time limit, saving as it goes)
    env\\Scripts\\python.exe -m selfmodel.train --resume         carry on from the last checkpoint

Choices made for the card (Pascal, 11 GB): the base weights are 4-bit (bitsandbytes NF4) and everything is computed in
32-bit float - this GPU is ~64x slower at half precision, and Gemma overflows in it anyway. Gemma's vocabulary is
262k tokens, so the output layer is only run on the positions being learned (your replies), not every position.
Conversations go one at a time with gradients accumulated; gradient checkpointing keeps activations small.

Memory is kept well under the card's 11 GB on purpose: on Windows the NVIDIA driver doesn't fail when video memory
runs out, it quietly spills into system RAM and everything runs ~30x slower. So Gemma 3's image encoder (unused here,
~1.6 GB in 32-bit) is dropped after loading, and the output layer is applied to the learned positions in chunks of
128, each recomputed in the backward pass, instead of holding scores over the whole vocabulary at once.

Writes to Local Storage/LLM Models/selfmodel/: adapter/ (the LoRA weights, the result), checkpoints/, train_log.jsonl.

Another base model and data set, kept in a run folder of its own (runs/<name>/adapter, checkpoints, train_log.jsonl):

    python -m selfmodel.train --run nemomix-adult --base base-nemomix --data data-adult --embed-cpu --optim adamw8bit

Mistral-family models (NemoMix and friends) are trained in ChatML, the format they're run with; Gemma in its own.
--embed-cpu keeps the vocabulary table in system memory, where looking a word up costs nothing, and quantizes the
output layer to 4-bit like the rest: what lets a 12B fit on an 11 GB card.
"""
import argparse
import json
import math
import os
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "Local Storage" / "LLM Models" / "selfmodel"
DATA = ROOT / "data"
BASE = ROOT / "base"                  # the base model, downloaded once (fetch.py)
OUT = ROOT / "adapter"
CKPT = ROOT / "checkpoints"
LOG = ROOT / "train_log.jsonl"
TARGETS = r".*language_model.*\.(q_proj|k_proj|v_proj|o_proj|gate_proj|up_proj|down_proj)$"
TARGETS_TEXT = r".*layers\.\d+\..*\.(q_proj|k_proj|v_proj|o_proj|gate_proj|up_proj|down_proj)$"   # Mistral, Llama...


class SlicedHead:
    """An output layer kept as several 4-bit slices of the vocabulary (see --embed-cpu). Built lazily as a torch
    module the first time it's made, so importing this file doesn't need torch."""

    def __new__(cls, weight, parts):
        import bitsandbytes as bnb
        import torch

        class _SlicedHead(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.in_features, self.out_features = weight.shape[1], weight.shape[0]
                self.slices = torch.nn.ModuleList()
                for chunk in torch.chunk(weight, parts, dim=0):
                    q = bnb.nn.Linear4bit(chunk.shape[1], chunk.shape[0], bias=False, compute_dtype=torch.float32,
                                          quant_type="nf4", compress_statistics=True)
                    q.weight = bnb.nn.Params4bit(chunk.contiguous(), requires_grad=False, quant_type="nf4",
                                                 compress_statistics=True)
                    self.slices.append(q.to("cuda"))

            def forward(self, h):
                return torch.cat([s(h) for s in self.slices], dim=-1)

        return _SlicedHead()


def use_run(name):
    """Point the outputs at runs/<name>/ (or the top folder when no run is named, as the first model was)."""
    global OUT, CKPT, LOG
    folder = ROOT / "runs" / name if name else ROOT
    folder.mkdir(parents=True, exist_ok=True)
    OUT, CKPT, LOG = folder / "adapter", folder / "checkpoints", folder / "train_log.jsonl"


def stay_awake(folder):
    """While training runs: ask Windows not to sleep, and touch a tiny file in `folder` every minute. Once the model is
    loaded, training hardly touches the drive, and Windows' USB selective suspend can put an external SSD to sleep -
    some don't wake up again, and the drive drops off ("surprise removed") mid-run. Changes no settings; it all
    stops when the process ends."""
    import threading
    if os.name == "nt":
        try:
            import ctypes
            ES_CONTINUOUS, ES_SYSTEM_REQUIRED = 0x80000000, 0x00000001
            ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)
        except Exception:
            pass
    beat = Path(folder) / ".keepawake"

    def touch():
        while True:
            try:
                beat.write_text(time.strftime("%Y-%m-%d %H:%M:%S"), encoding="utf-8")
                os.listdir(folder)
            except OSError:
                pass
            time.sleep(60)
    threading.Thread(target=touch, daemon=True).start()


def log(entry):
    entry["time"] = time.strftime("%Y-%m-%d %H:%M:%S")
    print(json.dumps(entry), flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def encode(tok, messages, max_len, fmt="gemma"):
    """The chat format, token by token: (input ids, labels) with labels only on your replies (and the end-of-turn
    marker that closes each, so the model learns where you stop). fmt: "gemma" or "chatml"."""
    if fmt == "chatml":
        return encode_chatml(tok, messages, max_len)
    system = ""
    ids, labels = [tok.bos_token_id], [-100]
    first_user = True
    for m in messages:
        if m["role"] == "system":
            system = m["content"]
            continue
        if m["role"] == "user":
            text = (system + "\n\n" + m["content"]) if first_user and system else m["content"]
            first_user = False
            part = tok(f"<start_of_turn>user\n{text}<end_of_turn>\n<start_of_turn>model\n", add_special_tokens=False)["input_ids"]
            ids += part
            labels += [-100] * len(part)
        else:
            part = tok(f"{m['content']}<end_of_turn>\n", add_special_tokens=False)["input_ids"]
            ids += part
            labels += part
    if len(ids) > max_len:
        ids, labels = ids[:max_len], labels[:max_len]
    return ids, labels


def encode_chatml(tok, messages, max_len):
    """ChatML: <|im_start|>role\n...<|im_end|>\n, with the "<|im_start|>assistant\n" header after each of their
    turns as context, and your reply plus its <|im_end|> as what's learned."""
    ids = [tok.bos_token_id] if tok.bos_token_id is not None else []
    labels = [-100] * len(ids)
    for m in messages:
        if m["role"] in ("system", "user"):
            part = f"<|im_start|>{m['role']}\n{m['content']}<|im_end|>\n"
            if m["role"] == "user":
                part += "<|im_start|>assistant\n"
            got = tok(part, add_special_tokens=False)["input_ids"]
            ids += got
            labels += [-100] * len(got)
        else:
            got = tok(f"{m['content']}<|im_end|>\n", add_special_tokens=False)["input_ids"]
            ids += got
            labels += got
    if len(ids) > max_len:
        ids, labels = ids[:max_len], labels[:max_len]
    return ids, labels


def load(path, tok, max_len, limit=None, seed=0, fmt="gemma"):
    rows = [json.loads(line) for line in open(path, encoding="utf-8")]
    random.Random(seed).shuffle(rows)
    if limit:
        rows = rows[:limit]
    out = []
    for r in rows:
        ids, labels = encode(tok, r["messages"], max_len, fmt)
        if any(l != -100 for l in labels):
            out.append((ids, labels))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--hours", type=float, default=8.0, help="stop after this long (saving the adapter)")
    ap.add_argument("--bench", action="store_true", help="time 30 conversations and estimate the whole run")
    ap.add_argument("--resume", action="store_true", help="carry on from the last checkpoint")
    ap.add_argument("--epochs", type=float, default=1.0)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--rank", type=int, default=16)
    ap.add_argument("--accum", type=int, default=16, help="conversations per optimiser step")
    ap.add_argument("--max-len", type=int, default=1280)
    ap.add_argument("--eval-every", type=int, default=150, help="optimiser steps between validation checks")
    ap.add_argument("--save-minutes", type=float, default=30)
    ap.add_argument("--run", default="", help="keep this run's adapter, checkpoints and log in runs/<name>/")
    ap.add_argument("--base", default="base", help="the base model's folder in selfmodel/ (e.g. base-nemomix)")
    ap.add_argument("--data", default="data", help="the training data's folder in selfmodel/ (e.g. data-adult)")
    ap.add_argument("--format", default="auto", choices=["auto", "gemma", "chatml"])
    ap.add_argument("--embed-cpu", action="store_true", help="vocabulary table in system memory, output layer 4-bit")
    ap.add_argument("--optim", default="adamw", choices=["adamw", "adamw8bit"])
    args = ap.parse_args(argv)
    use_run(args.run)
    stay_awake(LOG.parent)                  # keep Windows and the external drive from dozing off mid-run
    base_dir, data_dir = ROOT / args.base, ROOT / args.data

    import torch
    from peft import LoraConfig, PeftModel, get_peft_model, prepare_model_for_kbit_training
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, get_cosine_schedule_with_warmup

    torch.backends.cuda.matmul.allow_tf32 = False
    ROOT.mkdir(parents=True, exist_ok=True)
    if not (base_dir / "config.json").exists():
        sys.exit(f"No base model in {base_dir}: run selfmodel.fetch first.")
    model_type = json.loads((base_dir / "config.json").read_text()).get("model_type", "")
    fmt = args.format if args.format != "auto" else ("gemma" if model_type.startswith("gemma") else "chatml")
    tok = AutoTokenizer.from_pretrained(base_dir)
    # the output layer: 32-bit for Gemma (as the first model was made), 4-bit with --embed-cpu
    skip = ["vision_tower", "multi_modal_projector"] + ([] if args.embed_cpu else ["lm_head"])
    quant = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_use_double_quant=True,
                               bnb_4bit_compute_dtype=torch.float32, llm_int8_skip_modules=skip)
    model = AutoModelForCausalLM.from_pretrained(base_dir, quantization_config=quant,
                                                 dtype=torch.float16 if args.embed_cpu else torch.float32,
                                                 device_map={"": 0},
                                                 attn_implementation="eager" if fmt == "gemma" else "sdpa")
    if args.embed_cpu:
        import bitsandbytes as bnb
        embed = model.get_input_embeddings()
        embed.to("cpu", dtype=torch.float32)
        embed.register_forward_pre_hook(lambda _m, inputs: tuple(x.to("cpu") for x in inputs))
        embed.register_forward_hook(lambda _m, _inputs, output: output.to("cuda"))
        # the output layer in 8 slices of the vocabulary, each 4-bit: a 4-bit layer is unpacked to 32-bit whole every
        # time it's used, which for 131k words x 5120 is 2.7 GB at once - in slices it's a few hundred MB at a time
        head = model.get_output_embeddings()
        if isinstance(head, bnb.nn.Linear4bit):
            full = bnb.functional.dequantize_4bit(head.weight.data, head.weight.quant_state).to("cpu", torch.float16)
        else:
            full = head.weight.data.to("cpu", torch.float16)
        del head
        model.set_output_embeddings(SlicedHead(full, 8))
        del full
        torch.cuda.empty_cache()
        print(f"vocabulary table: {embed.weight.device} {embed.weight.dtype}; output layer: "
              f"{type(model.get_output_embeddings()).__name__}; graphics memory after loading: "
              f"{torch.cuda.memory_allocated() / 2**30:.2f} GB", flush=True)
    for name in ("vision_tower", "multi_modal_projector"):        # text only: the image side isn't needed
        holder = model.model if hasattr(model.model, name) else model
        if getattr(holder, name, None) is not None:
            setattr(holder, name, torch.nn.Identity())
    torch.cuda.empty_cache()
    model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True,
                                            gradient_checkpointing_kwargs={"use_reentrant": False})
    if args.resume and (CKPT / "latest" / "adapter_config.json").exists():
        model = PeftModel.from_pretrained(model, CKPT / "latest", is_trainable=True)
        state = json.loads((CKPT / "latest" / "state.json").read_text())
    else:
        model = get_peft_model(model, LoraConfig(r=args.rank, lora_alpha=args.rank * 2, lora_dropout=0.05,
                                                 target_modules=TARGETS if fmt == "gemma" else TARGETS_TEXT, task_type="CAUSAL_LM"))
        state = {"step": 0, "seen": 0, "tokens": 0}
    model.print_trainable_parameters()

    # the decoder body and the output layer, so the output layer runs only where there's something to learn
    inner = model.get_base_model()
    body = inner.model if hasattr(inner, "model") else inner
    lm_head = inner.lm_head
    cfg = getattr(inner.config, "text_config", inner.config)
    softcap = getattr(cfg, "final_logit_softcapping", None)

    from torch.utils.checkpoint import checkpoint

    def chunk_loss(h, target):
        logits = lm_head(h).float()
        if softcap:
            logits = torch.tanh(logits / softcap) * softcap
        return torch.nn.functional.cross_entropy(logits, target, reduction="sum")

    def loss_of(ids, labels):
        x = torch.tensor([ids], device="cuda")
        y = torch.tensor(labels[1:], device="cuda")
        out = body(input_ids=x, use_cache=False)
        hidden = out.last_hidden_state[0, :-1]
        keep = y != -100
        h, target = hidden[keep], y[keep]
        total = 0
        for a in range(0, h.shape[0], 128):            # the vocabulary is huge: score it 128 positions at a time
            if torch.is_grad_enabled():
                total = total + checkpoint(chunk_loss, h[a:a + 128], target[a:a + 128], use_reentrant=False)
            else:
                total = total + chunk_loss(h[a:a + 128], target[a:a + 128])
        return total, int(keep.sum())

    train = load(data_dir / "train.jsonl", tok, args.max_len, limit=30 if args.bench else None, fmt=fmt)
    val = load(data_dir / "val.jsonl", tok, args.max_len, limit=60, seed=1, fmt=fmt)
    total_steps = max(1, math.ceil(len(train) * args.epochs / args.accum))
    params = [p for p in model.parameters() if p.requires_grad]
    if args.optim == "adamw8bit":
        import bitsandbytes as bnb
        opt = bnb.optim.AdamW8bit(params, lr=args.lr, weight_decay=0.0)
    else:
        opt = torch.optim.AdamW(params, lr=args.lr, weight_decay=0.0)
    sched = get_cosine_schedule_with_warmup(opt, min(50, total_steps // 10 + 1), total_steps)
    if args.resume and (CKPT / "latest" / "optimizer.pt").exists():
        opt.load_state_dict(torch.load(CKPT / "latest" / "optimizer.pt"))
        sched.load_state_dict(torch.load(CKPT / "latest" / "scheduler.pt"))

    def evaluate():
        model.eval()
        tot, n = 0.0, 0
        with torch.no_grad():
            for ids, labels in val:
                l, k = loss_of(ids, labels)
                tot += float(l)
                n += k
        model.train()
        return tot / max(1, n)

    def save(where):
        where.mkdir(parents=True, exist_ok=True)
        model.save_pretrained(where)
        tok.save_pretrained(where)
        torch.save(opt.state_dict(), where / "optimizer.pt")
        torch.save(sched.state_dict(), where / "scheduler.pt")
        (where / "state.json").write_text(json.dumps(state))

    log({"event": "start", "train": len(train), "val": len(val), "steps": total_steps, "resume_at": state["step"],
         "bench": args.bench, "base": args.base, "data": args.data, "format": fmt, "max_len": args.max_len})
    if not args.bench:
        log({"event": "eval", "step": state["step"], "val_loss": round(evaluate(), 4)})
    model.train()
    started, last_save = time.time(), time.time()
    torch.cuda.reset_peak_memory_stats()
    order = list(range(len(train)))
    random.Random(state["step"]).shuffle(order)
    i = state["seen"] % len(train)
    acc_loss, acc_tokens, step_tokens = 0.0, 0, 0
    run_tokens = 0
    while state["step"] < total_steps:
        ids, labels = train[order[i % len(order)]]
        loss, k = loss_of(ids, labels)
        (loss / max(1, k) / args.accum).backward()
        acc_loss += float(loss)
        acc_tokens += k
        step_tokens += len(ids)
        run_tokens += len(ids)
        i += 1
        state["seen"] += 1
        if state["seen"] % args.accum:
            continue
        torch.nn.utils.clip_grad_norm_(params, 1.0)
        opt.step()
        sched.step()
        opt.zero_grad(set_to_none=True)
        state["step"] += 1
        state["tokens"] += step_tokens
        elapsed = time.time() - started
        speed = run_tokens / max(1e-6, elapsed)
        if state["step"] % 5 == 0 or args.bench:
            log({"event": "step", "step": state["step"], "of": total_steps, "loss": round(acc_loss / max(1, acc_tokens), 4),
                 "tok_per_s": round(speed, 1), "lr": sched.get_last_lr()[0],
                 "gpu_gb": round(torch.cuda.max_memory_allocated() / 2**30, 2)})
        acc_loss, acc_tokens, step_tokens = 0.0, 0, 0
        if args.bench:
            continue
        if state["step"] % args.eval_every == 0:
            log({"event": "eval", "step": state["step"], "val_loss": round(evaluate(), 4)})
        if time.time() - last_save > args.save_minutes * 60:
            save(CKPT / "latest")
            last_save = time.time()
        if elapsed > args.hours * 3600:
            log({"event": "time_up", "step": state["step"], "hours": round(elapsed / 3600, 2)})
            break
    if args.bench:
        all_tokens = sum(len(x[0]) for x in load(data_dir / "train.jsonl", tok, args.max_len, fmt=fmt))
        speed = run_tokens / max(1e-6, time.time() - started)
        log({"event": "bench", "tok_per_s": round(speed, 1), "gpu_peak_gb": round(torch.cuda.max_memory_allocated() / 2**30, 2),
             "dataset_tokens": all_tokens, "hours_for_one_epoch": round(all_tokens / speed / 3600, 1),
             "tokens_in_8_hours": int(speed * 8 * 3600)})
        return
    save(CKPT / "latest")
    log({"event": "eval", "step": state["step"], "val_loss": round(evaluate(), 4)})
    model.save_pretrained(OUT)
    tok.save_pretrained(OUT)
    log({"event": "done", "adapter": str(OUT), "steps": state["step"], "tokens": state["tokens"]})


if __name__ == "__main__":
    main()
