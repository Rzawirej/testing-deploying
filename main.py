

from fastapi import FastAPI, HTTPException
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import sqlite3
import uvicorn

from helpers import calculate_returned_value

app = FastAPI()
DB_FILE = "data.db"


# --- Database setup ---
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS html_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT UNIQUE,
            html_content TEXT
        )
    """)
    conn.commit()
    conn.close()

# --- Generate HTML (your daily logic here) ---
def generate_html() -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"<html><body><h1>Report for {now}</h1><p>Generated automatically.</p></body></html>"

# --- Save result & cleanup ---
def store_html():
    today = datetime.now().strftime("%Y-%m-%d")
    html_content = generate_html()

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO html_data (date, html_content) VALUES (?, ?)",
              (today, html_content))

    # Keep only last 7 days
    cutoff = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    c.execute("DELETE FROM html_data WHERE date < ?", (cutoff,))
    conn.commit()
    conn.close()

# --- Scheduler ---
scheduler = BackgroundScheduler()
scheduler.add_job(store_html, "interval", days=1)
scheduler.start()

# --- API Endpoints ---
@app.get("/html/{date}")
def get_html(date: str):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT html_content FROM html_data WHERE date = ?", (date,))
    row = c.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="No data for given date")
    return {"date": date, "html": row[0]}

@app.get("/html/latest")
def get_latest():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT date, html_content FROM html_data ORDER BY date DESC LIMIT 1")
    row = c.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="No data available")
    return {"date": row[0], "html": row[1]}

@app.get("/test")
def test():
    return calculate_returned_value()

# --- Run ---
if __name__ == "__main__":
    init_db()
    store_html()  # generate once at startup
    uvicorn.run(app, host="0.0.0.0", port=8000)