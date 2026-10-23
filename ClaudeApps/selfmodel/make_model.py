"""After training: turn the adapter into a model file the Timeline can run.

    env\\Scripts\\python.exe -m selfmodel.make_model                      the finished adapter -> Kithylin AI's Models folder
    env\\Scripts\\python.exe -m selfmodel.make_model --adapter PATH --name kithylin-step60
    env\\Scripts\\python.exe -m selfmodel.make_model --install-timeline    also install it for the Timeline's own programs

Three steps, all on the CPU (the graphics card can stay busy training):
  1. merge     the base model (16-bit, on the CPU) with the LoRA adapter folded into its weights -> work/<name>/merged
  2. convert   llama.cpp's converter (Local Storage/LLM Models/llama.cpp/src-b11533) -> a 16-bit .gguf
  3. quantize  llama-quantize -> Q4_K_M (about 2.5 GB), the same size the Timeline's other models use
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


def merge(adapter, merged):
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    say(f"loading the base model in 16-bit on the CPU ({BASE.name})")
    model = AutoModelForCausalLM.from_pretrained(BASE, dtype=torch.bfloat16, device_map="cpu", low_cpu_mem_usage=True)
    say(f"folding in the adapter {adapter}")
    model = PeftModel.from_pretrained(model, adapter)
    model = model.merge_and_unload()
    say(f"saving the merged model to {merged}")
    merged.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(merged, safe_serialization=True, max_shard_size="4GB")
    AutoTokenizer.from_pretrained(BASE).save_pretrained(merged)
    for extra in ("preprocessor_config.json", "processor_config.json", "chat_template.jinja", "chat_template.json",
                  "generation_config.json"):
        if (BASE / extra).exists() and not (merged / extra).exists():
            shutil.copy2(BASE / extra, merged / extra)
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


def write_info(folder, name, adapter, kind, steps):
    info = {"title": f"Kithylin ({name})",
            "source": f"Gemma 3 4B fine-tuned on your own chat logs with ClaudeApps/selfmodel ({adapter.name}"
                      + (f", step {steps}" if steps else "") + ")",
            "licence": "Gemma Terms of Use (https://ai.google.dev/gemma/terms); the fine-tune is personal - it was made "
                       "from your private conversations, so keep it to yourself",
            "notes": f"A model of you. {kind}, text only. Made {time.strftime('%Y-%m-%d')}.",
            "suggested": ["conversation"], "kithylin": True}
    (folder / "info.json").write_text(json.dumps(info, indent=2, ensure_ascii=False), encoding="utf-8")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--adapter", type=Path, default=ADAPTER, help="the LoRA adapter folder (default: the finished one)")
    ap.add_argument("--name", default="kithylin-v1", help="the model's folder name")
    ap.add_argument("--quant", default="Q4_K_M")
    ap.add_argument("--keep", action="store_true", help="keep the merged model and 16-bit GGUF in work/")
    ap.add_argument("--install-timeline", action="store_true", help="also copy it into Local Storage/LLM Models/models")
    ap.add_argument("--skip-merge", action="store_true", help="reuse work/<name>/merged from an earlier run")
    args = ap.parse_args(argv)

    adapter = args.adapter.resolve()
    if not (adapter / "adapter_config.json").exists():
        sys.exit(f"No adapter at {adapter} (adapter_config.json missing). Has training finished?")
    steps = None
    try:
        steps = json.loads((adapter / "state.json").read_text()).get("step")
    except (OSError, ValueError):
        pass
    work = WORK / args.name
    merged, gguf16 = work / "merged", work / f"{args.name}-f16.gguf"
    out_dir = KITHYLIN_MODELS / args.name
    out = out_dir / f"{args.name}-{args.quant}.gguf"
    started = time.time()

    if not (args.skip_merge and (merged / "config.json").exists()):
        if merged.exists():
            shutil.rmtree(merged)
        merge(adapter, merged)
    convert(merged, gguf16)
    out_dir.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()
    quantize(gguf16, out, args.quant)
    write_info(out_dir, args.name, adapter, args.quant, steps)
    say(f"made {out} ({out.stat().st_size / 2**30:.2f} GB)")

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
