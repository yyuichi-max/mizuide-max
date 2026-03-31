from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import feedparser


@dataclass
class NewsItem:
    title: str
    link: str
    published: str


class NewsError(Exception):
    """ニュース取得まわりの例外。"""


def fetch_feed(rss_url: str) -> feedparser.FeedParserDict:
    try:
        return feedparser.parse(rss_url)
    except Exception as exc:  # feedparser側の想定外エラーの保険
        raise NewsError(
            "RSSの取得処理でエラーが発生しました。ネットワーク接続とURLを確認してください。"
        ) from exc


def validate_feed(feed: feedparser.FeedParserDict, rss_url: str) -> None:
    if getattr(feed, "bozo", False):
        error = getattr(feed, "bozo_exception", None)
        detail = f" 詳細: {error}" if error else ""
        raise NewsError(
            "RSSの解析に失敗しました。URLの誤りや一時的な配信障害の可能性があります。"
            f"\n確認先: NHK_RSS_URL={rss_url}{detail}"
        )

    status = getattr(feed, "status", None)
    if status and int(status) >= 400:
        raise NewsError(
            f"RSSの取得に失敗しました (HTTP {status})。\n"
            f"確認先: NHK_RSS_URL={rss_url}"
        )

    if not getattr(feed, "entries", None):
        raise NewsError(
            f"RSSは取得できましたが記事が見つかりませんでした。\n確認先: NHK_RSS_URL={rss_url}"
        )


def normalize_entry(entry: feedparser.FeedParserDict) -> NewsItem:
    title = str(entry.get("title", "(タイトルなし)")).strip() or "(タイトルなし)"
    link = str(entry.get("link", "")).strip() or "(URLなし)"

    published = "(日時情報なし)"
    if entry.get("published"):
        published = str(entry.get("published")).strip()
    elif entry.get("updated"):
        published = str(entry.get("updated")).strip()

    return NewsItem(title=title, link=link, published=published)


def load_seen_links(state_file: Path) -> set[str]:
    if not state_file.exists():
        return set()

    try:
        data = json.loads(state_file.read_text(encoding="utf-8"))
        seen_links = data.get("seen_links", [])
        if isinstance(seen_links, list):
            return {str(link) for link in seen_links}
    except (json.JSONDecodeError, OSError) as exc:
        raise NewsError(
            "STATE_FILEの読み込みに失敗しました。ファイル権限とJSON形式を確認してください。"
        ) from exc

    return set()


def save_seen_links(state_file: Path, seen_links: set[str]) -> None:
    payload: dict[str, Any] = {
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
        raise NewsError(
            f"STATE_FILEの保存に失敗しました。保存先パスを確認してください: {state_file}"
        ) from exc


def select_entries(
    all_entries: list[NewsItem],
    seen_links: set[str],
    limit: int,
    mode: str,
) -> list[NewsItem]:
    if mode == "all":
        return all_entries[:limit]

    new_entries = [item for item in all_entries if item.link not in seen_links]
    return new_entries[:limit]
