import { createContext, useCallback, useContext, useMemo, useState } from 'react';

const ToastContext = createContext({ notify: () => {} });

export function ToastProvider({ children }) {
  const [messages, setMessages] = useState([]);
  const notify = useCallback((message, variant = 'info') => {
    const id = crypto.randomUUID();
    setMessages((current) => [...current, { id, message, variant }]);
    setTimeout(() => {
      setMessages((current) => current.filter((item) => item.id !== id));
    }, 4500);
  }, []);

  const value = useMemo(() => ({ notify }), [notify]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="ow-toast-region" role="status" aria-live="polite">
        {messages.map((toast) => (
          <div key={toast.id} className={`ow-toast ow-toast-${toast.variant}`}>
            {toast.message}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  return useContext(ToastContext);
}
