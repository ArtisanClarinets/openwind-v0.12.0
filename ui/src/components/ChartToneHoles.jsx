import {
  ResponsiveContainer,
  ComposedChart,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  Area,
  Scatter,
  ReferenceLine
} from 'recharts';

const JOINT_LABELS = {
  upper: 'Upper joint chimney',
  lower: 'Lower joint chimney',
  auxiliary: 'Auxiliary tone hole'
};

function classifyJoint(index) {
  if (index <= 2) return 'upper';
  if (index <= 5) return 'lower';
  return 'auxiliary';
}

function ToneHoleTooltip({ active, payload, label }) {
  if (!active || !payload || payload.length === 0) {
    return null;
  }
  const hole = payload[0].payload;
  const position = typeof label === 'number' ? label : hole.axial_pos_mm;
  return (
    <div className="chart-tooltip">
      <strong>Hole {hole.displayIndex}</strong>
      <div>{JOINT_LABELS[hole.joint]}</div>
      <div>Axial position: {position.toFixed(1)} mm</div>
      <div>Diameter: {hole.diameter_mm.toFixed(1)} mm</div>
      <div>Chimney: {hole.chimney_mm.toFixed(1)} mm</div>
      <div>State: {hole.closed ? 'Closed' : 'Open'}</div>
    </div>
  );
}

function ChartToneHoles({ toneHoles = [], boreMm, lengthMm }) {
  if (!toneHoles.length) {
    return <div className="chart-empty">Add tone holes to view their layout.</div>;
  }

  const sorted = [...toneHoles]
    .map((hole, index) => ({
      ...hole,
      joint: classifyJoint(index),
      displayIndex: index + 1,
      axial_pos_mm: Number(hole.axial_pos_mm) || 0,
      diameter_mm: Number(hole.diameter_mm) || 0,
      chimney_mm: Number(hole.chimney_mm) || 0,
      bore: Number(boreMm) || 0
    }))
    .sort((a, b) => a.axial_pos_mm - b.axial_pos_mm);

  const diameterSeries = sorted.map((hole) => ({
    ...hole,
    category: hole.closed ? 'Closed' : 'Open'
  }));

  const chimneySeries = sorted.map((hole) => ({
    ...hole,
    category: JOINT_LABELS[hole.joint]
  }));

  const maxDiameter = Math.max(boreMm ?? 0, ...sorted.map((hole) => hole.diameter_mm)) + 2;
  const maxChimney = Math.max(...sorted.map((hole) => hole.chimney_mm), 12) + 4;

  return (
    <div className="ow-chart">
      <ResponsiveContainer width="100%" height={300}>
        <ComposedChart
          data={sorted}
          margin={{ top: 16, right: 32, bottom: 16, left: 0 }}
        >
          <XAxis
            dataKey="axial_pos_mm"
            type="number"
            domain={[0, Math.max(lengthMm ?? 0, sorted.at(-1)?.axial_pos_mm ?? 0) + 20]}
            unit="mm"
            label={{ value: 'Unfolded position (mm)', position: 'insideBottom', offset: -6 }}
          />
          <YAxis
            yAxisId="diameter"
            domain={[0, maxDiameter]}
            label={{ value: 'Hole diameter (mm)', angle: -90, position: 'insideLeft' }}
          />
          <YAxis
            yAxisId="chimney"
            orientation="right"
            domain={[0, maxChimney]}
            label={{ value: 'Chimney height (mm)', angle: -90, position: 'insideRight' }}
          />
          <Tooltip content={<ToneHoleTooltip />} />
          <Legend />
          <Area
            yAxisId="diameter"
            type="step"
            dataKey="bore"
            name="Bore"
            isAnimationActive={false}
            fill="rgba(59, 130, 246, 0.1)"
            stroke="#3b82f6"
            strokeDasharray="4 4"
            dot={false}
          />
          <Scatter
            yAxisId="diameter"
            name="Hole diameter"
            data={diameterSeries}
            dataKey="diameter_mm"
            fill="#38bdf8"
          />
          <Scatter
            yAxisId="chimney"
            name="Chimney height"
            data={chimneySeries}
            dataKey="chimney_mm"
            fill="#f97316"
          />
          {lengthMm ? (
            <ReferenceLine
              x={lengthMm}
              stroke="#94a3b8"
              strokeDasharray="3 3"
              label={{ value: 'Bell end', position: 'top' }}
            />
          ) : null}
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}

export { ChartToneHoles };
