import json
import os
import time

import requests
from dotenv import load_dotenv

from deteksi import cari_kejadian

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
FILE_TERKIRIM = "terkirim.json"
CEK_SETIAP_DETIK = 60


def muat_terkirim():
    try:
        with open(FILE_TERKIRIM) as f:
            return set(json.load(f))
    except FileNotFoundError:
        return set()


def simpan_terkirim(data):
    with open(FILE_TERKIRIM, "w") as f:
        json.dump(sorted(data), f)


def kirim(teks):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    r = requests.post(url, data={"chat_id": CHAT_ID, "text": teks}, timeout=10)
    r.raise_for_status()


def susun_pesan(k):
    jenis = "Koneksi putus" if "gagal" in k["jenis"] else "Lonjakan latency"
    baris = [
        f"NetMon: {jenis}",
        f"Waktu: {k['mulai'].replace('T', ' ')} sampai {k['selesai'].replace('T', ' ')}",
        f"Alamat: {', '.join(k['host'])}",
    ]
    if k["latency_maks_ms"] is not None:
        baris.append(f"Latency maks: {k['latency_maks_ms']:.0f} ms")
    return "\n".join(baris)


def main():
    if not TOKEN or not CHAT_ID:
        raise SystemExit("Isi TELEGRAM_TOKEN dan TELEGRAM_CHAT_ID di file .env")
    terkirim = muat_terkirim()
    print("Pemantau alert berjalan. Tekan Ctrl+C untuk berhenti.")
    while True:
        try:
            for k in cari_kejadian():
                if k["keyakinan"] != "tinggi" or k["mulai"] in terkirim:
                    continue
                kirim(susun_pesan(k))
                terkirim.add(k["mulai"])
                simpan_terkirim(terkirim)
                print("Terkirim:", k["mulai"])
        except Exception as e:
            # Hanya cetak jenis errornya: pesan lengkap requests bisa memuat token
            print("Gagal, dicoba lagi nanti:", type(e).__name__)
        time.sleep(CEK_SETIAP_DETIK)


if __name__ == "__main__":
    main()