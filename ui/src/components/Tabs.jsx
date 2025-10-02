import { useId, useState } from 'react';

export function Tabs({ items }) {
  const id = useId();
  const [active, setActive] = useState(items[0]?.value ?? '');
  return (
    <div className="ow-tabs">
      <div role="tablist" aria-label="Tabs">
        {items.map((item) => (
          <button
            key={item.value}
            role="tab"
            id={`${id}-${item.value}`}
            aria-selected={active === item.value}
            aria-controls={`${id}-${item.value}-panel`}
            tabIndex={active === item.value ? 0 : -1}
            className={active === item.value ? 'active' : ''}
            onClick={() => setActive(item.value)}
          >
            {item.label}
          </button>
        ))}
      </div>
      {items.map((item) => (
        <div
          key={item.value}
          role="tabpanel"
          id={`${id}-${item.value}-panel`}
          aria-labelledby={`${id}-${item.value}`}
          hidden={active !== item.value}
          className="ow-tab-panel"
        >
          {item.content}
        </div>
      ))}
    </div>
  );
}
