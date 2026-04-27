import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

THUMBNAIL_MAX_SIZE = (480, 480)
BANNER_HEIGHT = 38
BANNER_COLOR = (0, 0, 0, 170)
TEXT_COLOR = (255, 255, 255)
FONT_SIZE = 22


def _load_font(size: int) -> ImageFont.ImageFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for path in candidates:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default(size=size)


def generate_labeled_thumbnail(source_path: str, label: str) -> str:
    """Generate a thumbnail with a semi-transparent date banner at the bottom.

    Returns the path to a temporary JPEG file. The caller is responsible for
    deleting it after use.
    """
    image = Image.open(source_path).convert("RGBA")
    image.thumbnail(THUMBNAIL_MAX_SIZE, Image.LANCZOS)
    width, height = image.size

    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rectangle([(0, height - BANNER_HEIGHT), (width, height)], fill=BANNER_COLOR)

    font = _load_font(FONT_SIZE)
    bbox = draw.textbbox((0, 0), label, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_x = (width - text_width) // 2
    text_y = height - BANNER_HEIGHT + (BANNER_HEIGHT - text_height) // 2
    draw.text((text_x, text_y), label, fill=TEXT_COLOR, font=font)

    composite = Image.alpha_composite(image, overlay).convert("RGB")

    tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
    composite.save(tmp.name, format="JPEG", quality=85)
    return tmp.name
