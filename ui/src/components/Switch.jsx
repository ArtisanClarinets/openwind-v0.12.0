import clsx from 'clsx';

export function Switch({ id, checked, onChange, label, description }) {
  return (
    <div className="ow-switch">
      <label htmlFor={id}>
        <span>{label}</span>
        {description && <small>{description}</small>}
      </label>
      <button
        id={id}
        role="switch"
        aria-checked={checked}
        className={clsx('toggle', checked ? 'on' : 'off')}
        onClick={() => onChange(!checked)}
        onKeyDown={(event) => {
          if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            onChange(!checked);
          }
        }}
      >
        <span className="toggle-label">{checked ? 'ON' : 'OFF'}</span>
      </button>
    </div>
  );
}
