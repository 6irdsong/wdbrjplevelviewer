# Backrooms JP Wiki 階層ビューア

Backrooms JP Wiki の通常階層一覧から階層ページを収集し、ローカル確認用 HTML と Wikidot 投稿用ソースを生成するプロジェクトです。

## ファイル

- `scraper.py`: 元ページ `normal-levels-i` から全階層リンクを取得し、各階層の作者・作成日時・最初の画像を収集します。
- `levels_data.json`: スクレイピング結果です。
- `build_viewer.py`: `levels_data.json` から `levels_viewer.html` と `wikidot_page.txt` を生成します。
- `levels_viewer.html`: ローカルで確認するための静的 HTML です。
- `wikidot_page.txt`: Wikidot のページ本文に貼り付ける `[[html]]` ブロックです。
- `detect_changes.py`: 元ページの追加・削除・タイトル変更を前回チェック時と比較します。

## 初期準備

```bash
python3 -m pip install -r requirements.txt
```

## 更新手順

元ページから最新データを取得し、表示用ファイルまでまとめて生成します。

```bash
python3 scraper.py --build
```

生成された `wikidot_page.txt` の中身を Wikidot の投稿ページに貼り付けます。ローカルで見た目を確認する場合は `levels_viewer.html` をブラウザで開きます。

Wikidot 側の表示幅は、投稿用ソース内で `1280px` まで広げる設定にしています。幅を変える場合は次のように指定します。

```bash
python3 scraper.py --build --wikidot-width 1400px
```

## ページ内更新ボタン

Wikidot のファイルストレージに `.py` をアップロードしても、Wikidot 上では Python は実行されません。ページ内の更新ボタンで直接スクレイピングするには、別のサーバーや GitHub Actions など、Python を実行できる場所が必要です。

静的運用では、`levels_data.json` を Wikidot のファイルとしてアップロードし、その URL を指定して投稿用ソースを生成します。

```bash
python3 scraper.py --build --refresh-url "https://example.wikidot.com/local--files/page-name/levels_data.json"
```

この場合、ページ内の「更新」ボタンは指定 URL の JSON を再取得して表示だけを更新します。JSON 自体を最新にするには、手元または外部CIで `scraper.py` を実行し、生成された `levels_data.json` をアップロードし直してください。

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

Wikidot に貼る本文は、Actions 実行後に生成される `wikidot_page.txt` の中身です。更新ボタンは GitHub Pages 上の `levels_data.json` を読み直します。

## 変更検知だけを行う

```bash
python3 detect_changes.py
```

変更があった場合は、追加・削除・タイトル変更の概要が表示されます。その後 `python3 scraper.py --build` を実行すると、元ページの現在の階層リストに合わせて再生成できます。
