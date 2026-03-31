from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from mailer import EmailConfig, MailError, SMTPConfig, build_news_body, build_subject, print_body_preview, send_mail
from news_fetcher import NewsError, NewsItem, fetch_feed, load_seen_links, normalize_entry, save_seen_links, select_entries, validate_feed

DEFAULT_RSS_URL = "https://www3.nhk.or.jp/rss/news/cat0.xml"
DEFAULT_LIMIT = 5
DEFAULT_STATE_FILE = ".news_state.json"
DEFAULT_SUBJECT = "毎朝のNHKニュース"
DEFAULT_EMAIL_TIMEOUT = 30


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="NHK RSSからニュースを取得し、毎朝メール送信するツール",
    )
    parser.add_argument("--all", action="store_true", help="既読を含む最新N件を対象にします")
    parser.add_argument("--new-only", action="store_true", help="前回以降の新着のみを対象にします")
    parser.add_argument("--limit", type=int, help="対象件数を指定します（例: --limit 10）")
    parser.add_argument("--print-only", action="store_true", help="メール送信せず本文をターミナル表示します")
    parser.add_argument("--skip-empty-mail", action="store_true", help="新着0件のときはメール送信をスキップします")
    return parser.parse_args()


def safe_int(value: str, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"必須設定 {name} が未設定です。.env を確認してください。")
    return value


def load_settings(args: argparse.Namespace) -> tuple[dict[str, object], SMTPConfig, EmailConfig]:
    load_dotenv()

    rss_url = os.getenv("NHK_RSS_URL", DEFAULT_RSS_URL).strip() or DEFAULT_RSS_URL
    env_limit = os.getenv("NEWS_LIMIT", str(DEFAULT_LIMIT)).strip()
    limit = args.limit if args.limit is not None else safe_int(env_limit, DEFAULT_LIMIT)
    if limit <= 0:
        raise ValueError("件数が不正です。--limit または NEWS_LIMIT に1以上を指定してください。")

    state_file = Path(os.getenv("STATE_FILE", DEFAULT_STATE_FILE).strip() or DEFAULT_STATE_FILE)

    mode = "new_only"
    if args.all:
        mode = "all"
    elif args.new_only:
        mode = "new_only"

    smtp_port = safe_int(require_env("SMTP_PORT"), 0)
    if smtp_port <= 0:
        raise ValueError("SMTP_PORT が不正です。数値（例: 587）を設定してください。")

    smtp_cfg = SMTPConfig(
        host=require_env("SMTP_HOST"),
        port=smtp_port,
        username=require_env("SMTP_USERNAME"),
        password=require_env("SMTP_PASSWORD"),
        use_tls=os.getenv("SMTP_USE_TLS", "true").strip().lower() in {"1", "true", "yes", "on"},
        timeout=safe_int(os.getenv("EMAIL_TIMEOUT", str(DEFAULT_EMAIL_TIMEOUT)), DEFAULT_EMAIL_TIMEOUT),
    )

    email_cfg = EmailConfig(
        from_addr=require_env("EMAIL_FROM"),
        to_addr=require_env("EMAIL_TO"),
        subject_base=os.getenv("EMAIL_SUBJECT", DEFAULT_SUBJECT).strip() or DEFAULT_SUBJECT,
    )

    app_settings: dict[str, object] = {
        "rss_url": rss_url,
        "limit": limit,
        "state_file": state_file,
        "mode": mode,
        "print_only": args.print_only,
        "skip_empty_mail": args.skip_empty_mail,
    }
    return app_settings, smtp_cfg, email_cfg


def main() -> int:
    args = parse_args()

    try:
        settings, smtp_cfg, email_cfg = load_settings(args)
    except ValueError as exc:
        print(f"[エラー] {exc}")
        return 1

    rss_url = str(settings["rss_url"])
    limit = int(settings["limit"])
    state_file = Path(settings["state_file"])
    mode = str(settings["mode"])
    print_only = bool(settings["print_only"])
    skip_empty_mail = bool(settings["skip_empty_mail"])

    print(f"RSS取得先: {rss_url}")
    print(f"対象モード: {'新着のみ' if mode == 'new_only' else '全件'}")
    print(f"対象件数  : {limit}")
    print(f"実行種別  : {'表示のみ(--print-only)' if print_only else 'メール送信'}")

    try:
        feed = fetch_feed(rss_url)
        validate_feed(feed, rss_url)
        all_entries: list[NewsItem] = [normalize_entry(entry) for entry in feed.entries]
        seen_links = load_seen_links(state_file)
        target_entries = select_entries(all_entries, seen_links, limit, mode)
    except NewsError as exc:
        print(f"[エラー] {exc}")
        return 1

    sent_at = datetime.now()
    body = build_news_body(target_entries, rss_url=rss_url, mode=mode, sent_at=sent_at)
    subject = build_subject(email_cfg.subject_base, len(target_entries))

    if print_only:
        print_body_preview(body)
        print("\n[情報] --print-only のため、メール送信と状態ファイル更新は行いません。")
        return 0

    if skip_empty_mail and len(target_entries) == 0:
        print("[情報] --skip-empty-mail が指定されているため、新着0件ではメール送信をスキップしました。")
        print("[情報] 状態ファイルも更新しません。")
        return 0

    try:
        send_mail(smtp_cfg, email_cfg, subject=subject, body=body)
        print(f"[完了] メールを送信しました: {email_cfg.to_addr}")

        # 実送信に成功したときだけ、取得記事を既読として保存する
        current_links = {item.link for item in all_entries if item.link != "(URLなし)"}
        merged_links = seen_links | current_links
        save_seen_links(state_file, merged_links)
        print(f"[完了] 状態ファイルを更新しました: {state_file}")
    except (MailError, NewsError) as exc:
        print(f"[エラー] {exc}")
        print("[案内] 送信に失敗したため、状態ファイルは更新していません。")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
