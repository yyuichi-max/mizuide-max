# NHKニュース毎朝メール送信ツール（初心者向け）

このプロジェクトは、NHKのRSSニュースを取得して、**毎朝1回メールで受け取る**ためのPython CLIツールです。  
常駐（ずっと動き続ける）アプリではなく、**1回実行して終了**するシンプル設計です。

---

## 1. このツールでできること

- NHK RSSからニュースを取得
- 新着のみ / 全件 を切り替え
- 件数を指定して本文を作成
- SMTP（メール送信サーバー）でメール送信
- `--print-only` で送信せず本文プレビュー
- 状態ファイル（`.news_state.json`）で既読URL管理

---

## 2. 以前のCLI版との違い

以前: ターミナル表示中心（RSS取得→表示）  
現在: メール送信中心（RSS取得→本文整形→送信）

変更点:
- デフォルトモードを `new_only`（新着のみ）に変更
- `--print-only` を追加
- `--skip-empty-mail` を追加
- SMTP設定を`.env`で管理

---

## 3. 動作イメージ

### 通常実行（デフォルト）

```bash
python main.py
```

- 新着記事を抽出
- メール本文を生成
- 送信先へメール送信
- 送信成功後に状態ファイル更新

### プレビュー実行

```bash
python main.py --print-only
```

- メール送信しない
- 本文をターミナル表示
- 状態ファイル更新しない

---

## 4. 必要なもの

- Python 3.11以上
- インターネット接続
- SMTPを使えるメールアカウント（例: Gmail）

---

## 5. Python のバージョン確認方法

```bash
python --version
```

または

```bash
python3 --version
```

`Python 3.11.x` 以上ならOKです。

---

## 6. Python が入っていない場合の案内

- Windows: <https://www.python.org/downloads/windows/>
- macOS: <https://www.python.org/downloads/macos/> または Homebrew
- Linux: ディストリビューションのパッケージマネージャ

> Windowsではインストール時に「Add Python to PATH」をオンにすると便利です。

---

## 7. 仮想環境の作り方

### Windows

```powershell
python -m venv .venv
```

### macOS / Linux

```bash
python3 -m venv .venv
```

---

## 8. 仮想環境の有効化方法

### Windows

PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

コマンドプロンプト:

```bat
.venv\Scripts\activate.bat
```

### macOS / Linux

```bash
source .venv/bin/activate
```

---

## 9. ライブラリのインストール方法

```bash
pip install -r requirements.txt
```

---

## 10. `.env` の作り方

`.env.example` をコピーして `.env` を作成します。

### Windows

```powershell
Copy-Item .env.example .env
```

### macOS / Linux

```bash
cp .env.example .env
```

その後、`.env`を自分のメール設定に編集してください。

---

## 11. Gmail などで SMTP を使う際の設定例

`.env` 例:

```env
NHK_RSS_URL=https://www3.nhk.or.jp/rss/news/cat0.xml
NEWS_LIMIT=5
STATE_FILE=.news_state.json

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_USE_TLS=true

EMAIL_FROM=your_email@gmail.com
EMAIL_TO=destination@example.com
EMAIL_SUBJECT=毎朝のNHKニュース
EMAIL_TIMEOUT=30
```

---

## 12. Gmail のアプリパスワードについて（初心者向け）

Gmailでは通常のログインパスワードをSMTPに直接使えない場合があります。  
そのときはGoogleアカウントで**2段階認証**を有効にし、**アプリパスワード**（16文字）を発行して、`SMTP_PASSWORD` に設定します。

- 普段のログインパスワードをコードに書かない
- `.env` にだけ保存する
- `.env` はGitHubに公開しない

---

## 13. 初回動作確認の方法

### 1) まず `--print-only` で確認

```bash
python main.py --print-only
```

確認ポイント:
- RSSが取得できるか
- 本文が見やすいか
- 件数やモードが想定どおりか

### 2) 次に実送信で確認

```bash
python main.py
```

成功すると送信先にメールが届きます。

---

## 14. よく使うコマンド一覧

```bash
# デフォルト: 新着のみをメール送信
python main.py

# 既読を含む最新N件を送信
python main.py --all

# 前回以降の新着のみを送信
python main.py --new-only

# 件数変更
python main.py --limit 10

# 送信せず本文表示
python main.py --print-only

# 新着0件なら送信しない
python main.py --skip-empty-mail

# ヘルプ
python main.py --help
```

---

## 15. 毎朝自動送信する方法

## Windows タスクスケジューラ

1. タスクスケジューラを開く
2. 基本タスクを作成
3. トリガー: 毎日（例: 07:00）
4. 操作: プログラムの開始
5. 設定例
   - プログラム: `C:\path\to\project\.venv\Scripts\python.exe`
   - 引数: `main.py`
   - 開始(作業フォルダ): `C:\path\to\project`

## macOS / Linux cron

```bash
crontab -e
```

例（毎朝7:00）:

```cron
0 7 * * * cd /path/to/project && /path/to/project/.venv/bin/python main.py >> nhk_mail.log 2>&1
```

---

## 16. トラブルシューティング

### メールが送れない
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USE_TLS` を確認
- 会社ネットワークでSMTPが制限されていないか確認

### 認証に失敗する
- `SMTP_USERNAME` が正しいか
- Gmailはアプリパスワードを使っているか

### SMTP_HOST / PORT がわからない
- 利用メールサービスの公式ドキュメントを確認
- 例: Gmail は `smtp.gmail.com:587(TLS)`

### RSS が取得できない
- `NHK_RSS_URL` を確認
- 代替URL: `https://www.nhk.or.jp/rss/news/cat0.xml`

### 文字化けする
- 端末の文字コードをUTF-8にする
- メーラー側のエンコード設定を確認

### Python が見つからない
- `python --version` が失敗する場合、PATH設定を確認
- `python3` コマンドも試す

### モジュールが見つからない
- 仮想環境が有効化されているか
- `pip install -r requirements.txt` を再実行

### 前回状態ファイルの削除方法

```bash
rm -f .news_state.json
```

Windows PowerShell:

```powershell
Remove-Item .news_state.json -ErrorAction SilentlyContinue
```

---

## 17. プロジェクト構成

```text
mizuide-max/
├─ main.py           # CLI入口。設定読み込み、分岐、実行フロー
├─ news_fetcher.py   # RSS取得・正規化・状態ファイル読み書き
├─ mailer.py         # 本文生成・件名生成・SMTP送信
├─ .env.example      # 環境変数テンプレート
├─ requirements.txt  # 依存ライブラリ
├─ .gitignore
└─ README.md
```

---

## 18. セキュリティ上の注意

- `.env` をGitHubに上げない（`.gitignore` 済み）
- パスワードをコードに直書きしない
- アプリパスワードは漏れたら再発行する

---

## 19. 新着なし時の仕様（重要）

このツールのデフォルトは **案A** です。

- 新着0件でも「新着なし」メールを送信
- 件名は `毎朝のNHKニュース（新着なし）`

`--skip-empty-mail` を指定した場合のみ、0件時は送信しません。

---

## 20. 状態ファイル更新ポリシー（重要）

- **実送信成功時のみ** `.news_state.json` を更新します。
- `--print-only` は確認用途のため、状態ファイルを更新しません。
- `--skip-empty-mail` で送信スキップ時も、状態ファイルを更新しません。

これにより、送信失敗時に「未送信なのに既読化される」問題を防ぎます。

---

## 21. 今後の改善案

- HTMLメール（見出しやリンクをより見やすく）
- 複数宛先対応（カンマ区切り）
- カテゴリ別RSSの複数配信
- 失敗時の再試行回数設定
- ログファイルのローテーション

