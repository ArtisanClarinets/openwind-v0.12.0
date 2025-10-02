import { Field } from './Form.jsx';

export function NumberField({ label, value, onChange, min, max, step = 0.1, description, error, unit }) {
  return (
    <Field label={label} description={description} error={error}>
      <div className="ow-number-field">
        <input
          type="number"
          value={value}
          min={min}
          max={max}
          step={step}
          onChange={(event) => onChange(Number(event.target.value))}
        />
        {unit && <span className="unit">{unit}</span>}
      </div>
    </Field>
  );
}
