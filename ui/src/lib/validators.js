export function validateHoleSpacing(holes, minSpacing) {
  const issues = [];
  for (let i = 1; i < holes.length; i += 1) {
    const spacing = holes[i].axial_pos_mm - holes[i - 1].axial_pos_mm;
    if (spacing < minSpacing) {
      issues.push({ index: holes[i].index, message: `Hole ${holes[i].index + 1} spacing ${spacing.toFixed(1)}mm below minimum` });
    }
  }
  return issues;
}

export function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

export function sanitizeGeometry(geometry) {
  return {
    ...geometry,
    tone_holes: geometry.tone_holes.map((hole) => ({
      ...hole,
      axial_pos_mm: Math.max(hole.axial_pos_mm, 1),
      diameter_mm: Math.max(hole.diameter_mm, 2),
      chimney_mm: Math.max(hole.chimney_mm, 2),
      undercut_mm: hole.undercut_mm == null ? 0.8 : Math.max(hole.undercut_mm, 0)
    }))
  };
}
