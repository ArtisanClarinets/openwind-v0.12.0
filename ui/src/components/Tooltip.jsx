import { useState } from 'react';

export function Tooltip({ label, children }) {
  const [visible, setVisible] = useState(false);
  return (
    <span
      className="ow-tooltip"
      onMouseEnter={() => setVisible(true)}
      onMouseLeave={() => setVisible(false)}
      onFocus={() => setVisible(true)}
      onBlur={() => setVisible(false)}
    >
      {children}
      {visible && <span role="tooltip" className="ow-tooltip-content">{label}</span>}
    </span>
  );
}
