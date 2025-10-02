import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, ReferenceLine } from 'recharts';

export function ChartIntonation({ data }) {
  if (!data || data.length === 0) {
    return <div className="chart-empty">Intonation offsets will appear here.</div>;
  }
  return (
    <div className="ow-chart">
      <ResponsiveContainer width="100%" height={320}>
        <BarChart data={data} margin={{ top: 16, right: 24, bottom: 8, left: 0 }}>
          <XAxis dataKey="note" />
          <YAxis unit="¢" domain={[-50, 50]} />
          <Tooltip />
          <ReferenceLine y={0} stroke="#16a34a" />
          <Bar dataKey="cents" fill="#c084fc" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
