import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, Legend } from 'recharts';

export function ChartImpedance({ data }) {
  if (!data || data.length === 0) {
    return <div className="chart-empty">Run a simulation to see impedance.</div>;
  }
  return (
    <div className="ow-chart">
      <ResponsiveContainer width="100%" height={320}>
        <LineChart data={data} margin={{ top: 16, right: 24, bottom: 8, left: 0 }}>
          <XAxis dataKey="freq" unit="Hz" />
          <YAxis yAxisId="left" label={{ value: '|Z|', angle: -90, position: 'insideLeft' }} />
          <YAxis yAxisId="right" orientation="right" label={{ value: 'Re(Z)', angle: -90 }} />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="abs" stroke="#38bdf8" dot={false} yAxisId="left" />
          <Line type="monotone" dataKey="re" stroke="#f97316" dot={false} yAxisId="right" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
