import joblib
import pandas as pd

from train import FITUR, buat_fitur, muat_data

GAGAL_BERUNTUN = 3        # minimal ping gagal berturut-turut dianggap gangguan
JEDA_GABUNG_DETIK = 60    # kejadian yang berdekatan digabung jadi satu


def kejadian_mentah():
    df = muat_data()
    hasil = []

    for host, d in df.groupby("host"):
        d = buat_fitur(d)

        # Aturan 1: ping gagal beruntun
        d["blok"] = (
            (d["sukses"] != d["sukses"].shift()) | (d["sesi"] != d["sesi"].shift())
        ).cumsum()
        for _, b in d[d["sukses"] == 0].groupby("blok"):
            if len(b) >= GAGAL_BERUNTUN:
                hasil.append({
                    "mulai": b["waktu"].iloc[0], "selesai": b["waktu"].iloc[-1],
                    "host": host, "jenis": "gagal", "latency_ms": None,
                })

        # Aturan 2: lonjakan latency menurut model ML
        try:
            model = joblib.load(f"model_{host}.joblib")
        except FileNotFoundError:
            continue  # host ini belum punya model, cukup pakai aturan 1
        ok = d.dropna(subset=["latency_ms"]).copy()
        ok["anomali"] = model.predict(ok[FITUR]) == -1
        # selisih > 0: hanya latency yang lebih TINGGI dari rata-rata jendela
        lonjakan = ok[ok["anomali"] & (ok["selisih"] > 0)]
        for _, r in lonjakan.iterrows():
            hasil.append({
                "mulai": r["waktu"], "selesai": r["waktu"],
                "host": host, "jenis": "lonjakan", "latency_ms": float(r["latency_ms"]),
            })
    return hasil


def gabung(mentah):
    if not mentah:
        return []
    mentah = sorted(mentah, key=lambda k: k["mulai"])
    jeda = pd.Timedelta(seconds=JEDA_GABUNG_DETIK)

    kelompok = [[mentah[0]]]
    akhir = mentah[0]["selesai"]
    for k in mentah[1:]:
        if k["mulai"] <= akhir + jeda:
            kelompok[-1].append(k)
            akhir = max(akhir, k["selesai"])
        else:
            kelompok.append([k])
            akhir = k["selesai"]

    kejadian = []
    for grup in kelompok:
        host = sorted({k["host"] for k in grup})
        latensi = [k["latency_ms"] for k in grup if k["latency_ms"] is not None]
        kejadian.append({
            "mulai": min(k["mulai"] for k in grup).isoformat(timespec="seconds"),
            "selesai": max(k["selesai"] for k in grup).isoformat(timespec="seconds"),
            "host": host,
            "jenis": sorted({k["jenis"] for k in grup}),
            "latency_maks_ms": max(latensi) if latensi else None,
            "keyakinan": "tinggi" if len(host) >= 2 else "rendah",
        })
    return kejadian


def cari_kejadian():
    return gabung(kejadian_mentah())


if __name__ == "__main__":
    for k in cari_kejadian():
        print(
            k["mulai"], "->", k["selesai"], "|", ", ".join(k["host"]),
            "|", ", ".join(k["jenis"]), "|", k["latency_maks_ms"], "|", k["keyakinan"],
        )