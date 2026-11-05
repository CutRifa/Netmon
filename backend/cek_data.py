import sqlite3

import pandas as pd

conn = sqlite3.connect("netmon.db")
df = pd.read_sql_query("SELECT waktu, host, latency_ms, sukses FROM ping_log", conn)
conn.close()
df["waktu"] = pd.to_datetime(df["waktu"])

# 1) Sesi pengumpulan data: jeda lebih dari 60 detik = sesi baru
w = df["waktu"].drop_duplicates().sort_values().reset_index(drop=True)
sesi = (w.diff().dt.total_seconds() > 60).cumsum()
print("=== Sesi pengumpulan data ===")
for _, grup in w.groupby(sesi):
    print(grup.iloc[0], "->", grup.iloc[-1], f"({len(grup)} putaran)")

# 2) Kapan ping gagal, per jam
gagal = df[(df["sukses"] == 0) & (df["host"].isin(["google.com", "1.1.1.1"]))]
print("\n=== Ping gagal per jam (google.com + 1.1.1.1) ===")
print(gagal.groupby(gagal["waktu"].dt.floor("60min")).size())