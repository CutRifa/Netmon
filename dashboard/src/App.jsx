import { useEffect, useState } from "react";
import {
  LineChart, Line, XAxis, YAxis, Tooltip, Legend,
  CartesianGrid, ResponsiveContainer,
} from "recharts";

const API = "http://127.0.0.1:8000";
const PALET = ["#60a5fa", "#4ade80", "#fbbf24", "#f472b6", "#a78bfa"];
const sel = { padding: "6px 8px" };

export default function App() {
  const [hosts, setHosts] = useState([]);
  const [grafik, setGrafik] = useState([]);
  const [stats, setStats] = useState([]);
  const [kejadian, setKejadian] = useState([]);
  const [error, setError] = useState(null);

  async function muatData() {
    try {
      // Daftar alamat diambil dari API, tidak ditulis manual
      const s = await fetch(`${API}/stats`).then((r) => r.json());
      const daftar = s.map((x) => x.host);

      const riwayat = await Promise.all(
        daftar.map((h) =>
          fetch(`${API}/history?host=${encodeURIComponent(h)}&limit=100`)
            .then((r) => r.json())
        )
      );

      const gabung = {};
      riwayat.forEach((data, i) => {
        data.forEach((d) => {
          if (!gabung[d.waktu]) gabung[d.waktu] = { waktu: d.waktu.slice(11) };
          gabung[d.waktu][daftar[i]] = d.latency_ms;
        });
      });

      setHosts(daftar);
      setStats(s);
      setGrafik(Object.keys(gabung).sort().map((k) => gabung[k]));
      setError(null);
    } catch (e) {
      setError("Tidak bisa mengambil data. Pastikan API (uvicorn) sedang berjalan.");
    }
  }

  async function muatKejadian() {
    try {
      const k = await fetch(`${API}/events?limit=20`).then((r) => r.json());
      setKejadian(k);
    } catch (e) {
      // kalau gagal, biarkan daftar lama
    }
  }

  useEffect(() => {
    muatData();
    muatKejadian();
    const t1 = setInterval(muatData, 10000);     // grafik: tiap 10 detik
    const t2 = setInterval(muatKejadian, 60000); // kejadian: tiap 1 menit
    return () => { clearInterval(t1); clearInterval(t2); };
  }, []);

  return (
    <div style={{ maxWidth: 1000, margin: "0 auto", padding: 24 }}>
      <h1>NetMon Dashboard</h1>
      <p style={{ color: "#94a3b8" }}>
        Latency jaringan (ms), 100 data terakhir per alamat, diperbarui tiap 10 detik.
      </p>

      {error && <p style={{ color: "#f87171" }}>{error}</p>}

      <div style={{ height: 360, background: "#1e293b", borderRadius: 12, padding: 16 }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={grafik}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="waktu" stroke="#94a3b8" minTickGap={40} />
            <YAxis stroke="#94a3b8" unit=" ms" />
            <Tooltip contentStyle={{ background: "#0f172a", border: "none" }} />
            <Legend />
            {hosts.map((h, i) => (
              <Line
                key={h}
                type="monotone"
                dataKey={h}
                stroke={PALET[i % PALET.length]}
                dot={false}
                strokeWidth={2}
                isAnimationActive={false}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>

      <h2 style={{ marginTop: 32 }}>Kejadian terdeteksi</h2>
      {kejadian.length === 0 ? (
        <p style={{ color: "#94a3b8" }}>Belum ada kejadian.</p>
      ) : (
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ textAlign: "left", color: "#94a3b8" }}>
                <th style={sel}>Mulai</th><th style={sel}>Selesai</th>
                <th style={sel}>Alamat</th><th style={sel}>Jenis</th>
                <th style={sel}>Latency maks (ms)</th><th style={sel}>Keyakinan</th>
              </tr>
            </thead>
            <tbody>
              {kejadian.map((k) => (
                <tr key={k.mulai + k.host.join()} style={{ borderTop: "1px solid #334155" }}>
                  <td style={sel}>{k.mulai.replace("T", " ")}</td>
                  <td style={sel}>{k.selesai.replace("T", " ")}</td>
                  <td style={sel}>{k.host.join(", ")}</td>
                  <td style={sel}>{k.jenis.join(", ")}</td>
                  <td style={sel}>{k.latency_maks_ms ?? "-"}</td>
                  <td
                    style={{
                      ...sel,
                      color: k.keyakinan === "tinggi" ? "#f87171" : "#94a3b8",
                      fontWeight: k.keyakinan === "tinggi" ? 700 : 400,
                    }}
                  >
                    {k.keyakinan}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <h2 style={{ marginTop: 32 }}>Statistik</h2>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr style={{ textAlign: "left", color: "#94a3b8" }}>
            <th style={sel}>Alamat</th><th style={sel}>Total ping</th>
            <th style={sel}>Rata-rata (ms)</th><th style={sel}>Min</th>
            <th style={sel}>Max</th><th style={sel}>Gagal (%)</th>
          </tr>
        </thead>
        <tbody>
          {stats.map((s) => (
            <tr key={s.host} style={{ borderTop: "1px solid #334155" }}>
              <td style={sel}>{s.host}</td>
              <td style={sel}>{s.total_ping}</td>
              <td style={sel}>{s.rata_rata_ms}</td>
              <td style={sel}>{s.min_ms}</td>
              <td style={sel}>{s.max_ms}</td>
              <td style={sel}>{s.gagal_persen}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}