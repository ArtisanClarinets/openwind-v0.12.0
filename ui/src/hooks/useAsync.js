import { useCallback, useState } from 'react';

export function useAsync(asyncFn, immediate = false) {
  const [status, setStatus] = useState('idle');
  const [value, setValue] = useState(null);
  const [error, setError] = useState(null);

  const execute = useCallback(
    async (...args) => {
      setStatus('pending');
      setError(null);
      try {
        const response = await asyncFn(...args);
        setValue(response);
        setStatus('success');
        return response;
      } catch (err) {
        setError(err);
        setStatus('error');
        throw err;
      }
    },
    [asyncFn]
  );

  return { execute, status, value, error };
}
