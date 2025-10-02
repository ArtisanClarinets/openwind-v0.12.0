export function Field({ label, description, error, children }) {
  return (
    <div className={`ow-field ${error ? 'has-error' : ''}`}>
      <label>
        <span>{label}</span>
        {children}
      </label>
      {description && <p className="description">{description}</p>}
      {error && <p className="error">{error}</p>}
    </div>
  );
}

export function FieldRow({ children }) {
  return <div className="ow-field-row">{children}</div>;
}
