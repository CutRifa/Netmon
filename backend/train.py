import sqlite3

import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest

DB_FILE = "netmon.db"
HOST_DIABAIKAN = ["192.168.1.1", "192.168.140.77"]  # alamat tebakan yang salah
JEDA_SESI_DETIK = 60              # jeda lebih dari ini dianggap sesi baru
JENDELA = 6                       # 6 data terakhir (sekitar 1 menit)
FITUR = ["latency_ms", "rata_geser", "std_geser", "selisih"]


def muat_data():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query(
        "SELECT waktu, host, latency_ms, sukses FROM ping_log", conn
    )
    conn.close()
    df["waktu"] = pd.to_datetime(df["waktu"])
    df = df[~df["host"].isin(HOST_DIABAIKAN)]
    return df.sort_values(["host", "waktu"]).reset_index(drop=True)


def buat_fitur(d):
    d = d.copy()
    # Pisahkan sesi: jeda panjang berarti laptop mati atau collector berhenti
    d["sesi"] = (d["waktu"].diff().dt.total_seconds() > JEDA_SESI_DETIK).cumsum()
    g = d.groupby("sesi")["latency_ms"]
    d["rata_geser"] = g.transform(lambda s: s.rolling(JENDELA, min_periods=1).mean())
    d["std_geser"] = g.transform(
        lambda s: s.rolling(JENDELA, min_periods=2).std()
    ).fillna(0)
    d["selisih"] = d["latency_ms"] - d["rata_geser"]
    return d


def main():
    df = muat_data()
    print(f"Total data: {len(df)} baris\n")

    for host, d in df.groupby("host"):
        d = buat_fitur(d)
        gagal = int((d["sukses"] == 0).sum())
        ok = d.dropna(subset=["latency_ms"]).copy()

        model = IsolationForest(
            n_estimators=200, contamination=0.01, random_state=42
        )
        model.fit(ok[FITUR])
        ok["anomali"] = model.predict(ok[FITUR]) == -1
        ok["skor"] = model.decision_function(ok[FITUR])

        joblib.dump(model, f"model_{host}.joblib")

        print(f"=== {host} ===")
        print(f"Data: {len(ok)} | Ping gagal: {gagal} | Ditandai anomali: {int(ok['anomali'].sum())}")
        print("Latency normal  : rata-rata", round(ok["latency_ms"].mean(), 1), "ms")
        print("10 yang paling tidak biasa:")
        print(
            ok.nsmallest(10, "skor")[["waktu", "latency_ms", "skor"]]
            .to_string(index=False)
        )
        print()


if __name__ == "__main__":
    main()