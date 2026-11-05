import sqlite3

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from deteksi import cari_kejadian

DB_FILE = "netmon.db"
HOST_DIABAIKAN = ["192.168.1.1", "192.168.140.77"]  # sisa alamat tebakan yang salah

app = FastAPI(title="NetMon API")

# Mengizinkan dashboard React (nanti) mengambil data dari API ini
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def ambil_data(sql, params=()):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    try:
        baris = conn.execute(sql, params).fetchall()
    finally:
        conn.close()
    return [dict(b) for b in baris]


def tanda_tanya():
    # Menghasilkan "?, ?" sesuai jumlah host yang diabaikan
    return ", ".join("?" for _ in HOST_DIABAIKAN)


@app.get("/")
def beranda():
    return {"pesan": "NetMon API berjalan"}


@app.get("/latest")
def data_terbaru():
    sql = f"""
        SELECT p.waktu, p.host, p.latency_ms, p.sukses
        FROM ping_log p
        JOIN (
            SELECT host, MAX(id) AS id_terakhir
            FROM ping_log
            WHERE host NOT IN ({tanda_tanya()})
            GROUP BY host
        ) m ON p.id = m.id_terakhir
    """
    return ambil_data(sql, HOST_DIABAIKAN)


@app.get("/history")
def riwayat(host: str, limit: int = Query(100, ge=1, le=2000)):
    sql = """
        SELECT waktu, latency_ms, sukses
        FROM ping_log
        WHERE host = ?
        ORDER BY id DESC
        LIMIT ?
    """
    data = ambil_data(sql, (host, limit))
    return list(reversed(data))  # urut dari lama ke baru, enak untuk grafik


@app.get("/stats")
def statistik():
    sql = f"""
        SELECT
            host,
            COUNT(*) AS total_ping,
            ROUND(AVG(latency_ms), 1) AS rata_rata_ms,
            MIN(latency_ms) AS min_ms,
            MAX(latency_ms) AS max_ms,
            ROUND(100.0 * SUM(1 - sukses) / COUNT(*), 2) AS gagal_persen
        FROM ping_log
        WHERE host NOT IN ({tanda_tanya()})
        GROUP BY host
    """
    return ambil_data(sql, HOST_DIABAIKAN)

@app.get("/events")
def kejadian(limit: int = Query(20, ge=1, le=200)):
    return list(reversed(cari_kejadian()))[:limit]  # terbaru dulu