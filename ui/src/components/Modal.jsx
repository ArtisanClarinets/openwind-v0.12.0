import { useEffect } from 'react';
import { createPortal } from 'react-dom';

export function Modal({ open, title, children, onClose, footer }) {
  useEffect(() => {
    function onKeyDown(event) {
      if (event.key === 'Escape') {
        onClose?.();
      }
    }
    if (open) {
      document.addEventListener('keydown', onKeyDown);
    }
    return () => document.removeEventListener('keydown', onKeyDown);
  }, [open, onClose]);

  if (!open) return null;
  return createPortal(
    <div className="ow-modal" role="dialog" aria-modal="true" aria-label={title}>
      <div className="ow-modal-surface">
        <header>
          <h2>{title}</h2>
          <button className="ow-modal-close" onClick={onClose} aria-label="Close dialog">
            ×
          </button>
        </header>
        <div className="ow-modal-body">{children}</div>
        {footer && <footer className="ow-modal-footer">{footer}</footer>}
      </div>
    </div>,
    document.body
  );
}
