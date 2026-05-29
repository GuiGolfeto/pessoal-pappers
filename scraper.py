import os
import sys
import subprocess
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

import feedparser
import requests
from deep_translator import GoogleTranslator
from dotenv import load_dotenv

from database import setup_tables, already_sent_today, is_paper_sent, save_papers, log_today

load_dotenv()

ARXIV_AI_RSS = "https://rss.arxiv.org/rss/cs.AI"
ARXIV_LG_RSS = "https://rss.arxiv.org/rss/cs.LG"
HUGGINGFACE_API = "https://huggingface.co/api/daily_papers"

SOURCE_META = {
    "arxiv_ai": {
        "label": "arXiv — cs.AI",
        "color": "#b45309",
        "bg": "#fffbeb",
        "border": "#fcd34d",
        "badge_bg": "#fef3c7",
        "badge_color": "#92400e",
    },
    "arxiv_lg": {
        "label": "arXiv — cs.LG",
        "color": "#065f46",
        "bg": "#f0fdf4",
        "border": "#6ee7b7",
        "badge_bg": "#d1fae5",
        "badge_color": "#065f46",
    },
    "huggingface": {
        "label": "HuggingFace Daily Papers",
        "color": "#1d4ed8",
        "bg": "#eff6ff",
        "border": "#93c5fd",
        "badge_bg": "#dbeafe",
        "badge_color": "#1e40af",
    },
}


def translate(text):
    if not text:
        return ""
    try:
        return GoogleTranslator(source="auto", target="pt").translate(text[:4500])
    except Exception:
        return text


def fetch_arxiv(feed_url, source_label, limit=3):
    feed = feedparser.parse(feed_url)
    papers = []
    for entry in feed.entries:
        if is_paper_sent(entry.link):
            continue
        raw_summary = (entry.get("summary") or "")[:500]
        papers.append({
            "title": translate(entry.title),
            "url": entry.link,
            "summary": translate(raw_summary),
            "source": source_label,
        })
        if len(papers) >= limit:
            break
    return papers


def fetch_huggingface(limit=3):
    try:
        resp = requests.get(HUGGINGFACE_API, timeout=10)
        resp.raise_for_status()
        papers = []
        for item in resp.json():
            paper = item.get("paper", {})
            arxiv_id = paper.get("id", "")
            url = f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else ""
            if not url or is_paper_sent(url):
                continue
            raw_summary = (item.get("summary") or paper.get("summary") or "")[:500]
            papers.append({
                "title": translate(item.get("title") or paper.get("title", "")),
                "url": url,
                "summary": translate(raw_summary),
                "source": "huggingface",
            })
            if len(papers) >= limit:
                break
        return papers
    except Exception:
        return []


def build_html(all_papers):
    grouped = {}
    for p in all_papers:
        grouped.setdefault(p["source"], []).append(p)

    sections = ""
    for source, papers in grouped.items():
        meta = SOURCE_META.get(source, {
            "label": source, "color": "#4f46e5", "bg": "#f8f8ff",
            "border": "#a5b4fc", "badge_bg": "#e0e7ff", "badge_color": "#3730a3",
        })

        cards = ""
        for i, p in enumerate(papers):
            cards += f"""
            <div style="
                background:{meta['bg']};
                border:1px solid {meta['border']};
                border-left:4px solid {meta['color']};
                border-radius:8px;
                padding:16px 18px;
                margin-bottom:12px;
            ">
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
                    <span style="
                        background:{meta['badge_bg']};
                        color:{meta['badge_color']};
                        font-size:11px;
                        font-weight:600;
                        padding:2px 8px;
                        border-radius:999px;
                        letter-spacing:0.4px;
                    ">#{i+1}</span>
                </div>
                <a href="{p['url']}" style="
                    font-size:15px;
                    font-weight:700;
                    color:#111827;
                    text-decoration:none;
                    line-height:1.4;
                ">{p['title']}</a>
                <p style="
                    color:#4b5563;
                    font-size:13px;
                    line-height:1.6;
                    margin:10px 0 12px;
                ">{p['summary']}</p>
                <a href="{p['url']}" style="
                    display:inline-block;
                    background:{meta['color']};
                    color:#ffffff;
                    font-size:12px;
                    font-weight:600;
                    padding:6px 14px;
                    border-radius:6px;
                    text-decoration:none;
                ">Ler paper →</a>
            </div>"""

        sections += f"""
        <div style="margin-bottom:36px;">
            <div style="
                display:flex;
                align-items:center;
                gap:10px;
                margin-bottom:14px;
                padding-bottom:10px;
                border-bottom:2px solid {meta['border']};
            ">
                <span style="
                    background:{meta['badge_bg']};
                    color:{meta['badge_color']};
                    font-size:12px;
                    font-weight:700;
                    padding:3px 10px;
                    border-radius:999px;
                ">{meta['label']}</span>
            </div>
            {cards}
        </div>"""

    today = datetime.now().strftime("%d de %B de %Y").lower()
    total = len(all_papers)

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/></head>
<body style="margin:0;padding:0;background:#f3f4f6;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
  <div style="max-width:640px;margin:32px auto;background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">

    <!-- header -->
    <div style="background:linear-gradient(135deg,#1e1b4b 0%,#3730a3 100%);padding:32px 32px 28px;">
      <div style="font-size:11px;font-weight:600;color:#a5b4fc;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:8px;">Pessoal Papers</div>
      <h1 style="margin:0;font-size:24px;font-weight:800;color:#ffffff;line-height:1.2;">Papers do Dia</h1>
      <p style="margin:6px 0 0;color:#c7d2fe;font-size:14px;">{today} &nbsp;·&nbsp; {total} papers selecionados</p>
    </div>

    <!-- body -->
    <div style="padding:28px 32px 8px;">
      {sections}
    </div>

    <!-- footer -->
    <div style="background:#f9fafb;border-top:1px solid #e5e7eb;padding:16px 32px;text-align:center;">
      <p style="margin:0;font-size:11px;color:#9ca3af;">Enviado automaticamente · pessoal-pappers</p>
    </div>

  </div>
</body>
</html>"""


def send_email(html_content, paper_count):
    from_email = os.getenv("EMAIL_FROM")
    password = os.getenv("EMAIL_PASSWORD")
    today = datetime.now().strftime("%d/%m/%Y")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Papers do Dia — {today} ({paper_count} papers)"
    msg["From"] = from_email
    msg["To"] = from_email
    msg.attach(MIMEText(html_content, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(from_email, password)
        server.sendmail(from_email, from_email, msg.as_string())


def notify(title, message):
    try:
        subprocess.run(
            ["notify-send", title, message, "--icon=emblem-mail", "--expire-time=8000"],
            check=False,
        )
    except FileNotFoundError:
        print(f"[notify] {title}: {message}")


def main():
    setup_tables()

    if already_sent_today():
        sys.exit(0)

    arxiv_ai = fetch_arxiv(ARXIV_AI_RSS, "arxiv_ai")
    arxiv_lg = fetch_arxiv(ARXIV_LG_RSS, "arxiv_lg")
    hf = fetch_huggingface()

    all_papers = arxiv_ai + arxiv_lg + hf

    if not all_papers:
        notify("Paper Daily", "Nenhum paper novo encontrado hoje.")
        sys.exit(0)

    html = build_html(all_papers)
    send_email(html, len(all_papers))

    save_papers(all_papers)
    log_today()

    notify("Paper Daily", f"{len(all_papers)} papers enviados para seu email!")


if __name__ == "__main__":
    main()
