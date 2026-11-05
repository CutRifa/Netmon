import { useEffect, useState } from "react";
import {
  LineChart, Line, XAxis, YAxis, Tooltip, Legend,
  CartesianGrid, ResponsiveContainer,
} from "recharts";

const API = "http://127.0.0.1:8000";
const HOSTS = ["google.com", "1.1.1.1", "192.168.140.77"];
const WARNA = {
  "google.com": "#60a5fa",
  "1.1.1.1": "#4ade80",
  "192.168.140.77": "#fbbf24",
};

export default function App() {
  const [grafik, setGrafik] = useState([]);
  const [stats, setStats] = useState([]);
  const [error, setError] = useState(null);

  async function muat() {
    try {
      // Ambil 100 data terakhir untuk tiap alamat
      const riwayat = await Promise.all(
        HOSTS.map((h) =>
          fetch(`${API}/history?host=${encodeURIComponent(h)}&limit=100`)
            .then((r) => r.json())
        )
      );

      // Gabungkan berdasarkan waktu, supaya satu baris = satu putaran
      const gabung = {};
      riwayat.forEach((data, i) => {
        data.forEach((d) => {
          if (!gabung[d.waktu]) gabung[d.waktu] = { waktu: d.waktu.slice(11) };
          gabung[d.waktu][HOSTS[i]] = d.latency_ms;
        });
      });
      setGrafik(Object.keys(gabung).sort().map((k) => gabung[k]));

      const s = await fetch(`${API}/stats`).then((r) => r.json());
      setStats(s);
      setError(null);
    } catch (e) {
      setError("Tidak bisa mengambil data. Pastikan API (uvicorn) sedang berjalan.");
    }
  }

  useEffect(() => {
    muat();
    const timer = setInterval(muat, 10000); // perbarui tiap 10 detik
    return () => clearInterval(timer);
  }, []);

  return (
    <div style={{ maxWidth: 1000, margin: "0 auto", padding: 24 }}>
      <h1>NetMon Dashboard</h1>
      <p style={{ color: "#94a3b8" }}>
        Latency jaringan (ms), diperbarui otomatis tiap 10 detik.
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
            {HOSTS.map((h) => (
              <Line
                key={h}
                type="monotone"
                dataKey={h}
                stroke={WARNA[h]}
                dot={false}
                strokeWidth={2}
                isAnimationActive={false}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>

      <h2 style={{ marginTop: 32 }}>Statistik</h2>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr style={{ textAlign: "left", color: "#94a3b8" }}>
            <th>Alamat</th><th>Total ping</th><th>Rata-rata (ms)</th>
            <th>Min</th><th>Max</th><th>Gagal (%)</th>
          </tr>
        </thead>
        <tbody>
          {stats.map((s) => (
            <tr key={s.host} style={{ borderTop: "1px solid #334155" }}>
              <td>{s.host}</td>
              <td>{s.total_ping}</td>
              <td>{s.rata_rata_ms}</td>
              <td>{s.min_ms}</td>
              <td>{s.max_ms}</td>
              <td>{s.gagal_persen}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}