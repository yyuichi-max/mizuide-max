from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import feedparser
from dotenv import load_dotenv

DEFAULT_RSS_URL = "https://www3.nhk.or.jp/rss/news/cat0.xml"
ALT_RSS_URL = "https://www.nhk.or.jp/rss/news/cat0.xml"
DEFAULT_LIMIT = 5
DEFAULT_STATE_FILE = ".news_state.json"


def parse_args() -> argparse.Namespace:
    """CLI引数を定義して解析する。"""
    parser = argparse.ArgumentParser(
        description="NHK RSSから最新ニュースを取得して表示するツール",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="最新N件をすべて表示します（既読も含む）",
    )
    parser.add_argument(
        "--new-only",
        action="store_true",
        help="前回実行以降の新着だけ表示します",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="表示件数を指定します（例: --limit 10）",
    )
    return parser.parse_args()


def load_settings(args: argparse.Namespace) -> dict[str, Any]:
    """環境変数と引数から設定値を組み立てる。"""
    load_dotenv()

    rss_url = os.getenv("NHK_RSS_URL", DEFAULT_RSS_URL).strip() or DEFAULT_RSS_URL

    env_limit = os.getenv("NEWS_LIMIT", str(DEFAULT_LIMIT)).strip()
    limit = args.limit if args.limit is not None else safe_int(env_limit, DEFAULT_LIMIT)
    if limit <= 0:
        print("[警告] 件数は1以上を指定してください。デフォルト5件で実行します。")
        limit = DEFAULT_LIMIT

    state_file = os.getenv("STATE_FILE", DEFAULT_STATE_FILE).strip() or DEFAULT_STATE_FILE

    mode = "new_only" if args.new_only else "all"
    if args.all:
        mode = "all"

    return {
        "rss_url": rss_url,
        "limit": limit,
        "state_file": Path(state_file),
        "mode": mode,
    }


def safe_int(value: str, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def fetch_feed(rss_url: str) -> feedparser.FeedParserDict:
    """RSSフィードを取得してパースする。"""
    return feedparser.parse(rss_url)


def normalize_entry(entry: feedparser.FeedParserDict) -> dict[str, str]:
    """表示に必要な情報を取り出して整形する。"""
    title = str(entry.get("title", "(タイトルなし)")).strip() or "(タイトルなし)"
    link = str(entry.get("link", "(URLなし)")).strip() or "(URLなし)"

    published = "(日時情報なし)"
    if entry.get("published"):
        published = str(entry.get("published")).strip()
    elif entry.get("updated"):
        published = str(entry.get("updated")).strip()

    return {
        "title": title,
        "link": link,
        "published": published,
    }


def load_seen_links(state_file: Path) -> set[str]:
    """前回までに表示したURLを読み込む。"""
    if not state_file.exists():
        return set()

    try:
        data = json.loads(state_file.read_text(encoding="utf-8"))
        seen_links = data.get("seen_links", [])
        if isinstance(seen_links, list):
            return {str(link) for link in seen_links}
    except (json.JSONDecodeError, OSError):
        print("[警告] 状態ファイルを読めませんでした。新規状態として扱います。")

    return set()


def save_seen_links(state_file: Path, seen_links: set[str]) -> None:
    """表示済みURLを保存する。"""
    payload = {
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "seen_links": sorted(seen_links),
    }

    try:
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except OSError as exc:
        print(f"[警告] 状態ファイルの保存に失敗しました: {exc}")


def filter_entries(
    entries: list[dict[str, str]],
    seen_links: set[str],
    limit: int,
    mode: str,
) -> list[dict[str, str]]:
    """表示対象をモードに応じて絞り込む。"""
    if mode == "all":
        return entries[:limit]

    new_entries = [item for item in entries if item["link"] not in seen_links]
    return new_entries[:limit]


def print_entries(entries: list[dict[str, str]], mode: str) -> None:
    """ニュース一覧を見やすく表示する。"""
    if not entries:
        if mode == "new_only":
            print("新着ニュースはありませんでした。")
        else:
            print("表示できるニュースがありませんでした。")
        return

    print("=" * 70)
    print(f"NHKニュース ({len(entries)}件)")
    print("=" * 70)
    for index, item in enumerate(entries, start=1):
        print(f"[{index}] {item['title']}")
        print(f"    公開日時: {item['published']}")
        print(f"    URL    : {item['link']}")
        print("-" * 70)


def validate_feed(feed: feedparser.FeedParserDict, rss_url: str) -> bool:
    """フィード取得結果の妥当性を確認し、エラーを案内する。"""
    if getattr(feed, "bozo", False):
        error = getattr(feed, "bozo_exception", None)
        print("[エラー] RSSの解析に失敗しました。URLが正しいか確認してください。")
        if error:
            print(f"詳細: {error}")
        print("代替URL例: https://www.nhk.or.jp/rss/news/cat0.xml")
        return False

    status = getattr(feed, "status", None)
    if status and int(status) >= 400:
        print(f"[エラー] RSSの取得に失敗しました (HTTP {status})")
        print(f"URL: {rss_url}")
        print("代替URL例: https://www.nhk.or.jp/rss/news/cat0.xml")
        return False

    if not getattr(feed, "entries", None):
        print("[エラー] RSSは取得できましたが記事が見つかりませんでした。")
        print(f"URL: {rss_url}")
        return False

    return True


def main() -> int:
    args = parse_args()
    settings = load_settings(args)

    rss_url = settings["rss_url"]
    limit = settings["limit"]
    state_file = settings["state_file"]
    mode = settings["mode"]

    print(f"RSS取得先: {rss_url}")
    print(f"表示モード: {'新着のみ' if mode == 'new_only' else '全件'}")
    print(f"表示件数  : {limit}")

    try:
        feed = fetch_feed(rss_url)
    except Exception as exc:
        print("[エラー] ネットワークまたはRSS取得処理で問題が発生しました。")
        print(f"詳細: {exc}")
        print("インターネット接続やRSS URLを確認してください。")
        print(f"代替URL候補: {ALT_RSS_URL}")
        return 1

    if not validate_feed(feed, rss_url):
        return 1

    normalized_entries = [normalize_entry(entry) for entry in feed.entries]
    seen_links = load_seen_links(state_file)
    target_entries = filter_entries(normalized_entries, seen_links, limit, mode)

    print_entries(target_entries, mode)

    # 取得した記事は既読として保存（次回のnew-only判定で利用）
    current_links = {item["link"] for item in normalized_entries if item["link"] != "(URLなし)"}
    merged_links = seen_links | current_links
    save_seen_links(state_file, merged_links)

    return 0


if __name__ == "__main__":
    sys.exit(main())
