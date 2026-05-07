# Backrooms JP Wiki 階層ビューア

Backrooms JP Wiki の通常階層一覧から階層ページを収集し、ローカル確認用 HTML と Wikidot 投稿用ソース（ネイティブ構文 + `[[module CSS]]`）を生成するプロジェクトです。

## ファイル

- `scraper.py`: 元ページ `normal-levels-i` から全階層リンクを取得し、各階層の作者・作成日時・最初の画像を収集します。
- `levels_data.json`: スクレイピング結果です。
- `build_viewer.py`: `levels_data.json` から `levels_viewer.html` と `wikidot_page.txt` を生成します。
- `levels_viewer.html`: ローカルで確認するための静的 HTML です（JS なし）。
- `wikidot_page.txt`: Wikidot のページ本文に貼り付けるネイティブ構文ソースです。

## 初期準備

```bash
python3 -m pip install -r requirements.txt
```

## 更新手順

元ページから最新データを取得し、表示用ファイルまでまとめて生成します。

```bash
python3 scraper.py --build
```

生成された `wikidot_page.txt` の中身を Wikidot の投稿ページにコピー＆ペーストして反映します。ローカルで見た目を確認する場合は `levels_viewer.html` をブラウザで開きます。

`wikidot_page.txt` は Wikidot のネイティブ構文（`[[div class]]`、`[[image]]`、`[[a]]` など）と `[[module CSS]]` のみで構成されており、`[[html]]` ブロックは含みません。検索・ソート・更新ボタンといったインタラクティブ要素はありません（静的表示のみ）。

## GitHub Actions で自動更新する

`.github/workflows/update-levels.yml` を追加済みです。このプロジェクトを GitHub に置くと、毎日 03:17 JST に次の処理をします。

1. `scraper.py --build` で最新データを取得
2. `levels_data.json` / `levels_viewer.html` / `wikidot_page.txt` を更新
3. GitHub Pages に `levels_data.json` と確認用 HTML を公開
4. 生成ファイルをリポジトリにコミット

初回セットアップ:

```bash
git init
git add .
git commit -m "Initial levels viewer"
git branch -M main
git remote add origin https://github.com/USER/REPO.git
git push -u origin main
```

GitHub 側で、リポジトリの `Settings > Pages` を開き、Source を `GitHub Actions` にします。その後 `Actions > Update levels data > Run workflow` を一度実行します。

GitHub Pages の公開URLは通常この形です。

```text
https://USER.github.io/REPO/
```

Wikidot に貼る本文は、Actions 実行後に生成される `wikidot_page.txt` の中身です。Wikidot ページは静的なので、最新のデータを反映するには Actions が走った後に `wikidot_page.txt` を再度コピー＆ペーストする必要があります。
