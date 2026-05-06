#!/usr/bin/env python3
"""Build the local HTML viewer and Wikidot page source from levels_data.json."""

import argparse
import json
from pathlib import Path

DEFAULT_DATA = "levels_data.json"
DEFAULT_HTML = "levels_viewer.html"
DEFAULT_WIKIDOT = "wikidot_page.txt"
DEFAULT_SOURCE_LIST_URL = "http://japan-backrooms-wiki.wikidot.com/normal-levels-i"
DEFAULT_WIKIDOT_WIDTH = "1280px"
PAGE_TITLE = "Backrooms JP Wiki - 階層一覧"

STYLE = r"""
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@300;400;500;700&family=JetBrains+Mono:wght@400&display=swap');

.level-viewer, .level-viewer * {
  box-sizing: border-box;
}

.level-viewer {
  --bg: #0a0a0c;
  --surface: #111115;
  --surface2: #1a1a20;
  --border: #2a2a32;
  --text: #c8c8d0;
  --text-dim: #6a6a78;
  --accent: #ff6b61;
  --accent2: #4a9eff;

  margin: 0;
  min-height: 100vh;
  background: var(--bg);
  color: var(--text);
  font-family: 'Noto Sans JP', sans-serif;
  line-height: 1.6;
}

.level-viewer a {
  color: inherit;
}

.lv-header {
  padding: 2rem 2rem 1rem;
  border-bottom: 1px solid var(--border);
  background: linear-gradient(180deg, #12121a 0%, var(--bg) 100%);
}

.lv-header h1 {
  margin: 0;
  color: #fff;
  font-size: 1.4rem;
  font-weight: 700;
  letter-spacing: 0;
}

.lv-header h1 span {
  color: var(--accent);
}

.lv-meta {
  display: flex;
  gap: 1.5rem;
  margin-top: 0.5rem;
  color: var(--text-dim);
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
}

.lv-controls {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 1rem;
  padding: 1rem 2rem;
  border-bottom: 1px solid var(--border);
  background: var(--surface);
}

.lv-search {
  flex: 1 1 200px;
  max-width: 400px;
  padding: 0.5rem 0.8rem;
  border: 1px solid var(--border);
  border-radius: 6px;
  outline: none;
  background: var(--bg);
  color: var(--text);
  font: inherit;
  font-size: 0.9rem;
  transition: border-color 0.2s;
}

.lv-search:focus {
  border-color: var(--accent);
}

.lv-sort-btn {
  padding: 0.4rem 0.8rem;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--surface2);
  color: var(--text-dim);
  cursor: pointer;
  font: inherit;
  font-size: 0.8rem;
  transition: border-color 0.2s, color 0.2s, background 0.2s;
}

.lv-refresh-btn {
  padding: 0.4rem 0.8rem;
  border: 1px solid var(--accent2);
  border-radius: 6px;
  background: rgba(74, 158, 255, 0.08);
  color: var(--accent2);
  cursor: pointer;
  font: inherit;
  font-size: 0.8rem;
  transition: border-color 0.2s, color 0.2s, background 0.2s;
}

.lv-sort-btn:hover {
  border-color: var(--text-dim);
  color: var(--text);
}

.lv-refresh-btn:hover {
  background: rgba(74, 158, 255, 0.14);
  color: #8fc4ff;
}

.lv-refresh-btn:disabled {
  cursor: wait;
  opacity: 0.65;
}

.lv-sort-btn.active {
  border-color: var(--accent);
  background: rgba(255, 107, 97, 0.08);
  color: var(--accent);
}

.lv-count {
  margin-left: auto;
  color: var(--text-dim);
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
}

.lv-refresh-status {
  flex-basis: 100%;
  min-height: 1.2em;
  color: var(--text-dim);
  font-size: 0.75rem;
}

.lv-view-toggle {
  display: flex;
  gap: 0.25rem;
  padding: 2px;
  border-radius: 6px;
  background: var(--bg);
}

.lv-view-btn {
  padding: 0.3rem 0.6rem;
  border: 0;
  border-radius: 4px;
  background: transparent;
  color: var(--text-dim);
  cursor: pointer;
  font: inherit;
  font-size: 0.8rem;
}

.lv-view-btn.active {
  background: var(--surface2);
  color: var(--text);
}

.lv-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 1px;
  margin: 0;
  background: var(--border);
}

.lv-card {
  display: block;
  padding: 0;
  background: var(--surface);
  color: inherit;
  text-decoration: none;
  transition: background 0.2s;
}

.lv-card:hover {
  background: var(--surface2);
}

.lv-card-img {
  display: block;
  width: 100%;
  height: 160px;
  border-bottom: 1px solid var(--border);
  background: var(--bg);
  object-fit: cover;
}

.lv-card-img.no-img {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-dim);
  font-size: 0.8rem;
}

.lv-card-body {
  padding: 0.8rem 1rem;
}

.lv-card-level {
  color: var(--accent);
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  letter-spacing: 0;
  text-transform: uppercase;
}

.lv-card-title {
  overflow: hidden;
  margin-top: 0.2rem;
  color: #fff;
  font-size: 0.95rem;
  font-weight: 500;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.lv-card-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  margin-top: 0.5rem;
  color: var(--text-dim);
  font-size: 0.75rem;
}

.lv-card-author,
.lv-author-cell {
  color: var(--accent2);
}

.lv-card-date,
.lv-date-cell,
.lv-level-cell {
  font-family: 'JetBrains Mono', monospace;
}

.lv-card-date {
  font-size: 0.7rem;
  white-space: nowrap;
}

.lv-table-view {
  display: none;
  overflow-x: auto;
}

.lv-table-view table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
}

.lv-table-view th {
  padding: 0.6rem 1rem;
  border-bottom: 1px solid var(--border);
  background: var(--surface2);
  color: var(--text-dim);
  cursor: pointer;
  font-size: 0.75rem;
  font-weight: 500;
  letter-spacing: 0;
  text-align: left;
  text-transform: uppercase;
  user-select: none;
  white-space: nowrap;
}

.lv-table-view th:hover {
  color: var(--text);
}

.lv-table-view th.sorted {
  color: var(--accent);
}

.lv-table-view td {
  padding: 0.4rem 1rem;
  border-bottom: 1px solid var(--border);
  vertical-align: middle;
}

.lv-table-view tr:hover td {
  background: var(--surface2);
}

.lv-table-view a {
  color: var(--accent2);
  text-decoration: none;
}

.lv-table-view a:hover {
  text-decoration: underline;
}

.lv-thumb {
  display: block;
  width: 64px;
  height: 40px;
  border-radius: 3px;
  background: var(--bg);
  object-fit: cover;
}

.lv-thumb.no-img {
  color: var(--text-dim);
  font-size: 0.7rem;
}

.lv-level-cell {
  color: var(--accent);
  font-size: 0.8rem;
}

.lv-date-cell {
  font-size: 0.8rem;
  white-space: nowrap;
}

.lv-hash-info {
  padding: 1rem 2rem;
  border-top: 1px solid var(--border);
  background: var(--surface);
  color: var(--text-dim);
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  overflow-wrap: anywhere;
}

@media (max-width: 600px) {
  .lv-header {
    padding: 1rem;
  }

  .lv-controls {
    padding: 0.8rem 1rem;
  }

  .lv-grid {
    grid-template-columns: 1fr 1fr;
  }

  .lv-card-img {
    height: 120px;
  }

  .lv-meta {
    flex-direction: column;
    gap: 0.3rem;
  }
}
""".strip()

APP_TEMPLATE = r"""
<style>
__STYLE__
</style>

<div class="level-viewer" id="levelViewer">
  <header class="lv-header">
    <h1><span>The Backrooms JP Wiki</span> 階層一覧</h1>
    <div class="lv-meta">
      <span id="lvScrapedAt"></span>
      <span id="lvTotalLevels"></span>
    </div>
  </header>

  <div class="lv-controls">
    <input type="text" class="lv-search" id="lvSearch" placeholder="階層名、著者で検索...">
    <div class="lv-view-toggle" aria-label="表示形式">
      <button type="button" class="lv-view-btn active" data-view="grid">Grid</button>
      <button type="button" class="lv-view-btn" data-view="table">Table</button>
    </div>
    <button type="button" class="lv-sort-btn active" data-sort="num">番号順</button>
    <button type="button" class="lv-sort-btn" data-sort="date">投稿日順</button>
    <button type="button" class="lv-sort-btn" data-sort="author">著者順</button>
    <button type="button" class="lv-refresh-btn" id="lvRefresh">更新</button>
    <span class="lv-count" id="lvCount"></span>
    <span class="lv-refresh-status" id="lvRefreshStatus"></span>
  </div>

  <div class="lv-grid" id="lvGrid"></div>

  <div class="lv-table-view" id="lvTableView">
    <table>
      <thead>
        <tr>
          <th data-sort="num" id="lvThNum" class="sorted">No.</th>
          <th>画像</th>
          <th data-sort="title" id="lvThTitle">タイトル</th>
          <th data-sort="author" id="lvThAuthor">著者</th>
          <th data-sort="date" id="lvThDate">投稿日</th>
        </tr>
      </thead>
      <tbody id="lvTbody"></tbody>
    </table>
  </div>

  <div class="lv-hash-info" id="lvHashInfo"></div>
</div>

<script id="levels-data" type="application/json">__DATA_JSON__</script>
<script>
(() => {
  const dataEl = document.getElementById('levels-data');
  const embeddedData = JSON.parse(dataEl.textContent);
  const refreshUrl = __REFRESH_URL__;
  let data = embeddedData;
  let levels = Array.isArray(data.levels) ? data.levels : [];
  const state = {
    sort: 'num',
    dir: 1,
    view: 'grid',
    query: '',
  };

  const el = {
    scrapedAt: document.getElementById('lvScrapedAt'),
    totalLevels: document.getElementById('lvTotalLevels'),
    search: document.getElementById('lvSearch'),
    refresh: document.getElementById('lvRefresh'),
    refreshStatus: document.getElementById('lvRefreshStatus'),
    count: document.getElementById('lvCount'),
    grid: document.getElementById('lvGrid'),
    tableView: document.getElementById('lvTableView'),
    tbody: document.getElementById('lvTbody'),
    hashInfo: document.getElementById('lvHashInfo'),
    sortButtons: Array.from(document.querySelectorAll('.lv-sort-btn')),
    viewButtons: Array.from(document.querySelectorAll('.lv-view-btn')),
    tableHeaders: Array.from(document.querySelectorAll('.lv-table-view th[data-sort]')),
  };

  const sortHeaderIds = {
    num: 'lvThNum',
    title: 'lvThTitle',
    author: 'lvThAuthor',
    date: 'lvThDate',
  };

  function valueText(value, fallback) {
    if (value === null || value === undefined || value === '') return fallback;
    return String(value);
  }

  function formatDate(dateStr) {
    if (!dateStr) return '-';
    return String(dateStr).replace(' UTC', '').slice(0, 10);
  }

  function clear(node) {
    while (node.firstChild) node.removeChild(node.firstChild);
  }

  function appendText(parent, className, text) {
    const node = document.createElement('span');
    node.className = className;
    node.textContent = text;
    parent.appendChild(node);
    return node;
  }

  function makeNoImage(className) {
    const node = document.createElement('div');
    node.className = className + ' no-img';
    node.textContent = 'No Image';
    return node;
  }

  function makeImage(className, src) {
    if (!src) return makeNoImage(className);
    const img = document.createElement('img');
    img.className = className;
    img.src = src;
    img.loading = 'lazy';
    img.alt = '';
    img.onerror = () => img.replaceWith(makeNoImage(className));
    return img;
  }

  function sortedLevels(items) {
    return Array.from(items).sort((a, b) => {
      let va;
      let vb;
      switch (state.sort) {
        case 'date':
          va = a.created_ts || 0;
          vb = b.created_ts || 0;
          return state.dir * (va - vb);
        case 'author':
          va = valueText(a.author, '').toLowerCase();
          vb = valueText(b.author, '').toLowerCase();
          return state.dir * va.localeCompare(vb, 'ja');
        case 'title':
          va = valueText(a.title || a.level_name, '');
          vb = valueText(b.title || b.level_name, '');
          return state.dir * va.localeCompare(vb, 'ja');
        case 'num':
        default:
          va = a.level_num || 0;
          vb = b.level_num || 0;
          return state.dir * (va - vb);
      }
    });
  }

  function filteredLevels() {
    const q = state.query.trim().toLowerCase();
    if (!q) return levels;
    return levels.filter((entry) => {
      return valueText(entry.level_name, '').toLowerCase().includes(q)
        || valueText(entry.title, '').toLowerCase().includes(q)
        || valueText(entry.author, '').toLowerCase().includes(q)
        || String(entry.level_num).includes(q);
    });
  }

  function renderGrid(items) {
    clear(el.grid);
    const fragment = document.createDocumentFragment();
    items.forEach((entry) => {
      const card = document.createElement('a');
      card.className = 'lv-card';
      card.href = valueText(entry.url, '#');
      card.target = '_blank';
      card.rel = 'noopener';

      card.appendChild(makeImage('lv-card-img', entry.first_image));

      const body = document.createElement('div');
      body.className = 'lv-card-body';
      const level = document.createElement('div');
      level.className = 'lv-card-level';
      level.textContent = 'Level ' + entry.level_num;
      const title = document.createElement('div');
      title.className = 'lv-card-title';
      title.textContent = valueText(entry.title || entry.level_name, '-');

      const meta = document.createElement('div');
      meta.className = 'lv-card-meta';
      appendText(meta, 'lv-card-author', valueText(entry.author, '-'));
      appendText(meta, 'lv-card-date', formatDate(entry.created_at));

      body.appendChild(level);
      body.appendChild(title);
      body.appendChild(meta);
      card.appendChild(body);
      fragment.appendChild(card);
    });
    el.grid.appendChild(fragment);
  }

  function appendCell(row, className, childOrText) {
    const cell = document.createElement('td');
    if (className) cell.className = className;
    if (childOrText instanceof Node) {
      cell.appendChild(childOrText);
    } else {
      cell.textContent = childOrText;
    }
    row.appendChild(cell);
    return cell;
  }

  function renderTable(items) {
    clear(el.tbody);
    const fragment = document.createDocumentFragment();
    items.forEach((entry) => {
      const row = document.createElement('tr');
      appendCell(row, 'lv-level-cell', String(entry.level_num));
      appendCell(row, '', makeImage('lv-thumb', entry.first_image));

      const link = document.createElement('a');
      link.href = valueText(entry.url, '#');
      link.target = '_blank';
      link.rel = 'noopener';
      link.textContent = valueText(entry.title || entry.level_name, '-');
      appendCell(row, '', link);

      appendCell(row, 'lv-author-cell', valueText(entry.author, '-'));
      appendCell(row, 'lv-date-cell', formatDate(entry.created_at));
      fragment.appendChild(row);
    });
    el.tbody.appendChild(fragment);
  }

  function updateActiveSort() {
    el.sortButtons.forEach((button) => {
      button.classList.toggle('active', button.dataset.sort === state.sort);
    });
    el.tableHeaders.forEach((th) => th.classList.remove('sorted'));
    const header = document.getElementById(sortHeaderIds[state.sort]);
    if (header) header.classList.add('sorted');
  }

  function render() {
    const items = sortedLevels(filteredLevels());
    el.count.textContent = String(items.length) + ' / ' + String(levels.length);
    if (state.view === 'grid') {
      renderGrid(items);
    } else {
      renderTable(items);
    }
  }

  function setMeta() {
    el.scrapedAt.textContent = '取得日時: ' + valueText(data.scraped_at, '-');
    el.totalLevels.textContent = '全 ' + String(levels.length) + ' 階層';
    el.hashInfo.textContent = '元ページ: ' + valueText(data.source_list_url, '-') + ' / SHA-256: ' + valueText(data.main_page_hash, '-');
  }

  function setRefreshStatus(message, isError) {
    el.refreshStatus.textContent = message;
    el.refreshStatus.style.color = isError ? 'var(--accent)' : 'var(--text-dim)';
  }

  function applyData(nextData) {
    data = nextData && typeof nextData === 'object' ? nextData : embeddedData;
    levels = Array.isArray(data.levels) ? data.levels : [];
    setMeta();
    render();
  }

  async function refreshData() {
    if (!refreshUrl) {
      setRefreshStatus('ページを再読み込みしています...', false);
      window.location.reload();
      return;
    }

    const separator = refreshUrl.includes('?') ? '&' : '?';
    const url = refreshUrl + separator + 't=' + Date.now();
    el.refresh.disabled = true;
    setRefreshStatus('最新データを取得しています...', false);

    try {
      const response = await fetch(url, { cache: 'no-store' });
      if (!response.ok) {
        throw new Error('HTTP ' + response.status);
      }
      const nextData = await response.json();
      applyData(nextData);
      setRefreshStatus('更新しました: ' + valueText(nextData.scraped_at, '-'), false);
    } catch (error) {
      setRefreshStatus('更新できませんでした。データURLまたは接続を確認してください。', true);
    } finally {
      el.refresh.disabled = false;
    }
  }

  function setSort(sortKey) {
    if (state.sort === sortKey) {
      state.dir *= -1;
    } else {
      state.sort = sortKey;
      state.dir = 1;
    }
    updateActiveSort();
    render();
  }

  function setView(view) {
    state.view = view;
    el.viewButtons.forEach((button) => {
      button.classList.toggle('active', button.dataset.view === view);
    });
    el.grid.style.display = view === 'grid' ? 'grid' : 'none';
    el.tableView.style.display = view === 'table' ? 'block' : 'none';
    render();
  }

  setMeta();

  el.search.addEventListener('input', (event) => {
    state.query = event.target.value;
    render();
  });

  el.sortButtons.forEach((button) => {
    button.addEventListener('click', () => setSort(button.dataset.sort));
  });

  el.refresh.addEventListener('click', refreshData);

  el.tableHeaders.forEach((th) => {
    th.addEventListener('click', () => setSort(th.dataset.sort));
  });

  el.viewButtons.forEach((button) => {
    button.addEventListener('click', () => setView(button.dataset.view));
  });

  updateActiveSort();
  render();
})();
</script>
""".strip()


def json_for_script(data):
    text = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    return text.replace('</', '<\\/')


def build_app_markup(data, refresh_url=""):
    return (
        APP_TEMPLATE
        .replace("__STYLE__", STYLE)
        .replace("__DATA_JSON__", json_for_script(data))
        .replace("__REFRESH_URL__", json.dumps(refresh_url, ensure_ascii=False))
    )


def build_local_html(app_markup):
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{PAGE_TITLE}</title>
<style>
body {{
  margin: 0;
  background: #0a0a0c;
}}
</style>
</head>
<body>
{app_markup}
</body>
</html>
"""


def build_wikidot_source(app_markup, width=DEFAULT_WIKIDOT_WIDTH):
    return (
        f'[[div style="width: {width}; max-width: 96vw; margin-left: 50%; transform: translateX(-50%);"]]\n'
        f"[[html]]\n{app_markup}\n[[/html]]\n"
        "[[/div]]\n"
    )


def build_outputs(
    data_path=DEFAULT_DATA,
    html_path=DEFAULT_HTML,
    wikidot_path=DEFAULT_WIKIDOT,
    refresh_url="",
    wikidot_width=DEFAULT_WIKIDOT_WIDTH,
):
    data_path = Path(data_path)
    html_path = Path(html_path)
    wikidot_path = Path(wikidot_path)

    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    data.setdefault('source_list_url', DEFAULT_SOURCE_LIST_URL)

    app_markup = build_app_markup(data, refresh_url)
    html_path.write_text(build_local_html(app_markup), encoding='utf-8')
    wikidot_path.write_text(build_wikidot_source(app_markup, wikidot_width), encoding='utf-8')

    levels = data.get('levels') or []
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
    parser.add_argument(
        "--refresh-url",
        default="",
        help="Optional levels_data.json URL used by the in-page update button.",
    )
    parser.add_argument(
        "--wikidot-width",
        default=DEFAULT_WIKIDOT_WIDTH,
        help=f"Wikidot wrapper width. Default: {DEFAULT_WIKIDOT_WIDTH}",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    build_outputs(args.data, args.html, args.wikidot, args.refresh_url, args.wikidot_width)


if __name__ == "__main__":
    main()
