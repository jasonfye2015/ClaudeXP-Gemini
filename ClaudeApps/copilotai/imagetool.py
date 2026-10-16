"""CopilotAI's image tool: how a local language model asks for a picture, and how the request is read back.

Local models don't reliably support structured tool calls, so the tool is a tag the model writes in its reply:

    Here's a little fox for you!
    <image shape="wide">a red fox in a snowy forest at dawn, soft golden light, detailed fur, photograph</image>

CopilotAI strips the tag from the visible reply and hands the description to the local Stable Diffusion engine
(the one Copilot Image Creator installs). The Image button and "/image ..." skip the model's decision: the model is
only asked to write a good Stable Diffusion prompt from the request."""
import re

ADDENDUM = (
    "\n\nYou can create pictures. When the user asks you to draw, paint, make, generate or show a picture, image, "
    "photo or illustration (and only then), reply with one short friendly sentence and then put the picture on a line "
    "of its own like this:\n"
    "<image>subject, setting, lighting, style, mood</image>\n"
    "Write the description in English as a comma-separated list of concrete visual details, 30 to 60 words, with the "
    "main subject first. For a wide picture write <image shape=\"wide\">, for a tall one <image shape=\"tall\">. "
    "Never explain the tag. Lines that look like [image created: ...] are records of pictures you already made; "
    "never write those yourself, but use them if the user asks for a change.")

WRITER_SYSTEM = (
    "You write prompts for a Stable Diffusion image generator. Turn the user's request into one prompt: a "
    "comma-separated list of concrete visual details, main subject first, then setting, lighting, style and quality "
    "words, 30 to 60 words. Keep every detail the user asked for. Reply with only the prompt, in English, on one "
    "line, with no quotation marks and no explanation.")

NEGATIVE = "blurry, low quality, deformed, disfigured, extra limbs, bad anatomy, text, watermark, signature"

SIZES = {
    "sd15": {"square": (512, 512), "wide": (768, 512), "tall": (512, 768)},
    "sdxl": {"square": (1024, 1024), "wide": (1216, 832), "tall": (832, 1216)},
}

_TAG = re.compile(r"<image(?:\s+shape\s*=\s*[\"']?(\w+)[\"']?)?\s*>(.*?)(?:</image\s*>|\Z)", re.I | re.S)
_PARTIAL = re.compile(r"<image[^>]*\Z|<i(?:m(?:a(?:g(?:e)?)?)?)?\Z", re.I)


def extract(text):
    """(reply without the tag, the picture description or None, 'square' | 'wide' | 'tall')."""
    found = _TAG.search(text or "")
    if not found:
        return (text or "").strip(), None, "square"
    shape = (found.group(1) or "square").lower()
    if shape not in ("square", "wide", "tall"):
        shape = {"landscape": "wide", "portrait": "tall"}.get(shape, "square")
    prompt = clean_prompt(found.group(2))
    return _TAG.sub("", text).strip(), prompt or None, shape


def visible(text):
    """The reply as it should look while streaming: complete tags, and a half-typed one, are hidden."""
    return _PARTIAL.sub("", _TAG.sub("", text or "")).rstrip() if "<" in (text or "") else text or ""


def clean_prompt(text):
    """A model's raw prompt -> one tidy line."""
    text = re.sub(r"^```\w*|```$", "", (text or "").strip())
    text = re.sub(r"^\s*(?:image\s+)?prompt\s*:\s*", "", " ".join(text.split()), flags=re.I)
    return text.strip(" \"'`")[:600]


def guess_shape(request):
    """Wide / tall from the user's own words, for the forced image path."""
    words = (request or "").lower()
    if re.search(r"\b(wide|landscape|panorama|panoramic|widescreen|banner)\b", words):
        return "wide"
    if re.search(r"\b(tall|portrait|full[- ]body|vertical|phone wallpaper)\b", words):
        return "tall"
    return "square"


def history_note(images):
    """What the model is told about pictures it already made, so 'make it bluer' works."""
    return "\n".join(f"[image created: {item.get('prompt', '')}]" for item in images or [])
