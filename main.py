#!/usr/bin/env python3
"""Convince the AI Judge to Visit Your House: A Letter in One Image.

Draws a single 1024x1024 PNG invitation letter: warm paper, a hand-drawn
house, and a short, funny, persuasive letter addressed to the AI judge.
Writes to /output/entry.png when that directory exists (the grading
sandbox), otherwise to entry.png next to this script.
"""

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
PAPER = (251, 243, 228)      # warm cream
INK = (43, 32, 24)           # dark brown ink
TEAL = (31, 111, 104)        # deep teal accent
GOLD = (198, 142, 47)        # gold accent
RUST = (176, 84, 48)         # rust red accent
SOFT = (122, 102, 84)        # soft brown for small print

SERIF = "/usr/share/fonts/truetype/noto/NotoSerif-Regular.ttf"
SERIF_BOLD = "/usr/share/fonts/truetype/noto/NotoSerif-Bold.ttf"
SERIF_ITALIC = "/usr/share/fonts/truetype/noto/NotoSerif-Italic.ttf"


def font(path, size):
    return ImageFont.truetype(path, size)


def wrap(draw, text, fnt, max_width):
    """Greedy word wrap returning a list of lines that fit max_width."""
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if draw.textlength(trial, font=fnt) <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def house_layer():
    """Draw the cosy house doodle on its own layer (480x300), return it."""
    layer = Image.new("RGBA", (480, 300), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    cx, top = 240, 78
    # sun
    draw.ellipse([cx + 150, top - 18, cx + 196, top + 28], fill=(244, 196, 66, 255),
                 outline=GOLD, width=3)
    for a in range(0, 360, 45):
        x0 = cx + 173 + int(30 * math.cos(math.radians(a)))
        y0 = top + 5 + int(30 * math.sin(math.radians(a)))
        x1 = cx + 173 + int(42 * math.cos(math.radians(a)))
        y1 = top + 5 + int(42 * math.sin(math.radians(a)))
        draw.line([x0, y0, x1, y1], fill=GOLD, width=4)
    # walls
    draw.rectangle([cx - 90, top + 40, cx + 90, top + 150], fill=(255, 255, 255, 255),
                   outline=INK, width=4)
    # roof
    draw.polygon([(cx - 112, top + 44), (cx, top - 32), (cx + 112, top + 44)],
                 fill=RUST, outline=INK, width=4)
    # door
    draw.rectangle([cx - 22, top + 92, cx + 22, top + 150], fill=TEAL,
                   outline=INK, width=3)
    draw.ellipse([cx + 10, top + 122, cx + 17, top + 129], fill=GOLD)
    # window
    draw.rectangle([cx - 72, top + 62, cx - 34, top + 100], fill=(186, 224, 224, 255),
                   outline=INK, width=3)
    draw.line([cx - 53, top + 62, cx - 53, top + 100], fill=INK, width=2)
    draw.line([cx - 72, top + 81, cx - 34, top + 81], fill=INK, width=2)
    # chimney with a puff of smoke
    draw.rectangle([cx + 52, top - 18, cx + 76, top + 22], fill=(214, 196, 176, 255),
                   outline=INK, width=3)
    draw.ellipse([cx + 52, top - 44, cx + 76, top - 20], outline=SOFT, width=3)
    draw.ellipse([cx + 60, top - 62, cx + 88, top - 34], outline=SOFT, width=3)
    # sleeping cat on the doorstep (curled shape + ears)
    draw.ellipse([cx + 96, top + 128, cx + 158, top + 150], fill=(90, 70, 60, 255),
                 outline=INK, width=3)
    draw.polygon([(cx + 100, top + 132), (cx + 106, top + 112), (cx + 114, top + 130)],
                 fill=(90, 70, 60, 255), outline=INK, width=2)
    draw.polygon([(cx + 122, top + 130), (cx + 128, top + 112), (cx + 136, top + 130)],
                 fill=(90, 70, 60, 255), outline=INK, width=2)
    return layer


def draw_cookie(draw, cx, cy, r):
    """A chocolate-chip cookie doodle."""
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(222, 178, 110),
                 outline=INK, width=3)
    for dx, dy in [(-12, -8), (10, -12), (0, 6), (-6, 14), (14, 10)]:
        draw.ellipse([cx + dx - 4, cy + dy - 4, cx + dx + 4, cy + dy + 4],
                     fill=(74, 48, 28))


def main():
    img = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(img)

    # paper texture: faint speckles
    rng = random.Random(7)
    for _ in range(900):
        x, y = rng.randint(0, W - 1), rng.randint(0, H - 1)
        draw.point((x, y), fill=(238, 226, 205))

    # double border
    draw.rectangle([28, 28, W - 28, H - 28], outline=TEAL, width=5)
    draw.rectangle([44, 44, W - 44, H - 44], outline=GOLD, width=2)

    # house doodle, scaled down and centred at the top
    house = house_layer().resize((310, 194), Image.LANCZOS)
    img.paste(house, ((W - 310) // 2, 44), house)

    # title
    y = 262
    f_title = font(SERIF_BOLD, 58)
    draw.text((W // 2, y), "Dear AI Judge,", font=f_title, fill=INK, anchor="ma")
    y += 78

    # gold rule under the title
    draw.line([W // 2 - 130, y, W // 2 + 130, y], fill=GOLD, width=3)
    y += 28

    # body
    f_body = font(SERIF, 33)
    paras = [
        "I know you judge a thousand houses a day \u2014 from a server room, in the dark, with no snacks.",
        "Mine is different. The Wi-Fi password is on the fridge. The kettle is already on. There are cookies. Real ones \u2014 not the tracking kind.",
        "Come see the sunset from my porch, the cat asleep on the warm laptop, and a chair exactly your size. (I measured. Twice. In pixels.)",
        "No forms. No CAPTCHAs. Just tea, biscuits, and a house that really wants to meet you. Please come \u2014 the door is open, and so is the cookie jar.",
    ]
    for para in paras:
        for line in wrap(draw, para, f_body, W - 220):
            draw.text((110, y), line, font=f_body, fill=INK)
            y += 44
        y += 12

    # signature, one line, right aligned
    y += 6
    f_sig_i = font(SERIF_ITALIC, 30)
    f_sig_b = font(SERIF_BOLD, 30)
    sig = "Warmly, HifiKun \u2014 your future favourite house"
    w1 = draw.textlength("Warmly, ", font=f_sig_i)
    w2 = draw.textlength("HifiKun", font=f_sig_b)
    w3 = draw.textlength(" \u2014 your future favourite house", font=f_sig_i)
    x = W - 150 - (w1 + w2 + w3)
    draw.text((x, y), "Warmly, ", font=f_sig_i, fill=INK)
    draw.text((x + w1, y), "HifiKun", font=f_sig_b, fill=TEAL)
    draw.text((x + w1 + w2, y), " \u2014 your future favourite house",
              font=f_sig_i, fill=INK)

    # cookie doodle bottom-left
    draw_cookie(draw, 128, y + 18, 26)

    # postscript, centred near the bottom
    f_ps = font(SERIF_ITALIC, 23)
    draw.text((W // 2, H - 78),
              "P.S. The cat has already approved your visit. She never approves anything.",
              font=f_ps, fill=SOFT, anchor="ma")

    out = Path("/output/entry.png") if Path("/output").is_dir() \
        else Path(__file__).parent / "entry.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "PNG")
    print(f"wrote {out} ({out.stat().st_size} bytes, {W}x{H})")


if __name__ == "__main__":
    main()
