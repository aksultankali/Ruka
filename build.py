"""Собирает сайт-визитку: index.html, contact.vcf и QR-код.

Поменять данные: отредактируйте CONTACT ниже и запустите
    pip install segno
    python3 build.py
"""

import html
import json
from pathlib import Path

import segno

CONTACT = {
    "first_name": "Aksultan",
    "last_name": "Kaliyev",
    "title": "",  # должность, например "Product designer"
    "company": "",
    "phone": "+7 702 803 03 00",
    "whatsapp": True,  # True — тот же номер в WhatsApp
    "email": "aksultankaliyev@gmail.com",
    "telegram": "yellowba1",  # ник без @
    "instagram": "aksultankali",  # ник без @
    "github": "aksultankali",
    # Адрес, по которому опубликована визитка. Его записывают на NFC-метку.
    "page_url": "https://aksultankali.github.io/Ruka/",
}

ROOT = Path(__file__).parent
TEMPLATE = ROOT / "templates" / "card.html"


def digits(phone):
    return "".join(ch for ch in phone if ch.isdigit())


def vcard(c, compact=False):
    """compact=True keeps the QR code sparse: name, phone, email and the card link only."""
    def esc(v):
        return v.replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;")

    full = f"{c['first_name']} {c['last_name']}".strip()
    lines = [
        "BEGIN:VCARD",
        "VERSION:3.0",
        f"N:{esc(c['last_name'])};{esc(c['first_name'])};;;",
        f"FN:{esc(full)}",
    ]
    if c["company"]:
        lines.append(f"ORG:{esc(c['company'])}")
    if c["title"]:
        lines.append(f"TITLE:{esc(c['title'])}")
    if c["phone"]:
        lines.append(f"TEL;TYPE=CELL:+{digits(c['phone'])}")
    if c["email"]:
        lines.append(f"EMAIL;TYPE=INTERNET:{c['email']}")
    links = []
    if not compact:
        if c["phone"] and c["whatsapp"]:
            links.append(("WhatsApp", f"https://wa.me/{digits(c['phone'])}"))
        if c["telegram"]:
            links.append(("Telegram", f"https://t.me/{c['telegram']}"))
        if c["instagram"]:
            links.append(("Instagram", f"https://instagram.com/{c['instagram']}"))
        if c["github"]:
            links.append(("GitHub", f"https://github.com/{c['github']}"))
    if c["page_url"]:
        links.append(("Card", c["page_url"]))
    # itemN.X-ABLabel gives each link a readable name in iPhone Contacts; other apps ignore it.
    for i, (label, url) in enumerate(links, 1):
        lines.append(f"item{i}.URL:{url}")
        lines.append(f"item{i}.X-ABLabel:{esc(label)}")
    lines.append("END:VCARD")
    return "\r\n".join(lines) + "\r\n"


def contact_rows(c):
    rows = []
    if c["phone"]:
        rows.append(("Телефон", c["phone"], f"tel:+{digits(c['phone'])}"))
        if c["whatsapp"]:
            rows.append(("WhatsApp", c["phone"], f"https://wa.me/{digits(c['phone'])}"))
    if c["telegram"]:
        rows.append(("Telegram", f"@{c['telegram']}", f"https://t.me/{c['telegram']}"))
    if c["instagram"]:
        rows.append(("Instagram", f"@{c['instagram']}", f"https://instagram.com/{c['instagram']}"))
    if c["email"]:
        rows.append(("Email", c["email"], f"mailto:{c['email']}"))
    if c["github"]:
        rows.append(("GitHub", f"github.com/{c['github']}", f"https://github.com/{c['github']}"))
    out = []
    for label, value, href in rows:
        v, h = html.escape(value), html.escape(href)
        # On narrow phones a long address breaks after the @, never mid-word.
        shown = v.replace("@", "@<wbr>", 1) if "@" in v[1:] else v
        out.append(
            "    <li>\n"
            f'      <div class="text"><span class="label">{html.escape(label)}</span>'
            f'<a class="value" href="{h}" target="_blank" rel="noopener">{shown}</a></div>\n'
            f'      <button class="copy" type="button" data-copy="{v}">Копировать</button>\n'
            "    </li>"
        )
    return "\n".join(out)


def qr_svg(data):
    qr = segno.make(data, error="m")
    svg = qr.svg_inline(scale=1, border=2, dark="#17213a", light=None)
    size = qr.symbol_size(scale=1, border=2)[0]
    return svg.replace(
        f'width="{size}" height="{size}"',
        f'viewBox="0 0 {size} {size}" role="img" aria-label="QR-код: контакт в формате vCard"',
        1,
    ).replace('class="segno"', 'shape-rendering="crispEdges"', 1).replace('stroke="#17213a"', 'stroke="currentColor"')


def main():
    c = CONTACT
    full = f"{c['first_name']} {c['last_name']}".strip()
    card = vcard(c)
    page = (
        TEMPLATE.read_text(encoding="utf-8")
        .replace("{{FULL_NAME}}", html.escape(full))
        .replace("{{INITIALS}}", (c["first_name"][:1] + c["last_name"][:1]).upper())
        .replace("{{NAME_LINES}}", "<br>".join(html.escape(p) for p in full.split()))
        .replace("{{CONTACT_ROWS}}", contact_rows(c))
        .replace("{{QR_SVG}}", qr_svg(vcard(c, compact=True)))
        .replace("{{PAGE_URL_JSON}}", json.dumps(c["page_url"]))
    )
    (ROOT / "card.fragment.html").write_text(page, encoding="utf-8")
    (ROOT / "index.html").write_text(
        '<!doctype html>\n<html lang="ru">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        "<style>body{margin:0}[hidden]{display:none!important}</style>\n</head>\n<body>\n"
        + page
        + "\n</body>\n</html>\n",
        encoding="utf-8",
    )
    (ROOT / "contact.vcf").write_text(card, encoding="utf-8", newline="")
    print("Готово: index.html, card.fragment.html, contact.vcf")


if __name__ == "__main__":
    main()
