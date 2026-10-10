"""Command-line worker used by the Image Creator's isolated local runtime."""
import argparse
import sys
from pathlib import Path

if sys.path and Path(sys.path[0]).resolve() == Path(__file__).resolve().parent:
    sys.path.pop(0)

MODELS = {
    "sd15": "stable-diffusion-v1-5/stable-diffusion-v1-5",
    "sdxl": "stabilityai/stable-diffusion-xl-base-1.0",
}


def install(model_id, root):
    from huggingface_hub import HfApi, snapshot_download

    repo = MODELS[model_id]
    files = HfApi().model_info(repo).siblings
    names = {item.rfilename for item in files}
    patterns = ["*.json", "*.txt", "*.model"]
    directories = {str(Path(name).parent).replace(".", "") for name in names if name.endswith("/config.json")}
    for directory in sorted(directories):
        weights = sorted(name for name in names if str(Path(name).parent).replace(".", "") == directory
                         and name.endswith(".safetensors"))
        half = [name for name in weights if ".fp16." in name]
        if half:
            patterns.extend(half)
        else:
            canonical = [name for name in weights if Path(name).name in (
                "model.safetensors", "diffusion_pytorch_model.safetensors", "pytorch_model.safetensors")]
            patterns.extend(canonical[:1])

    target = Path(root) / model_id
    target.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {repo} to {target}", flush=True)
    snapshot_download(repo_id=repo, local_dir=str(target), allow_patterns=patterns)
    print(f"MODEL_READY:{model_id}", flush=True)


def generate(args):
    import torch
    from diffusers import DiffusionPipeline

    if not torch.cuda.is_available():
        print("CUDA is unavailable; generation will use the CPU and may be very slow.", flush=True)
        device = "cpu"
        dtype = torch.float32
    else:
        capability = torch.cuda.get_device_capability()
        architecture = f"sm_{capability[0]}{capability[1]}"
        if architecture not in torch.cuda.get_arch_list():
            raise RuntimeError(
                f"The installed PyTorch build has no {architecture} kernels for "
                f"{torch.cuda.get_device_name()}. Run Set Up Image Engine again to repair it.")
        device = "cuda"
        dtype = torch.float16

    model_path = Path(args.model_path)
    if not (model_path / "model_index.json").is_file():
        raise FileNotFoundError(f"The selected model is not installed: {model_path}")
    print(f"Loading {args.model} on {device}...", flush=True)
    pipe = DiffusionPipeline.from_pretrained(
        str(model_path),
        torch_dtype=dtype,
        variant="fp16" if device == "cuda" else None,
        use_safetensors=True,
        local_files_only=True,
        safety_checker=None,
    )
    pipe.to(device)
    if device == "cuda":
        pipe.enable_attention_slicing()
    pipe.set_progress_bar_config(disable=True)
    generator = torch.Generator(device=device).manual_seed(args.seed)

    def progress(_pipeline, step, _timestep, _kwargs):
        print(f"PROGRESS:{step + 1}:{args.steps}", flush=True)
        return _kwargs

    result = pipe(
        prompt=args.prompt,
        negative_prompt=args.negative_prompt or None,
        width=args.width,
        height=args.height,
        num_inference_steps=args.steps,
        guidance_scale=args.guidance,
        generator=generator,
        callback_on_step_end=progress,
    ).images[0]
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    result.save(destination)
    print(f"IMAGE_READY:{destination}", flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=("install", "generate"))
    parser.add_argument("--model", choices=tuple(MODELS), required=True)
    parser.add_argument("--models-root", default="")
    parser.add_argument("--model-path", default="")
    parser.add_argument("--prompt", default="")
    parser.add_argument("--negative-prompt", default="")
    parser.add_argument("--width", type=int, default=512)
    parser.add_argument("--height", type=int, default=512)
    parser.add_argument("--steps", type=int, default=25)
    parser.add_argument("--guidance", type=float, default=7.0)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--output", default="")
    args = parser.parse_args()
    try:
        if args.operation == "install":
            install(args.model, args.models_root)
        else:
            generate(args)
    except Exception as exc:
        print(f"ERROR:{type(exc).__name__}: {exc}", file=sys.stderr, flush=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
