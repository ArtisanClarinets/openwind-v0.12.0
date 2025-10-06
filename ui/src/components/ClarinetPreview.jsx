const JOINT_COLORS = {
  upper: '#38bdf8',
  lower: '#f97316',
  auxiliary: '#a855f7'
};

const JOINT_LABELS = {
  upper: 'Upper joint chimneys (left hand)',
  lower: 'Lower joint chimneys (right hand)',
  auxiliary: 'Auxiliary tone holes and vents'
};

function classifyJoint(index) {
  if (index <= 2) return 'upper';
  if (index <= 5) return 'lower';
  return 'auxiliary';
}

export function ClarinetPreview({ toneHoles = [], lengthMm = 0, boreMm = 0 }) {
  if (!toneHoles.length) {
    return <div className="clarinet-preview empty">Add tone holes to preview the clarinet body.</div>;
  }

  const sorted = [...toneHoles]
    .map((hole, index) => ({
      ...hole,
      index,
      axial_pos_mm: Number(hole.axial_pos_mm) || 0,
      diameter_mm: Number(hole.diameter_mm) || 0,
      chimney_mm: Number(hole.chimney_mm) || 0,
      joint: classifyJoint(index)
    }))
    .sort((a, b) => a.axial_pos_mm - b.axial_pos_mm);

  const safeLength = Math.max(lengthMm, sorted.at(-1)?.axial_pos_mm ?? 0) + 40;
  const ratio = safeLength > 0 ? 1 / safeLength : 0;
  const bodyWidth = Math.max(boreMm, 15);

  return (
    <div className="clarinet-preview">
      <svg viewBox="0 0 1000 180" role="img" aria-label="Clarinet body preview">
        <defs>
          <linearGradient id="clarinet-body" x1="0%" x2="100%" y1="0%" y2="0%">
            <stop offset="0%" stopColor="#0f172a" />
            <stop offset="100%" stopColor="#1f2937" />
          </linearGradient>
        </defs>
        <rect
          x="40"
          y={90 - bodyWidth / 4}
          width={920}
          height={bodyWidth / 2}
          rx={bodyWidth / 4}
          fill="url(#clarinet-body)"
          stroke="#1e293b"
        />
        <polygon points="960,90 990,110 990,70" fill="#1f2937" />
        {sorted.map((hole) => {
          const cx = 40 + (hole.axial_pos_mm * ratio + 0.04) * 920;
          const radius = Math.max(4, (hole.diameter_mm / 20) * 24);
          return (
            <g key={hole.index}>
              <circle
                cx={cx}
                cy={90}
                r={radius}
                fill={JOINT_COLORS[hole.joint]}
                fillOpacity={hole.closed ? 0.35 : 0.7}
                stroke="#0f172a"
                strokeWidth={hole.closed ? 1 : 2}
              />
              <line
                x1={cx}
                x2={cx}
                y1={90 - radius}
                y2={90 - radius - hole.chimney_mm * 2}
                stroke={JOINT_COLORS[hole.joint]}
                strokeWidth={2}
                strokeLinecap="round"
              />
            </g>
          );
        })}
      </svg>
      <div className="clarinet-legend" aria-hidden="true">
        {Object.entries(JOINT_LABELS).map(([key, label]) => (
          <span key={key}>
            <span className="legend-dot" style={{ backgroundColor: JOINT_COLORS[key] }} />
            {label}
          </span>
        ))}
      </div>
    </div>
  );
}
