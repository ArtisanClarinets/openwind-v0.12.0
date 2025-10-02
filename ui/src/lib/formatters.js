export function formatMm(value, digits = 1) {
  return `${value.toFixed(digits)} mm`;
}

export function formatHz(value, digits = 1) {
  return `${value.toFixed(digits)} Hz`;
}

export function formatCents(value) {
  const symbol = value > 0 ? '+' : '';
  return `${symbol}${value.toFixed(1)} ¢`;
}
