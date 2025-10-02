import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip } from 'recharts';

export function ChartConvergence({ data }) {
  if (!data || data.length === 0) {
    return <div className="chart-empty">Optimization progress will appear here.</div>;
  }
  return (
    <div className="ow-chart">
      <ResponsiveContainer width="100%" height={320}>
        <AreaChart data={data.map((score, index) => ({ iteration: index, score }))}>
          <XAxis dataKey="iteration" />
          <YAxis />
          <Tooltip />
          <Area type="monotone" dataKey="score" stroke="#22d3ee" fill="#0f172a" fillOpacity={0.45} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
