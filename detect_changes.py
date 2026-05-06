#!/usr/bin/env python3
"""
Backrooms JP Wiki 階層リストページの変更検知スクリプト

使い方:
  python3 detect_changes.py

前回のハッシュと比較して変更があれば差分を表示します。
初回実行時は現在の状態を保存するだけです。
"""

import hashlib
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone
from urllib.parse import urlparse

from bs4 import BeautifulSoup

BASE_URL = "http://japan-backrooms-wiki.wikidot.com"
STATE_FILE = "levels_state.json"

def fetch_page(url):
    """URLからHTMLを取得"""
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode('utf-8')

def normalize_path(href):
    """Wikidotのリンクからパスだけを取り出す"""
    parsed = urlparse(href)
    return parsed.path.lstrip('/')

def extract_title_after_link(link):
    """レベルリンク直後のタイトル文字列を取り出す"""
    parts = []
    node = link.next_sibling
    while node:
        if getattr(node, 'name', None) == 'br':
            break
        if isinstance(node, str):
            parts.append(node)
        elif hasattr(node, 'get_text'):
            parts.append(node.get_text(' ', strip=True))
        node = node.next_sibling

    title = ''.join(parts).strip()
    if title.startswith('-'):
        title = title[1:].strip()
    if len(title) >= 2 and title[0] == title[-1] and title[0] in ('"', "'"):
        title = title[1:-1]
    return title

def extract_levels_from_html(html):
    """HTMLからレベルのリンクとタイトル情報を抽出"""
    soup = BeautifulSoup(html, 'html.parser')
    content_div = soup.find('div', id='page-content') or soup
    levels = {}

    for link in content_div.find_all('a', href=True):
        if 'newpage' in (link.get('class') or []):
            continue

        slug = normalize_path(link['href'])
        m = re_fullmatch_level_slug(slug)
        if not m:
            continue

        num = int(m.group(1))
        expected_slug = 'level-0' if num == 0 else f'level-{num}-n'
        if slug != expected_slug:
            continue

        title = extract_title_after_link(link)
        levels[num] = {'slug': slug, 'title': title}
    return levels

def re_fullmatch_level_slug(slug):
    """通常階層のslugだけに一致させる"""
    return re.fullmatch(r'level-(\d+)(?:-n)?', slug)

def main():
    print("Backrooms JP Wiki 変更検知")
    print("=" * 50)
    
    # Fetch current page
    print("ページを取得中...")
    try:
        html = fetch_page(f"{BASE_URL}/normal-levels-i")
    except Exception as e:
        print(f"エラー: ページの取得に失敗しました: {e}")
        sys.exit(1)
    
    current_hash = hashlib.sha256(html.encode()).hexdigest()
    current_levels = extract_levels_from_html(html)
    current_state = {
        'checked_at': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC'),
        'hash': current_hash,
        'level_count': len(current_levels),
        'levels': {str(k): v for k, v in current_levels.items()},
    }
    
    print(f"現在のハッシュ: {current_hash[:16]}...")
    print(f"検出された階層数: {len(current_levels)}")
    
    # Load previous state
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            prev_state = json.load(f)
        
        prev_hash = prev_state.get('hash', '')
        prev_levels = prev_state.get('levels', {})
        
        if current_hash == prev_hash:
            print("\n変更なし: ページは前回チェック時から変わっていません。")
            print(f"前回チェック: {prev_state.get('checked_at', '不明')}")
        else:
            print("\n*** 変更を検出しました ***")
            print(f"前回チェック: {prev_state.get('checked_at', '不明')}")
            
            # Compare level lists
            prev_nums = set(prev_levels.keys())
            curr_nums = set(str(k) for k in current_levels.keys())
            
            added = curr_nums - prev_nums
            removed = prev_nums - curr_nums
            
            if added:
                print(f"\n追加された階層 ({len(added)}件):")
                for n in sorted(added, key=int):
                    info = current_levels.get(int(n), {})
                    print(f"  + Level {n} N: {info.get('title', '?')}")
            
            if removed:
                print(f"\n削除された階層 ({len(removed)}件):")
                for n in sorted(removed, key=int):
                    info = prev_levels.get(n, {})
                    print(f"  - Level {n} N: {info.get('title', '?')}")
            
            # Check title changes
            common = prev_nums & curr_nums
            changed_titles = []
            for n in common:
                prev_title = prev_levels.get(n, {}).get('title', '')
                curr_title = current_levels.get(int(n), {}).get('title', '')
                if prev_title != curr_title:
                    changed_titles.append((n, prev_title, curr_title))
            
            if changed_titles:
                print(f"\nタイトルが変更された階層 ({len(changed_titles)}件):")
                for n, old, new in sorted(changed_titles, key=lambda x: int(x[0])):
                    print(f"  ~ Level {n} N: \"{old}\" → \"{new}\"")
            
            if not added and not removed and not changed_titles:
                print("  (レベルリスト以外の部分が変更されました)")
    else:
        print("\n初回実行: 現在の状態を保存します。")
    
    # Save current state
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(current_state, f, ensure_ascii=False, indent=2)
    
    print(f"\n状態を {STATE_FILE} に保存しました。")

if __name__ == '__main__':
    main()
