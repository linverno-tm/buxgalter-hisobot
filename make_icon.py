# -*- coding: utf-8 -*-
"""
Ilova belgisini (.ico) yasaydi.

Uch variant. Har biri 16x16 dan 256x256 gacha chizilади - kichik o'lchamda
ham tanib olinadigan bo'lishi uchun shakllar SODDA va kontrast YUQORI.

    python make_icon.py            -> uchala variant + taqqoslash rasmi
    python make_icon.py A          -> faqat A ni icon.ico ga yozadi
"""

import os
import sys

from PIL import Image, ImageDraw, ImageFont

SIZES = [16, 24, 32, 48, 64, 128, 256]
HERE = os.path.dirname(os.path.abspath(__file__))
S = 512          # chizish o'lchami (keyin kichraytiriladi)


def rounded(draw, box, r, fill):
    draw.rounded_rectangle(box, radius=r, fill=fill)


def _font(px, bold=True):
    for name in ("segoeuib.ttf" if bold else "segoeui.ttf",
                 "arialbd.ttf" if bold else "arial.ttf"):
        try:
            return ImageFont.truetype(name, px)
        except OSError:
            continue
    return ImageFont.load_default()


# ---------------------------------------------------------------------------
# A: ko'k kvadrat + o'suvchi ustunlar  (hisobot / o'sish)
# ---------------------------------------------------------------------------
def variant_a():
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    rounded(d, (0, 0, S, S), int(S * 0.22), (26, 63, 140, 255))
    # yuqori qismda ozgina yorug'lik
    rounded(d, (0, 0, S, int(S * 0.5)), int(S * 0.22), (33, 79, 173, 255))
    rounded(d, (0, int(S * 0.28), S, S), int(S * 0.22), (26, 63, 140, 255))

    # uchta o'suvchi ustun
    bars = [(0.20, 0.44), (0.42, 0.60), (0.64, 0.78)]
    w = S * 0.16
    for x, h in bars:
        x0 = S * x
        y1 = S * 0.80
        y0 = y1 - S * h
        d.rounded_rectangle((x0, y0, x0 + w, y1), radius=int(w * 0.22),
                            fill=(255, 255, 255, 255))
    # o'ng yuqorida yashil nuqta - o'sish urg'usi
    r = S * 0.085
    cx, cy = S * 0.795, S * 0.205
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(47, 196, 122, 255))
    return img


# ---------------------------------------------------------------------------
# B: sariq kvadrat + katta "Ҳ"  (juda ajralib turadi)
# ---------------------------------------------------------------------------
def variant_b():
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    rounded(d, (0, 0, S, S), int(S * 0.22), (214, 138, 16, 255))
    rounded(d, (0, 0, S, int(S * 0.5)), int(S * 0.22), (232, 154, 26, 255))
    rounded(d, (0, int(S * 0.28), S, S), int(S * 0.22), (214, 138, 16, 255))

    f = _font(int(S * 0.62))
    t = "Ҳ"
    bb = d.textbbox((0, 0), t, font=f)
    d.text(((S - (bb[2] - bb[0])) / 2 - bb[0],
            (S - (bb[3] - bb[1])) / 2 - bb[1] - S * 0.02),
           t, font=f, fill=(255, 255, 255, 255))
    return img


# ---------------------------------------------------------------------------
# C: to'q yashil kvadrat + hujjat va belgi  (tekshirilgan hisobot)
# ---------------------------------------------------------------------------
def variant_c():
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    rounded(d, (0, 0, S, S), int(S * 0.22), (17, 94, 89, 255))
    rounded(d, (0, 0, S, int(S * 0.5)), int(S * 0.22), (21, 110, 104, 255))
    rounded(d, (0, int(S * 0.28), S, S), int(S * 0.22), (17, 94, 89, 255))

    # hujjat
    x0, y0, x1, y1 = S * 0.24, S * 0.17, S * 0.70, S * 0.83
    fold = S * 0.16
    d.polygon([(x0, y0), (x1 - fold, y0), (x1, y0 + fold), (x1, y1), (x0, y1)],
              fill=(255, 255, 255, 255))
    d.polygon([(x1 - fold, y0), (x1, y0 + fold), (x1 - fold, y0 + fold)],
              fill=(206, 224, 222, 255))
    # satrlar
    for i, wf in enumerate((0.62, 0.78, 0.45)):
        yy = y0 + S * (0.20 + i * 0.135)
        d.rounded_rectangle((x0 + S * 0.07, yy,
                             x0 + S * 0.07 + (x1 - x0 - S * 0.14) * wf,
                             yy + S * 0.055),
                            radius=S * 0.027, fill=(17, 94, 89, 255))
    # yashil belgi
    r = S * 0.175
    cx, cy = S * 0.74, S * 0.74
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(47, 196, 122, 255))
    d.line([(cx - r * 0.46, cy + r * 0.02),
            (cx - r * 0.10, cy + r * 0.40),
            (cx + r * 0.50, cy - r * 0.42)],
           fill=(255, 255, 255, 255), width=int(S * 0.055), joint="curve")
    return img


VARIANTS = {"A": variant_a, "B": variant_b, "C": variant_c}
LABELS = {"A": "A - ko'k, o'suvchi ustunlar",
          "B": "B - sariq, Ҳ harfi",
          "C": "C - yashil, tekshirilgan hujjat"}


def save_ico(img, path):
    img.save(path, format="ICO",
             sizes=[(s, s) for s in SIZES])


def preview():
    """Uchala variantni turli o'lchamda yonma-yon ko'rsatadigan rasm."""
    show = [256, 64, 48, 32, 16]
    pad, gap, lblw = 26, 22, 300
    rowh = max(show) + gap
    W = lblw + sum(s + gap for s in show) + pad
    H = pad * 2 + rowh * len(VARIANTS)
    sheet = Image.new("RGBA", (W, H), (244, 246, 249, 255))
    d = ImageDraw.Draw(sheet)
    f = _font(20, bold=True)
    fs = _font(15, bold=False)

    y = pad
    for key in ("A", "B", "C"):
        img = VARIANTS[key]()
        d.text((pad, y + max(show) // 2 - 12), LABELS[key], font=f,
               fill=(28, 36, 52, 255))
        x = lblw
        for s in show:
            sheet.paste(img.resize((s, s), Image.LANCZOS),
                        (x, y + (max(show) - s) // 2),
                        img.resize((s, s), Image.LANCZOS))
            d.text((x, y + (max(show) + s) // 2 + 6), "%dpx" % s, font=fs,
                   fill=(110, 120, 136, 255))
            x += s + gap
        y += rowh
    p = os.path.join(HERE, "icon_variants.png")
    sheet.convert("RGB").save(p, quality=95)
    return p


def main():
    if len(sys.argv) > 1:
        key = sys.argv[1].strip().upper()
        if key not in VARIANTS:
            raise SystemExit("Variant A, B yoki C bo'lishi kerak")
        p = os.path.join(HERE, "icon.ico")
        save_ico(VARIANTS[key](), p)
        print("Tanlandi: %s" % LABELS[key])
        print("Yozildi : %s  (%d bayt)" % (p, os.path.getsize(p)))
        return

    for key in VARIANTS:
        p = os.path.join(HERE, "icon_%s.ico" % key)
        save_ico(VARIANTS[key](), p)
        print("  %s -> %s" % (LABELS[key], os.path.basename(p)))
    print("\nTaqqoslash rasmi: %s" % preview())
    print("\nBirini tanlash:  python make_icon.py A")


if __name__ == "__main__":
    main()
