from __future__ import annotations

import smtplib
from dataclasses import dataclass
from datetime import datetime
from email.mime.text import MIMEText

from news_fetcher import NewsItem


class MailError(Exception):
    """メール送信まわりの例外。"""


@dataclass
class SMTPConfig:
    host: str
    port: int
    username: str
    password: str
    use_tls: bool
    timeout: int


@dataclass
class EmailConfig:
    from_addr: str
    to_addr: str
    subject_base: str


def build_subject(subject_base: str, count: int) -> str:
    if count > 0:
        return f"{subject_base}（{count}件）"
    return f"{subject_base}（新着なし）"


def build_news_body(
    entries: list[NewsItem],
    rss_url: str,
    mode: str,
    sent_at: datetime,
) -> str:
    mode_label = "新着のみ" if mode == "new_only" else "全件"
    lines = [
        "毎朝のNHKニュース",
        "",
        f"送信日時: {sent_at.strftime('%Y-%m-%d %H:%M:%S')}",
        f"RSS取得先: {rss_url}",
        f"対象モード: {mode_label}",
        f"対象件数: {len(entries)}件",
        "",
    ]

    if not entries:
        lines.append("新着はありませんでした。")
        return "\n".join(lines)

    for index, item in enumerate(entries, start=1):
        lines.extend(
            [
                "-" * 50,
                f"[{index}] {item.title}",
                f"公開日時: {item.published}",
                f"URL: {item.link}",
                "",
            ]
        )

    return "\n".join(lines)


def print_body_preview(body: str) -> None:
    print("=" * 70)
    print("メール本文プレビュー")
    print("=" * 70)
    print(body)


def send_mail(smtp: SMTPConfig, email_cfg: EmailConfig, subject: str, body: str) -> None:
    if not email_cfg.to_addr.strip():
        raise MailError("メール送信先(EMAIL_TO)が未設定です。.envを確認してください。")

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = email_cfg.from_addr
    msg["To"] = email_cfg.to_addr

    try:
        with smtplib.SMTP(smtp.host, smtp.port, timeout=smtp.timeout) as server:
            if smtp.use_tls:
                server.starttls()
            server.login(smtp.username, smtp.password)
            server.send_message(msg)
    except smtplib.SMTPAuthenticationError as exc:
        raise MailError(
            "SMTP認証に失敗しました。ユーザー名・パスワード（またはアプリパスワード）を確認してください。"
        ) from exc
    except smtplib.SMTPConnectError as exc:
        raise MailError(
            "SMTPサーバーへ接続できませんでした。SMTP_HOST / SMTP_PORT を確認してください。"
        ) from exc
    except smtplib.SMTPException as exc:
        raise MailError(
            "メール送信に失敗しました。SMTP設定とネットワーク接続を確認してください。"
        ) from exc
