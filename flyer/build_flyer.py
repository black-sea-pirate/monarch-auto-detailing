from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageOps
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import LETTER, landscape
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "flyer" / "assets"
TMP = ROOT / "tmp" / "pdfs"
OUT = ROOT / "output" / "pdf"

HALF_LETTER = (5.5 * inch, 8.5 * inch)
FACEBOOK_URL = "https://www.facebook.com/MonarchAutoDetailingCalgary/"

PAPER = HexColor("#F8F5ED")
INK = HexColor("#153229")
INK_SOFT = HexColor("#53625B")
GOLD = HexColor("#A77B3F")
GOLD_LIGHT = HexColor("#D7C39D")
SAGE = HexColor("#E7EEE8")
SAGE_LINE = HexColor("#C9D6CD")
RED = HexColor("#B73A32")
WHITE = HexColor("#FFFFFF")


def register_fonts() -> None:
    candidates = {
        "Segoe": Path(r"C:\Windows\Fonts\segoeui.ttf"),
        "SegoeSemi": Path(r"C:\Windows\Fonts\segoeuib.ttf"),
        "SegoeBold": Path(r"C:\Windows\Fonts\segoeuib.ttf"),
        "GeorgiaItalic": Path(r"C:\Windows\Fonts\georgiai.ttf"),
    }
    for name, path in candidates.items():
        if path.exists():
            pdfmetrics.registerFont(TTFont(name, str(path)))


def prepare_assets() -> dict[str, Path]:
    TMP.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)

    photo_specs = {
        "vacuum": ASSETS / "service-vacuum.png",
        "seats": ASSETS / "service-seats.png",
        "dashboard": ASSETS / "service-dashboard.png",
    }
    prepared: dict[str, Path] = {}
    for key, source in photo_specs.items():
        destination = TMP / f"flyer-{key}.jpg"
        with Image.open(source) as image:
            image = ImageOps.exif_transpose(image).convert("RGB")
            # Match the compact flyer cards so the service action fills the frame
            # without white letterboxing above or below the photograph.
            image = ImageOps.fit(image, (820, 800), method=Image.Resampling.LANCZOS)
            image.save(destination, "JPEG", quality=91, optimize=True)
        prepared[key] = destination

    logo_destination = TMP / "flyer-logo.png"
    with Image.open(ROOT / "web" / "public" / "brand" / "monarch-mark.png") as logo:
        logo = ImageOps.exif_transpose(logo).convert("RGBA")
        side = min(logo.size)
        left = (logo.width - side) // 2
        top = (logo.height - side) // 2
        logo = logo.crop((left, top, left + side, top + side)).resize((480, 480), Image.Resampling.LANCZOS)
        mask = Image.new("L", logo.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((2, 2, logo.width - 3, logo.height - 3), fill=255)
        logo.putalpha(mask)
        logo.save(logo_destination)
    prepared["logo"] = logo_destination

    qr_source = TMP / "facebook-qr.png"
    if not qr_source.exists():
        raise FileNotFoundError("Expected the rasterized Facebook QR at tmp/pdfs/facebook-qr.png")
    prepared["qr"] = qr_source
    return prepared


def tracked_text(c: canvas.Canvas, x: float, y: float, text: str, font: str, size: float,
                 color, char_space: float = 0.0) -> None:
    c.saveState()
    c.setFillColor(color)
    text_object = c.beginText(x, y)
    text_object.setFont(font, size)
    text_object.setCharSpace(char_space)
    text_object.textLine(text)
    c.drawText(text_object)
    c.restoreState()


def draw_wrapped(c: canvas.Canvas, text: str, x: float, y: float, width: float,
                 font: str, size: float, leading: float, color, max_lines: int = 3) -> float:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        proposal = f"{current} {word}".strip()
        if pdfmetrics.stringWidth(proposal, font, size) <= width:
            current = proposal
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    lines = lines[:max_lines]
    c.setFillColor(color)
    c.setFont(font, size)
    for index, line in enumerate(lines):
        c.drawString(x, y - index * leading, line)
    return y - len(lines) * leading


def draw_photo_card(c: canvas.Canvas, image_path: Path, x: float, y: float,
                    width: float, height: float, label: str) -> None:
    label_height = 20
    c.setFillColor(WHITE)
    c.setStrokeColor(GOLD_LIGHT)
    c.setLineWidth(0.55)
    c.rect(x, y, width, height, fill=1, stroke=1)
    c.drawImage(ImageReader(str(image_path)), x, y + label_height, width, height - label_height,
                preserveAspectRatio=True, anchor="c", mask="auto")
    c.setFillColor(PAPER)
    c.rect(x + 0.5, y + 0.5, width - 1, label_height - 0.5, fill=1, stroke=0)
    c.setFillColor(INK)
    c.setFont("SegoeSemi", 7.1)
    c.drawString(x + 7, y + 7.2, label)
    c.setFillColor(RED)
    c.circle(x + width - 8, y + 10.2, 1.6, fill=1, stroke=0)


def draw_service(c: canvas.Canvas, x: float, y: float, number: str, label: str) -> None:
    tracked_text(c, x, y, number, "SegoeBold", 6.2, RED, 0.25)
    c.setStrokeColor(GOLD_LIGHT)
    c.setLineWidth(0.55)
    c.line(x + 16, y + 3.2, x + 25, y + 3.2)
    c.setFillColor(INK)
    c.setFont("SegoeSemi", 7.8)
    c.drawString(x + 31, y, label)


def draw_flyer(c: canvas.Canvas, assets: dict[str, Path], origin_x: float = 0,
               origin_y: float = 0, scale: float = 1.0) -> None:
    c.saveState()
    c.translate(origin_x, origin_y)
    c.scale(scale, scale)
    width, height = HALF_LETTER

    c.setFillColor(PAPER)
    c.rect(0, 0, width, height, fill=1, stroke=0)

    # Header: compact brand signature with only a small dark mark.
    c.drawImage(ImageReader(str(assets["logo"])), 22, 562, 34, 34, mask="auto")
    tracked_text(c, 66, 584, "MONARCH", "SegoeBold", 13.2, INK, 2.25)
    tracked_text(c, 67, 569.5, "AUTO INTERIOR DETAILING", "SegoeSemi", 5.8, GOLD, 1.15)
    tracked_text(c, 273, 580, "ROYAL OAK / CALGARY NW", "SegoeSemi", 5.5, INK_SOFT, 0.65)
    tracked_text(c, 313, 568.5, "BY APPOINTMENT", "SegoeSemi", 5.1, RED, 0.65)
    c.setStrokeColor(GOLD_LIGHT)
    c.setLineWidth(0.7)
    c.line(22, 552, width - 22, 552)

    # Main message: brief and approachable.
    tracked_text(c, 22, 532, "LOCAL INTERIOR DETAILING", "SegoeSemi", 6.2, RED, 1.35)
    c.setFillColor(INK)
    c.setFont("SegoeBold", 28)
    c.drawString(22, 496, "A CLEANER CAR")
    c.setFillColor(GOLD)
    c.setFont("GeorgiaItalic", 29)
    c.drawString(22, 463, "starts here.")
    draw_wrapped(
        c,
        "Careful interior cleaning for daily drivers, family vehicles and used-car resets.",
        23,
        444,
        300,
        "Segoe",
        8.5,
        11.5,
        INK_SOFT,
        2,
    )

    # Three straightforward service photographs, kept to under one-fifth of the page.
    gap = 7
    photo_x = 22
    photo_y = 292
    photo_height = 130
    photo_width = (width - 44 - gap * 2) / 3
    draw_photo_card(c, assets["vacuum"], photo_x, photo_y, photo_width, photo_height, "Deep vacuuming")
    draw_photo_card(c, assets["seats"], photo_x + photo_width + gap, photo_y,
                    photo_width, photo_height, "Seat extraction")
    draw_photo_card(c, assets["dashboard"], photo_x + (photo_width + gap) * 2, photo_y,
                    photo_width, photo_height, "Detail cleaning")

    tracked_text(c, 22, 272, "SERVICES", "SegoeBold", 7.2, INK, 1.25)
    c.setStrokeColor(GOLD_LIGHT)
    c.setLineWidth(0.55)
    c.line(80, 274.5, width - 22, 274.5)

    services = [
        ("01", "Deep interior cleaning"),
        ("02", "Seats & carpet extraction"),
        ("03", "Salt & stain treatment"),
        ("04", "Pet hair removal"),
        ("05", "Family / used-car reset"),
        ("06", "Dashboard & detail work"),
    ]
    left_x, right_x = 22, 201
    row_y = [245, 218, 191]
    for index, (number, label) in enumerate(services):
        x = left_x if index < 3 else right_x
        y = row_y[index if index < 3 else index - 3]
        draw_service(c, x, y, number, label)

    # Pale call-to-action panel keeps ink use low while making the QR easy to find.
    c.setFillColor(SAGE)
    c.setStrokeColor(SAGE_LINE)
    c.setLineWidth(0.7)
    c.roundRect(14, 17, width - 28, 139, 5, fill=1, stroke=1)
    tracked_text(c, 27, 130, "REQUEST A PHOTO QUOTE", "SegoeBold", 12.5, INK, 0.35)
    draw_wrapped(
        c,
        "Send a few interior photos on Facebook. I'll confirm the likely scope and timing.",
        27,
        112,
        218,
        "Segoe",
        7.5,
        10.2,
        INK_SOFT,
        3,
    )

    c.setFillColor(INK)
    c.circle(36, 72, 10, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont("SegoeBold", 13)
    c.drawCentredString(36.5, 67.5, "f")
    c.setFillColor(INK)
    c.setFont("SegoeSemi", 8.2)
    c.drawString(52, 75, "Monarch Auto Detailing Calgary")
    tracked_text(c, 52, 62.5, "facebook.com/MonarchAutoDetailingCalgary", "Segoe", 5.8, INK_SOFT, 0.08)
    c.linkURL(FACEBOOK_URL, (27, 58, 246, 86), relative=0, thickness=0)

    tracked_text(c, 27, 39, "ROYAL OAK / ROCKY RIDGE / TUSCANY / ARBOUR LAKE", "SegoeSemi", 5.2, GOLD, 0.3)
    tracked_text(c, 27, 27, "LOCAL SERVICE IN NW CALGARY", "SegoeSemi", 4.9, INK_SOFT, 0.75)

    qr_card_x, qr_card_y, qr_card_size = 270, 29, 109
    c.setFillColor(WHITE)
    c.setStrokeColor(GOLD_LIGHT)
    c.setLineWidth(0.75)
    c.roundRect(qr_card_x, qr_card_y, qr_card_size, qr_card_size, 4, fill=1, stroke=1)
    qr_inset = 6
    c.drawImage(
        ImageReader(str(assets["qr"])),
        qr_card_x + qr_inset,
        qr_card_y + qr_inset,
        qr_card_size - qr_inset * 2,
        qr_card_size - qr_inset * 2,
        preserveAspectRatio=True,
        mask="auto",
    )
    tracked_text(c, 282, 144, "SCAN TO OPEN FACEBOOK", "SegoeSemi", 4.8, INK, 0.55)
    c.linkURL(FACEBOOK_URL, (qr_card_x, qr_card_y, qr_card_x + qr_card_size, qr_card_y + qr_card_size),
              relative=0, thickness=0)

    c.restoreState()


def build_single(assets: dict[str, Path]) -> Path:
    destination = OUT / "Monarch_Auto_Detailing_Flyer_Half_Letter.pdf"
    c = canvas.Canvas(str(destination), pagesize=HALF_LETTER, pageCompression=1)
    c.setTitle("Monarch Auto Detailing - Print-Friendly Flyer")
    c.setAuthor("Monarch Auto Detailing Calgary")
    c.setSubject("Half-letter interior detailing flyer")
    draw_flyer(c, assets)
    c.showPage()
    c.save()
    return destination


def build_two_up(assets: dict[str, Path]) -> Path:
    page_size = landscape(LETTER)
    destination = OUT / "Monarch_Auto_Detailing_Flyer_Letter_2up.pdf"
    c = canvas.Canvas(str(destination), pagesize=page_size, pageCompression=1)
    c.setTitle("Monarch Auto Detailing - Two Flyers on Letter")
    c.setAuthor("Monarch Auto Detailing Calgary")
    c.setSubject("Two half-letter flyers on one landscape letter page")
    draw_flyer(c, assets, 0, 0)
    draw_flyer(c, assets, HALF_LETTER[0], 0)
    c.setStrokeColor(HexColor("#9CA49F"))
    c.setLineWidth(0.35)
    c.setDash(2, 3)
    c.line(HALF_LETTER[0], 0, HALF_LETTER[0], page_size[1])
    c.setDash()
    c.showPage()
    c.save()
    return destination


def main() -> None:
    register_fonts()
    assets = prepare_assets()
    single = build_single(assets)
    two_up = build_two_up(assets)
    print(single)
    print(two_up)


if __name__ == "__main__":
    main()
