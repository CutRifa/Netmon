import platform
import re
import sqlite3
import subprocess
import time
from datetime import datetime

# Alamat yang mau dipantau. Ganti IP router sesuai jaringanmu.
TARGETS = ["google.com", "1.1.1.1", "192.168.149.128"]
INTERVAL_DETIK = 10
DB_FILE = "netmon.db"


def siapkan_db():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ping_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            waktu TEXT NOT NULL,
            host TEXT NOT NULL,
            latency_ms REAL,
            sukses INTEGER NOT NULL
        )
    """)
    conn.commit()
    return conn


def ping(host):
    param = "-n" if platform.system() == "Windows" else "-c"
    try:
        hasil = subprocess.run(
            ["ping", param, "1", host],
            capture_output=True, text=True, timeout=5
        )
    except subprocess.TimeoutExpired:
        return None
    cocok = re.search(r"(?:time|waktu)\s*[=<]\s*([\d.]+)", hasil.stdout, re.IGNORECASE)
    return float(cocok.group(1)) if cocok else None


def main():
    conn = siapkan_db()
    print("Mulai memantau. Tekan Ctrl+C untuk berhenti.")
    while True:
        waktu = datetime.now().isoformat(timespec="seconds")
        for host in TARGETS:
            latency = ping(host)
            sukses = 1 if latency is not None else 0
            conn.execute(
                "INSERT INTO ping_log (waktu, host, latency_ms, sukses) VALUES (?, ?, ?, ?)",
                (waktu, host, latency, sukses),
            )
            print(f"{waktu} | {host} | {latency} ms")
        conn.commit()
        time.sleep(INTERVAL_DETIK)


if __name__ == "__main__":
    main()