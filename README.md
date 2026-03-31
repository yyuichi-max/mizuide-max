# NHKニュース取得CLI（初心者向け）

毎朝1回実行して、NHKニュースの最新記事をターミナルに見やすく表示するためのシンプルなPythonツールです。  
常駐アプリではなく、**1回実行して終了するCLIツール**として作っています。

---

## 1. このツールでできること

- NHKのRSSから最新ニュースを取得して表示
- 表示内容は以下の3点
  - タイトル
  - 公開日時（取得できる場合）
  - URL
- 表示件数の指定（デフォルト5件）
- 前回表示済み記事を記録し、**新着のみ表示**できる
- `--all` で既読を含む最新N件表示
- `--new-only` で前回以降の新着のみ表示
- `.env`で設定値を変更可能

---

## 2. 動作イメージ

### `python main.py --all` の例

```text
RSS取得先: https://www3.nhk.or.jp/rss/news/cat0.xml
表示モード: 全件
表示件数  : 5
======================================================================
NHKニュース (5件)
======================================================================
[1] 〇〇〇〇〇〇
    公開日時: Tue, 31 Mar 2026 06:00:00 +0900
    URL    : https://www3.nhk.or.jp/news/html/xxxxxxxx.html
----------------------------------------------------------------------
[2] △△△△△△
    公開日時: Tue, 31 Mar 2026 05:30:00 +0900
    URL    : https://www3.nhk.or.jp/news/html/yyyyyyyy.html
----------------------------------------------------------------------
```

### `python main.py --new-only` で新着がない場合

```text
RSS取得先: https://www3.nhk.or.jp/rss/news/cat0.xml
表示モード: 新着のみ
表示件数  : 5
新着ニュースはありませんでした。
```

---

## 3. 必要なもの

- Python 3.11 以上
- インターネット接続
- ターミナル（コマンドプロンプト / PowerShell / macOSターミナル など）

---

## 4. Python のバージョン確認方法

```bash
python --version
```

環境によっては `python3` を使います。

```bash
python3 --version
```

`Python 3.11.x` 以上が表示されればOKです。

---

## 5. Python が入っていない場合の案内

- Windows: 公式サイト https://www.python.org/downloads/windows/ からインストール
- macOS: 公式サイト または Homebrew でインストール
- Linux: 各ディストリビューションのパッケージマネージャでインストール

> 補足: Windowsではインストール時に `Add Python to PATH` にチェックを入れると、`python` コマンドが使いやすくなります。

---

## 6. 仮想環境の作り方

仮想環境（プロジェクト専用のPython環境）を作ると、他のプロジェクトとのライブラリ競合を避けられます。

### Windows

```powershell
python -m venv .venv
```

### macOS / Linux

```bash
python3 -m venv .venv
```

---

## 7. 仮想環境の有効化方法

### Windows

#### PowerShell

```powershell
.\.venv\Scripts\Activate.ps1
```

#### コマンドプロンプト

```bat
.venv\Scripts\activate.bat
```

### macOS / Linux

```bash
source .venv/bin/activate
```

有効化できると、ターミナル行頭に `(.venv)` と表示されることが多いです。

---

## 8. ライブラリのインストール方法

仮想環境を有効化した状態で実行:

```bash
pip install -r requirements.txt
```

---

## 9. `.env` の作り方

`.env.example` をコピーして `.env` を作ります。

### Windows（PowerShell）

```powershell
Copy-Item .env.example .env
```

### macOS / Linux

```bash
cp .env.example .env
```

作成後、必要なら `.env` を編集します。

```env
NHK_RSS_URL=https://www3.nhk.or.jp/rss/news/cat0.xml
NEWS_LIMIT=5
STATE_FILE=.news_state.json
```

RSS URLが取得できない場合の代替候補:

```env
NHK_RSS_URL=https://www.nhk.or.jp/rss/news/cat0.xml
```

---

## 10. 初回実行方法

まずは全件表示で確認するのがおすすめです。

```bash
python main.py --all
```

環境によっては `python3` を使ってください。

```bash
python3 main.py --all
```

---

## 11. よく使うコマンド一覧

```bash
# デフォルト実行（内部的には全件モード）
python main.py

# 最新N件をすべて表示
python main.py --all

# 前回以降の新着のみ表示
python main.py --new-only

# 件数を10件に変更
python main.py --limit 10

# ヘルプ表示
python main.py --help
```

### モードの注意点

- `--all`: 既読を含めて表示
- `--new-only`: 前回までに保存したURLを除外して表示
- 初回実行時は状態ファイルがないため、`--new-only` でも最新記事が表示されます

---

## 12. 毎朝自動実行する方法

このツールは1回実行で終了するので、定期実行はOS標準機能（タスクスケジューラ / cron）を使います。

### Windows タスクスケジューラ（毎朝7:00）

1. 「タスク スケジューラ」を開く
2. 右側の「基本タスクの作成」をクリック
3. 名前を入力（例: `NHK News CLI`）
4. トリガーで「毎日」を選ぶ
5. 開始時刻を `7:00:00` に設定
6. 操作で「プログラムの開始」を選ぶ
7. 以下を設定

- プログラム/スクリプト: 仮想環境のPython実行ファイル（例）
  - `C:\path\to\project\.venv\Scripts\python.exe`
- 引数の追加:
  - `main.py --new-only`
- 開始（作業フォルダー）:
  - `C:\path\to\project`

8. 完了して保存

> 重要: 「開始（作業フォルダー）」をプロジェクトフォルダにしないと、`.env` や状態ファイルが正しく扱えないことがあります。

### macOS / Linux cron（毎朝7:00）

1. ターミナルで以下を実行

```bash
crontab -e
```

2. 次の1行を追加（パスは自分の環境に置き換え）

```cron
0 7 * * * cd /path/to/project && /path/to/project/.venv/bin/python main.py --new-only >> nhk_news.log 2>&1
```

3. 保存して終了

確認:

```bash
crontab -l
```

> 補足: `>> nhk_news.log 2>&1` は実行ログをファイルに残すための設定です（トラブル時の確認に便利）。

---

## 13. トラブルシューティング

### RSS が取得できない

- インターネット接続を確認
- `.env` の `NHK_RSS_URL` を確認
- 代替URLを試す

```env
NHK_RSS_URL=https://www.nhk.or.jp/rss/news/cat0.xml
```

### 文字化けする

- ターミナルの文字コードをUTF-8にする
- Windows Terminal / PowerShell を使うと改善することが多い

### Python が見つからない

- `python --version` でエラーになる場合、`python3 --version` を試す
- Python未インストールなら公式サイトからインストール

### モジュールが見つからない

例: `ModuleNotFoundError: No module named 'feedparser'`

対処:

```bash
pip install -r requirements.txt
```

仮想環境を有効化してから実行してください。

### 前回状態ファイルの削除方法

状態をリセットしたいときは、`STATE_FILE` で指定したファイルを削除します。
デフォルトは `.news_state.json` です。

#### Windows

```powershell
Remove-Item .news_state.json
```

#### macOS / Linux

```bash
rm .news_state.json
```

---

## 14. プロジェクト構成

```text
.
├─ main.py            # メインCLI（RSS取得・表示・状態保存）
├─ requirements.txt   # 依存ライブラリ
├─ .env.example       # 環境変数のサンプル
├─ .gitignore         # Git管理から除外するファイル
└─ README.md          # この説明書
```

---

## 15. 今後の改善案

- カテゴリ別RSSの切り替えコマンド追加
- 通知連携（Slack / Discord / メール）
- 表示フォーマットの切り替え（表形式、Markdown出力）
- ログローテーション対応
- テストコード追加（pytest）

---

## ありがちな失敗例

- `.env.example` のままで `.env` を作っていない
- 仮想環境を有効化せずに `pip install` してしまう
- タスクスケジューラ / cron の作業ディレクトリ未設定
- `--new-only` なのに「新着なし」で壊れたと勘違いする（仕様どおり）

---

## ライセンス

必要に応じて追記してください（例: MIT License）。
