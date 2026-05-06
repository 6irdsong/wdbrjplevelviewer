#!/usr/bin/env python3
"""
Backrooms JP Wiki Level Scraper

- Fetches the source normal-level list on every run.
- Fetches each listed level page to get pageId and first content image.
- Uses Wikidot AJAX API to get revision history (creation date + author).
- Outputs JSON that can be rendered for local preview and Wikidot posting.
"""

import argparse
import asyncio
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import aiohttp
from bs4 import BeautifulSoup

BASE_URL = "http://japan-backrooms-wiki.wikidot.com"
AJAX_URL = f"{BASE_URL}/ajax-module-connector.php"
MAIN_LEVELS_PATH = "normal-levels-i"
DEFAULT_OUTPUT = "levels_data.json"
CONCURRENCY = 5
DELAY = 0.3

# Images to ignore (utility/UI images, not content)
IGNORE_IMG_PATTERNS = [
    'black.png', 'blank.png', 'logo.svg', 'avatar.php',
    'userkarma.php', 'favicon', 'component:', 'iosicon',
    'Class0.svg', 'Class1.svg', 'Class2.svg', 'Class3.svg',
    'Class4.svg', 'Class5.svg', 'white.png', 'transparent',
    'rras/', 'wp8icon',
]


def parse_args():
    parser = argparse.ArgumentParser(description="Scrape Backrooms JP Wiki normal levels.")
    parser.add_argument(
        "-o", "--output",
        default=DEFAULT_OUTPUT,
        help=f"JSON output path. Default: {DEFAULT_OUTPUT}",
    )
    parser.add_argument(
        "--build",
        action="store_true",
        help="Also rebuild levels_viewer.html and wikidot_page.txt after scraping.",
    )
    parser.add_argument(
        "--html-output",
        default="levels_viewer.html",
        help="HTML output path used with --build.",
    )
    parser.add_argument(
        "--wikidot-output",
        default="wikidot_page.txt",
        help="Wikidot source output path used with --build.",
    )
    parser.add_argument(
        "--refresh-url",
        default="",
        help="Optional levels_data.json URL used by the in-page update button.",
    )
    parser.add_argument(
        "--wikidot-width",
        default="1280px",
        help="Wikidot wrapper width used with --build.",
    )
    return parser.parse_args()


def level_name(num):
    """Return the public level label used on the JP normal level list."""
    return "Level 0" if num == 0 else f"Level {num} N"


def normalize_path(href):
    """Normalize a Wikidot link href to a path without query or fragment."""
    parsed = urlparse(href)
    return parsed.path.lstrip('/')


def extract_levels_from_list_html(html):
    """Extract all normal level links from the source list page."""
    soup = BeautifulSoup(html, 'html.parser')
    content_div = soup.find('div', id='page-content') or soup
    levels = {}

    for link in content_div.find_all('a', href=True):
        if 'newpage' in (link.get('class') or []):
            continue

        slug = normalize_path(link['href'])
        slug_match = re.fullmatch(r'level-(\d+)(?:-n)?', slug)
        if not slug_match:
            continue

        num = int(slug_match.group(1))
        expected_slug = 'level-0' if num == 0 else f'level-{num}-n'
        if slug != expected_slug:
            continue

        text = link.get_text(' ', strip=True)
        text_match = re.fullmatch(r'Level\s+(\d+)(?:\s*N)?', text)
        if text_match and int(text_match.group(1)) != num:
            continue

        levels[num] = {
            'num': num,
            'name': text if text else level_name(num),
            'slug': slug,
        }

    return [levels[num] for num in sorted(levels)]


def extract_page_id(html):
    """Extract pageId from the HTML."""
    m = re.search(r'pageId\s*=\s*(\d+)', html)
    return int(m.group(1)) if m else None


def extract_first_image(html):
    """Extract the first content image URL, ignoring UI images."""
    soup = BeautifulSoup(html, 'html.parser')
    content_div = soup.find('div', id='page-content')
    if not content_div:
        return None

    for img in content_div.find_all('img'):
        src = img.get('src', '')
        if not src:
            continue
        if any(pattern in src for pattern in IGNORE_IMG_PATTERNS):
            continue
        return src

    return None


def extract_title_from_html(html):
    """Extract the page title from HTML."""
    m = re.search(r'<title>([^<]+)</title>', html)
    if m:
        return m.group(1).replace(' - The Backrooms JP Wiki', '').strip()
    return None


def parse_revision_history(body):
    """Parse revision history HTML to find the oldest revision."""
    revs = re.findall(
        r'<td>(\d+)\.</td>.*?user:info/([^"]+).*?>([^<]+)</a></span>.*?odate time_(\d+)',
        body,
        re.DOTALL,
    )
    if not revs:
        return None, None, None

    oldest = revs[-1]
    ts = int(oldest[3])
    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    return oldest[2], dt.strftime('%Y-%m-%d %H:%M:%S UTC'), ts


async def fetch_main_level_list(session):
    """Fetch the normal levels list page once and return HTML plus hash."""
    url = f"{BASE_URL}/{MAIN_LEVELS_PATH}"
    async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
        if resp.status != 200:
            raise RuntimeError(f"Failed to fetch {url}: HTTP {resp.status}")
        html = await resp.text()
    return html, hashlib.sha256(html.encode()).hexdigest()


async def get_token(session):
    """Get a fresh wikidot_token7 cookie."""
    async with session.get(f"{BASE_URL}/level-0") as resp:
        await resp.text()
    for cookie in session.cookie_jar:
        if cookie.key == 'wikidot_token7':
            return cookie.value
    return None


async def fetch_page(session, slug, semaphore):
    """Fetch page HTML and extract pageId + first image."""
    url = f"{BASE_URL}/{slug}"
    async with semaphore:
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                if resp.status != 200:
                    return slug, None, None, None
                html = await resp.text()
                page_id = extract_page_id(html)
                first_img = extract_first_image(html)
                title = extract_title_from_html(html)
                return slug, page_id, first_img, title
        except Exception as e:
            print(f"  Error fetching {slug}: {e}")
            return slug, None, None, None


async def fetch_history(session, slug, page_id, token, semaphore):
    """Fetch revision history via AJAX API."""
    async with semaphore:
        try:
            data = {
                'page_id': str(page_id),
                'moduleName': 'history/PageRevisionListModule',
                'wikidot_token7': token,
                'perpage': '200',
                'options': '{"all":true}',
            }
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'Referer': f'{BASE_URL}/{slug}',
                'Origin': BASE_URL,
            }
            async with session.post(
                AJAX_URL,
                data=data,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=20),
            ) as resp:
                result = await resp.json(content_type=None)
                if result.get('status') == 'ok':
                    body = result.get('body', '')
                    author, created_at, ts = parse_revision_history(body)
                    return slug, author, created_at, ts
                return slug, None, None, None
        except Exception as e:
            print(f"  Error fetching history for {slug}: {e}")
            return slug, None, None, None


async def main():
    args = parse_args()
    semaphore = asyncio.Semaphore(CONCURRENCY)

    connector = aiohttp.TCPConnector(limit=CONCURRENCY, ttl_dns_cache=300)
    default_headers = {
        'User-Agent': (
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
            '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }
    jar = aiohttp.CookieJar(unsafe=True)

    async with aiohttp.ClientSession(
        connector=connector,
        headers=default_headers,
        cookie_jar=jar,
    ) as session:
        print(f"Fetching source list: {BASE_URL}/{MAIN_LEVELS_PATH}")
        main_html, main_hash = await fetch_main_level_list(session)
        slugs = extract_levels_from_list_html(main_html)
        total = len(slugs)
        if not slugs:
            raise RuntimeError("No levels were found on the source list page.")
        print(f"Found {total} levels on the source list page.")

        token = await get_token(session)
        if not token:
            print("Failed to get wikidot token!")
            return
        print(f"Got token: {token[:8]}...")

        print("\n=== Phase 1: Fetching pages ===")
        batch_size = 10
        page_data = {}
        for i in range(0, total, batch_size):
            batch = slugs[i:i + batch_size]
            tasks = [fetch_page(session, s['slug'], semaphore) for s in batch]
            batch_results = await asyncio.gather(*tasks)
            for slug, page_id, first_img, title in batch_results:
                page_data[slug] = {
                    'page_id': page_id,
                    'first_image': first_img,
                    'title': title,
                }
            done = min(i + batch_size, total)
            print(f"  Pages: {done}/{total}")
            await asyncio.sleep(DELAY)

        token = await get_token(session)

        print("\n=== Phase 2: Fetching revision histories ===")
        history_data = {}
        items_with_pageid = [
            (s, page_data[s['slug']]['page_id'])
            for s in slugs
            if page_data.get(s['slug'], {}).get('page_id')
        ]

        for i in range(0, len(items_with_pageid), batch_size):
            batch = items_with_pageid[i:i + batch_size]
            tasks = [
                fetch_history(session, s['slug'], page_id, token, semaphore)
                for s, page_id in batch
            ]
            batch_results = await asyncio.gather(*tasks)
            for slug, author, created_at, ts in batch_results:
                history_data[slug] = {
                    'author': author,
                    'created_at': created_at,
                    'created_ts': ts,
                }
            done = min(i + batch_size, len(items_with_pageid))
            print(f"  Histories: {done}/{len(items_with_pageid)}")
            await asyncio.sleep(DELAY)

            if (i // batch_size) % 5 == 4:
                token = await get_token(session)

    print("\n=== Combining results ===")
    combined = []
    for s in slugs:
        slug = s['slug']
        pd = page_data.get(slug, {})
        hd = history_data.get(slug, {})
        combined.append({
            'level_num': s['num'],
            'level_name': s['name'],
            'slug': slug,
            'url': f"{BASE_URL}/{slug}",
            'title': pd.get('title'),
            'author': hd.get('author'),
            'created_at': hd.get('created_at'),
            'created_ts': hd.get('created_ts'),
            'first_image': pd.get('first_image'),
        })

    output = {
        'scraped_at': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC'),
        'total_levels': len(combined),
        'source_list_url': f"{BASE_URL}/{MAIN_LEVELS_PATH}",
        'main_page_hash': main_hash,
        'levels': combined,
    }

    outpath = Path(args.output)
    with open(outpath, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nDone! Saved to {outpath}")
    print(f"Total levels: {len(combined)}")
    success = sum(1 for e in combined if e['author'])
    print(f"Successfully scraped: {success}/{len(combined)}")

    print("\nSample entries:")
    for e in combined[:5]:
        has_image = 'Yes' if e['first_image'] else 'No'
        print(f"  {e['level_name']}: author={e['author']}, created={e['created_at']}, img={has_image}")

    if args.build:
        from build_viewer import build_outputs

        build_outputs(
            outpath,
            Path(args.html_output),
            Path(args.wikidot_output),
            args.refresh_url,
            args.wikidot_width,
        )


if __name__ == '__main__':
    asyncio.run(main())
