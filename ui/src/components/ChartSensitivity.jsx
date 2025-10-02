import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip } from 'recharts';

export function ChartSensitivity({ data }) {
  if (!data || data.length === 0) {
    return <div className="chart-empty">Sensitivity metrics will appear here.</div>;
  }
  return (
    <div className="ow-chart">
      <ResponsiveContainer width="100%" height={320}>
        <BarChart data={data} margin={{ top: 16, right: 16, bottom: 8, left: 8 }}>
          <XAxis dataKey="iteration" />
          <YAxis />
          <Tooltip />
          <Bar dataKey="score" fill="#facc15" radius={[6, 6, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
