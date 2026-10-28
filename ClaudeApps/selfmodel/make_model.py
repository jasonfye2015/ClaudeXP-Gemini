"""After training: turn the adapter into a model file the Timeline can run.

    env\\Scripts\\python.exe -m selfmodel.make_model                      the finished adapter -> Kithylin AI's Models folder
    env\\Scripts\\python.exe -m selfmodel.make_model --adapter PATH --name kithylin-step60
    env\\Scripts\\python.exe -m selfmodel.make_model --install-timeline    also install it for the Timeline's own programs

Three steps, all on the CPU (the graphics card can stay busy training):
  1. merge     the base model (16-bit, on the CPU) with the LoRA adapter folded into its weights -> work/<name>/merged
  2. convert   llama.cpp's converter (Local Storage/LLM Models/llama.cpp/src-b11533) -> a 16-bit .gguf
  3. quantize  llama-quantize -> Q4_K_M (about 2.5 GB), the same size the Timeline's other models use
For a big base (a 12B: merging would need ~50 GB of working space) there's --lora-on instead: the adapter alone is
converted to a small GGUF add-on that the engine applies on top of the base's own quantized file at load time
(llama-server --lora), e.g.

    python -m selfmodel.make_model --run nemomix-adult --base base-nemomix --lora-on nemomix-unleashed-12b --name kithylin-nemomix-adult

The result goes to ClaudeApps/kithylinai/Models/<name>/ with an info.json; --install-timeline copies it into
Local Storage/LLM Models/models/<name>/ too, so ClaudeAI and the residents can use it. The 16-GB of working files
are deleted afterwards unless --keep is given. Takes about 15-25 minutes; needs about 12 GB of free RAM.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

TIMELINE = Path(__file__).resolve().parents[2]
LLM = TIMELINE / "Local Storage" / "LLM Models"
ROOT = LLM / "selfmodel"
BASE = ROOT / "base"
ADAPTER = ROOT / "adapter"
WORK = ROOT / "work"
CONVERTER = LLM / "llama.cpp" / "src-b11533" / "convert_hf_to_gguf.py"
QUANTIZERS = [LLM / "llama.cpp" / "cuda" / "llama-quantize.exe", LLM / "llama.cpp" / "vulkan" / "llama-quantize.exe"]
KITHYLIN_MODELS = TIMELINE / "ClaudeApps" / "kithylinai" / "Models"
TIMELINE_MODELS = LLM / "models"


def say(msg):
    print(time.strftime("%H:%M:%S"), msg, flush=True)


def merge(adapter, merged, base=BASE):
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    say(f"loading the base model in 16-bit on the CPU ({base.name})")
    model = AutoModelForCausalLM.from_pretrained(base, dtype=torch.bfloat16, device_map="cpu", low_cpu_mem_usage=True)
    say(f"folding in the adapter {adapter}")
    model = PeftModel.from_pretrained(model, adapter)
    model = model.merge_and_unload()
    say(f"saving the merged model to {merged}")
    merged.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(merged, safe_serialization=True, max_shard_size="4GB")
    AutoTokenizer.from_pretrained(base).save_pretrained(merged)
    for extra in ("preprocessor_config.json", "processor_config.json", "chat_template.jinja", "chat_template.json",
                  "generation_config.json"):
        if (base / extra).exists() and not (merged / extra).exists():
            shutil.copy2(base / extra, merged / extra)
    del model


def convert(merged, gguf16):
    if not CONVERTER.exists():
        sys.exit(f"The GGUF converter is missing: {CONVERTER}")
    say("converting to GGUF (16-bit)")
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    subprocess.run([sys.executable, str(CONVERTER), str(merged), "--outfile", str(gguf16), "--outtype", "f16"],
                   check=True, env=env, cwd=str(CONVERTER.parent))


def quantize(gguf16, out, kind):
    exe = next((q for q in QUANTIZERS if q.exists()), None)
    if exe is None:
        sys.exit("llama-quantize.exe not found in Local Storage/LLM Models/llama.cpp")
    say(f"quantizing to {kind} with {exe.parent.name}\\{exe.name}")
    subprocess.run([str(exe), str(gguf16), str(out), kind], check=True, cwd=str(exe.parent))


def make_lora(adapter, base_dir, out_dir, name, base_model):
    """The adapter as a GGUF add-on beside a reference to the base's quantized file (the Timeline's models folder)."""
    converter = CONVERTER.parent / "convert_lora_to_gguf.py"
    base_gguf = next((f for f in sorted((TIMELINE_MODELS / base_model).glob("*.gguf"))
                      if not f.name.lower().startswith("mmproj")), None)
    if base_gguf is None:
        sys.exit(f"No GGUF for {base_model} in {TIMELINE_MODELS}")
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{name}-lora-f16.gguf"
    say(f"converting the adapter to a GGUF add-on for {base_gguf.name}")
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    subprocess.run([sys.executable, str(converter), str(adapter), "--base", str(base_dir), "--outfile", str(out),
                    "--outtype", "f16"], check=True, env=env, cwd=str(converter.parent))
    base_info = {}
    try:
        base_info = json.loads((TIMELINE_MODELS / base_model / "info.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    return out, base_gguf, base_info


def write_info(folder, name, adapter, kind, steps, extra=None):
    info = {"title": f"Kithylin ({name})",
            "source": f"Gemma 3 4B fine-tuned on your own chat logs with ClaudeApps/selfmodel ({adapter.name}"
                      + (f", step {steps}" if steps else "") + ")",
            "licence": "Gemma Terms of Use (https://ai.google.dev/gemma/terms); the fine-tune is personal - it was made "
                       "from your private conversations, so keep it to yourself",
            "notes": f"A model of you. {kind}, text only. Made {time.strftime('%Y-%m-%d')}.",
            "suggested": ["conversation"], "kithylin": True}
    info.update(extra or {})
    (folder / "info.json").write_text(json.dumps(info, indent=2, ensure_ascii=False), encoding="utf-8")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--adapter", type=Path, default=ADAPTER, help="the LoRA adapter folder (default: the finished one)")
    ap.add_argument("--name", default="kithylin-v1", help="the model's folder name")
    ap.add_argument("--quant", default="Q4_K_M")
    ap.add_argument("--keep", action="store_true", help="keep the merged model and 16-bit GGUF in work/")
    ap.add_argument("--install-timeline", action="store_true", help="also copy it into Local Storage/LLM Models/models")
    ap.add_argument("--skip-merge", action="store_true", help="reuse work/<name>/merged from an earlier run")
    ap.add_argument("--data", type=Path, default=ROOT / "data", help="the training data it was trained on (for the card)")
    ap.add_argument("--notes", default="", help="a line for the details card, e.g. what this model is for")
    ap.add_argument("--run", default="", help="the training run (runs/<name>/): its adapter and log")
    ap.add_argument("--base", default="base", help="the base model's folder in selfmodel/ it was trained on")
    ap.add_argument("--lora-on", default="", help="make an add-on for this Timeline model instead of merging")
    ap.add_argument("--base-title", default="", help="the base model's name for the details card")
    ap.add_argument("--title", default="", help="the model's name in the model lists (default: Kithylin (<name>))")
    ap.add_argument("--companion", default="",
                    help="a Soul and Song Companion's own version: its folder's name (its Retraining tab finds it so)")
    ap.add_argument("--delete-base-weights", action="store_true",
                    help="with --lora-on: delete the base's .safetensors once the add-on is made (frees ~24 GB for a 12B)")
    args = ap.parse_args(argv)
    run_dir = ROOT / "runs" / args.run if args.run else ROOT
    if args.run and args.adapter == ADAPTER:
        args.adapter = run_dir / "adapter"
    if args.run and args.data == ROOT / "data":
        try:
            started = [json.loads(l) for l in open(run_dir / "train_log.jsonl", encoding="utf-8")
                       if '"start"' in l]
            args.data = ROOT / started[-1].get("data", "data")
        except (OSError, ValueError, IndexError):
            pass

    adapter = args.adapter.resolve()
    if not (adapter / "adapter_config.json").exists():
        sys.exit(f"No adapter at {adapter} (adapter_config.json missing). Has training finished?")
    steps = None
    try:
        steps = json.loads((adapter / "state.json").read_text()).get("step")
    except (OSError, ValueError):
        pass
    if args.lora_on:
        out_dir = KITHYLIN_MODELS / args.name
        started = time.time()
        out, base_gguf, base_info = make_lora(adapter, ROOT / args.base, out_dir, args.name, args.lora_on)
        base_title = base_info.get("title", args.lora_on)
        extra = {"lora_base": args.lora_on, "lora_base_file": base_gguf.name,
                 "chat_template": base_info.get("chat_template", ""), "stop": base_info.get("stop", []),
                 "source": f"{base_title} fine-tuned on your own chat logs with ClaudeApps/selfmodel ({adapter.name}"
                           + (f", step {steps}" if steps else "") + "): a LoRA add-on, applied to the base at load time",
                 "licence": (base_info.get("licence") or "the base model's") + "; the fine-tune is personal - it was "
                            "made from your private conversations, so keep it to yourself",
                 "notes": f"A model of you: a LoRA add-on applied to {base_title} at load "
                          f"time. Made {time.strftime('%Y-%m-%d')}."}
        if args.companion:                         # (a Companion's own life, from Soul and Song's Retraining tab)
            extra.update(companion=args.companion, kithylin=False,
                         source=f"{base_title} fine-tuned on a Soul and Song Companion's own life ({adapter.name}"
                                + (f", step {steps}" if steps else "") + "): a LoRA add-on, applied to the base at "
                                "load time",
                         licence=(base_info.get("licence") or "the base model's") + "; the fine-tune is personal - "
                                 "it was made from a Companion's conversations with you",
                         notes=(args.notes + " " if args.notes else "") + f"Made {time.strftime('%Y-%m-%d')}.")
        if args.title:
            extra["title"] = args.title
        write_info(out_dir, args.name, adapter, "LoRA add-on (f16)", steps, extra)
        say(f"made {out} ({out.stat().st_size / 2**20:.0f} MB), on top of {base_gguf}")
        try:
            from . import card
            card.build(out_dir, args.data, adapter, log=run_dir / "train_log.jsonl", notes=args.notes,
                       base=args.base_title or base_info.get("title", args.lora_on), settings={"lora_on": args.lora_on})
            say("wrote the model details card (card.json)")
        except Exception as e:
            say(f"couldn't write the details card: {e}")
        if args.delete_base_weights:
            weights = sorted((ROOT / args.base).glob("*.safetensors"))
            freed = sum(w.stat().st_size for w in weights)
            for w in weights:
                w.unlink()
            say(f"deleted the base's full weights ({freed / 2**30:.1f} GB; its config and tokenizer files are kept, "
                f"and selfmodel.fetch gets the weights back for another round)")
        say(f"done in {(time.time() - started) / 60:.1f} minutes")
        return

    work = WORK / args.name
    merged, gguf16 = work / "merged", work / f"{args.name}-f16.gguf"
    out_dir = KITHYLIN_MODELS / args.name
    out = out_dir / f"{args.name}-{args.quant}.gguf"
    started = time.time()

    if not (args.skip_merge and (merged / "config.json").exists()):
        if merged.exists():
            shutil.rmtree(merged)
        merge(adapter, merged, ROOT / args.base)
    convert(merged, gguf16)
    out_dir.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()
    quantize(gguf16, out, args.quant)
    write_info(out_dir, args.name, adapter, args.quant, steps)
    say(f"made {out} ({out.stat().st_size / 2**30:.2f} GB)")
    try:
        from . import card
        card.build(out_dir, args.data, adapter, log=run_dir / "train_log.jsonl", notes=args.notes,
                   settings={"quant": args.quant}, **({"base": args.base_title} if args.base_title else {}))
        say("wrote the model details card (card.json)")
    except Exception as e:                                # the model is fine without one
        say(f"couldn't write the details card: {e}")

    if args.install_timeline:
        dest = TIMELINE_MODELS / args.name
        dest.mkdir(parents=True, exist_ok=True)
        shutil.copy2(out, dest / out.name)
        shutil.copy2(out_dir / "info.json", dest / "info.json")
        say(f"installed for the Timeline at {dest}")
    if not args.keep:
        shutil.rmtree(work, ignore_errors=True)
        say("cleaned up the working files")
    say(f"done in {(time.time() - started) / 60:.1f} minutes")


if __name__ == "__main__":
    main()
