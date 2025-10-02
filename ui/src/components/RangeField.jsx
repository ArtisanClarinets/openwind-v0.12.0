import { Field } from './Form.jsx';

export function RangeField({ label, value, onChange, min, max, step = 1, description, unit }) {
  return (
    <Field label={label} description={description}>
      <div className="ow-range-field">
        <input
          type="range"
          value={value}
          min={min}
          max={max}
          step={step}
          onChange={(event) => onChange(Number(event.target.value))}
        />
        <span>{value}{unit}</span>
      </div>
    </Field>
  );
}
