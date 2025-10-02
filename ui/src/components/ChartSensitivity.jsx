import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend } from 'recharts';

function formatValue(value) {
  if (Number.isNaN(value) || value == null) {
    return null;
  }
  return Math.round(value * 100) / 100;
}

export function ChartSensitivity({ data }) {
  if (!data || data.length === 0) {
    return <div className="chart-empty">Sensitivity metrics will appear here.</div>;
  }

  const parsed = data.map((item) => ({
    hole: typeof item.hole_index === 'number' ? `H${item.hole_index + 1}` : String(item.hole_index ?? ''),
    axial: formatValue(item.axial_delta_cents),
    diameter: formatValue(item.diameter_delta_cents)
  }));

  return (
    <div className="ow-chart">
      <ResponsiveContainer width="100%" height={320}>
        <BarChart data={parsed} margin={{ top: 16, right: 16, bottom: 8, left: 8 }}>
          <XAxis dataKey="hole" label={{ value: 'Hole', position: 'insideBottom', offset: -4 }} />
          <YAxis label={{ value: 'Δ cents', angle: -90, position: 'insideLeft' }} />
          <Tooltip formatter={(value) => `${value} cents`} />
          <Legend />
          <Bar dataKey="axial" name="Axial +0.5mm" fill="#38bdf8" radius={[6, 6, 0, 0]} />
          <Bar dataKey="diameter" name="Diameter +0.3mm" fill="#facc15" radius={[6, 6, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
