#!/usr/bin/env python3
"""Build the local HTML preview and Wikidot-native page source from levels_data.json."""

import argparse
import html
import json
import re
from pathlib import Path

DEFAULT_DATA = "levels_data.json"
DEFAULT_HTML = "levels_viewer.html"
DEFAULT_WIKIDOT = "wikidot_page.txt"
PAGE_TITLE = "Backrooms JP Wiki - 階層一覧"

STYLE = r"""
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@300;400;500;700&family=JetBrains+Mono:wght@400&display=swap');

.lv-outer, .level-viewer, .level-viewer * {
  box-sizing: border-box;
}

.lv-outer {
  width: 1680px;
  max-width: 96vw;
  margin-left: 50%;
  transform: translateX(-50%);
}

.level-viewer {
  --surface2: #1a1a20;
  --border: #2a2a32;
  --text: #c8c8d0;
  --text-dim: #6a6a78;
  --accent: #ff6b61;
  --accent2: #4a9eff;

  margin: 0;
  background: transparent;
  color: var(--text);
  font-family: 'Noto Sans JP', sans-serif;
  line-height: 1.6;
}

.level-viewer a {
  color: inherit;
}

.lv-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 0;
  margin: 0;
  background: transparent;
}

.lv-card {
  display: flex;
  flex-direction: column;
  padding: 0;
  background: transparent;
  color: inherit;
  text-decoration: none;
  outline: 1px solid var(--border);
  outline-offset: -1px;
}

.lv-card-img {
  display: block;
  width: 100%;
  height: 160px;
  border-bottom: 1px solid var(--border);
  background: transparent;
  object-fit: cover;
}

.lv-card-img.no-img {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-dim);
  font-size: 0.88rem;
}

.lv-card-body {
  display: flex;
  flex-direction: column;
  flex: 1;
  padding: 0.8rem 1rem;
}

.lv-card-level {
  color: var(--accent);
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.78rem;
  letter-spacing: 0;
  text-transform: uppercase;
}

.lv-card-level.is-sub {
  color: #a8625a;
}

.lv-card.is-sub {
  align-self: end;
}

.lv-card.is-sub .lv-card-body {
  padding: 0.1rem 1rem 0.8rem;
}

.lv-card-title {
  margin-top: 0.2rem;
  padding-top: 0.5em;
  color: #fff;
  font-size: 1.05rem;
  font-weight: 500;
  word-break: break-word;
  min-height: calc(1.05rem * 1.6 * 2 + 0.5em);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.lv-card-title a {
  color: inherit;
  text-decoration: none;
}

.lv-card-title a:hover {
  text-decoration: underline;
}

.lv-card-title .ruby {
  display: inline-block;
  position: relative;
  vertical-align: baseline;
}

.lv-card-title .ruby .rt {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 100%;
  color: var(--text-dim);
  font-size: 0.5em;
  font-weight: 400;
  line-height: 1;
  text-align: center;
  white-space: nowrap;
}

.lv-card-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  margin-top: auto;
  padding-top: 0.5rem;
  color: var(--text-dim);
  font-size: 0.82rem;
}

.lv-card-author {
  color: var(--accent2);
}

.lv-card-date {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.78rem;
  white-space: nowrap;
}

@media (max-width: 600px) {
  .lv-grid {
    grid-template-columns: 1fr 1fr;
  }

  .lv-card-img {
    height: 120px;
  }
}
""".strip()


def safe_wiki_text(text):
    """Neutralize Wikidot bracket syntax in user-controlled text."""
    if text is None or text == "":
        return "-"
    return str(text).replace("[[", "[​[").replace("]]", "]​]")


def safe_url(url):
    """Strip whitespace and brackets from a URL so it cannot break Wikidot syntax."""
    if not url:
        return ""
    return str(url).replace(" ", "%20").replace("[[", "").replace("]]", "")


def format_date(date_str):
    if not date_str:
        return "-"
    return str(date_str).replace(" UTC", "")[:10]


SPAN_OPEN_RE = re.compile(r"<span\b([^>]*)>", re.IGNORECASE)
SPAN_CLOSE_RE = re.compile(r"</span\s*>", re.IGNORECASE)
ANY_TAG_RE = re.compile(r"<[^>]+>")


def html_to_wikidot(text):
    """Translate the small inline-HTML subset used in subtitles to Wikidot syntax."""
    if not text:
        return text
    text = SPAN_OPEN_RE.sub(lambda m: f"[[span{m.group(1)}]]", text)
    text = SPAN_CLOSE_RE.sub("[[/span]]", text)
    # Drop any other stray tags but keep their inner text.
    text = ANY_TAG_RE.sub("", text)
    return text


def render_subtitle_wikidot(entry):
    sub = entry.get("subtitle")
    if sub:
        return html_to_wikidot(sub)
    return safe_wiki_text(entry.get("title") or entry.get("level_name"))


def render_subtitle_html(entry):
    sub = entry.get("subtitle")
    if sub:
        return sub
    return html.escape(entry.get("title") or entry.get("level_name") or "-")


def build_wikidot_card(entry):
    num = entry.get("level_num", 0)
    url = safe_url(entry.get("url", ""))
    title = render_subtitle_wikidot(entry)
    author = safe_wiki_text(entry.get("author"))
    date = safe_wiki_text(format_date(entry.get("created_at")))
    img = safe_url(entry.get("first_image") or "")
    is_sub = bool(entry.get("is_sub"))
    card_class = "lv-card is-sub" if is_sub else "lv-card"
    level_class = "lv-card-level is-sub" if is_sub else "lv-card-level"

    if img:
        img_block = f'[[image {img} class="lv-card-img"]]'
    else:
        img_block = '[[div class="lv-card-img no-img"]]\nNo Image\n[[/div]]'

    if url:
        title_block = f'[[a href="{url}" target="_blank"]]{title}[[/a]]'
    else:
        title_block = title

    return (
        f'[[div class="{card_class}"]]\n'
        f'{img_block}\n'
        '[[div class="lv-card-body"]]\n'
        f'[[div class="{level_class}"]]\nLevel {num}\n[[/div]]\n'
        f'[[div class="lv-card-title"]]\n{title_block}\n[[/div]]\n'
        '[[div class="lv-card-meta"]]\n'
        f'[[span class="lv-card-author"]]{author}[[/span]]\n'
        f'[[span class="lv-card-date"]]{date}[[/span]]\n'
        '[[/div]]\n'
        '[[/div]]\n'
        '[[/div]]'
    )


def build_wikidot_source(data):
    levels = data.get("levels") or []
    cards = "\n\n".join(build_wikidot_card(e) for e in levels)

    return (
        "[[module CSS]]\n"
        f"{STYLE}\n"
        "[[/module]]\n"
        "\n"
        '[[div class="lv-outer"]]\n'
        '[[div class="level-viewer"]]\n'
        '[[div class="lv-grid"]]\n'
        f"{cards}\n"
        "[[/div]]\n"
        "[[/div]]\n"
        "[[/div]]\n"
    )


def html_card(entry):
    num = entry.get("level_num", 0)
    url = html.escape(entry.get("url", ""), quote=True)
    title = render_subtitle_html(entry)
    author = html.escape(entry.get("author") or "-")
    date = html.escape(format_date(entry.get("created_at")))
    img = entry.get("first_image")
    is_sub = bool(entry.get("is_sub"))
    card_class = "lv-card is-sub" if is_sub else "lv-card"
    level_class = "lv-card-level is-sub" if is_sub else "lv-card-level"

    if img:
        img_html = f'<img class="lv-card-img" src="{html.escape(img, quote=True)}" loading="lazy" alt="">'
    else:
        img_html = '<div class="lv-card-img no-img">No Image</div>'

    title_html = f'<a href="{url}" target="_blank" rel="noopener">{title}</a>' if url else title

    return (
        f'<div class="{card_class}">\n'
        f'  {img_html}\n'
        '  <div class="lv-card-body">\n'
        f'    <div class="{level_class}">Level {num}</div>\n'
        f'    <div class="lv-card-title">{title_html}</div>\n'
        '    <div class="lv-card-meta">\n'
        f'      <span class="lv-card-author">{author}</span>\n'
        f'      <span class="lv-card-date">{date}</span>\n'
        '    </div>\n'
        '  </div>\n'
        '</div>'
    )


def build_local_html(data):
    levels = data.get("levels") or []
    cards = "\n".join(html_card(e) for e in levels)

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{PAGE_TITLE}</title>
<style>
body {{
  margin: 0;
}}
{STYLE}
</style>
</head>
<body>
<div class="level-viewer">
  <div class="lv-grid">
{cards}
  </div>
</div>
</body>
</html>
"""


def build_outputs(data_path=DEFAULT_DATA, html_path=DEFAULT_HTML, wikidot_path=DEFAULT_WIKIDOT):
    data_path = Path(data_path)
    html_path = Path(html_path)
    wikidot_path = Path(wikidot_path)

    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    html_path.write_text(build_local_html(data), encoding="utf-8")
    wikidot_path.write_text(build_wikidot_source(data), encoding="utf-8")

    levels = data.get("levels") or []
    print(f"Built {html_path} ({len(levels)} levels)")
    print(f"Built {wikidot_path} for Wikidot posting")


def parse_args():
    parser = argparse.ArgumentParser(description="Build viewer files from levels_data.json.")
    parser.add_argument("--data", default=DEFAULT_DATA, help=f"Input JSON. Default: {DEFAULT_DATA}")
    parser.add_argument("--html", default=DEFAULT_HTML, help=f"Local HTML output. Default: {DEFAULT_HTML}")
    parser.add_argument(
        "--wikidot",
        default=DEFAULT_WIKIDOT,
        help=f"Wikidot source output. Default: {DEFAULT_WIKIDOT}",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    build_outputs(args.data, args.html, args.wikidot)


if __name__ == "__main__":
    main()
