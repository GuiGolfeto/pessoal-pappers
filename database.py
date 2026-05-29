import os
from urllib.parse import urlparse, urlencode, urlunparse, parse_qs
import psycopg2
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    raw_url = os.getenv("DATABASE_URL", "")
    parsed = urlparse(raw_url)
    params = {k: v[0] for k, v in parse_qs(parsed.query).items()}
    params.pop("channel_binding", None)
    clean_url = urlunparse(parsed._replace(query=urlencode(params)))
    return psycopg2.connect(clean_url)


def setup_tables():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS sent_papers (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    url TEXT UNIQUE NOT NULL,
                    source TEXT NOT NULL,
                    sent_date DATE NOT NULL DEFAULT CURRENT_DATE
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS daily_log (
                    date DATE PRIMARY KEY,
                    sent_at TIMESTAMP NOT NULL DEFAULT NOW()
                )
            """)
        conn.commit()


def already_sent_today():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM daily_log WHERE date = CURRENT_DATE")
            return cur.fetchone() is not None


def is_paper_sent(url):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM sent_papers WHERE url = %s", (url,))
            return cur.fetchone() is not None


def save_papers(papers):
    with get_connection() as conn:
        with conn.cursor() as cur:
            for p in papers:
                cur.execute("""
                    INSERT INTO sent_papers (title, url, source)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (url) DO NOTHING
                """, (p["title"], p["url"], p["source"]))
        conn.commit()


def log_today():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO daily_log (date) VALUES (CURRENT_DATE)
                ON CONFLICT (date) DO NOTHING
            """)
        conn.commit()
