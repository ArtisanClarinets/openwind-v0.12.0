export function Card({ title, action, children, footer, className }) {
  return (
    <section className={`ow-card ${className ?? ''}`}>
      {(title || action) && (
        <header className="ow-card-header">
          <h2>{title}</h2>
          {action}
        </header>
      )}
      <div className="ow-card-body">{children}</div>
      {footer && <footer className="ow-card-footer">{footer}</footer>}
    </section>
  );
}
