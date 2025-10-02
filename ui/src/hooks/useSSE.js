import { useEffect, useRef } from 'react';

export function useSSE(url, onMessage) {
  const eventSourceRef = useRef(null);
  useEffect(() => {
    if (!url) return undefined;
    const source = new EventSource(url);
    eventSourceRef.current = source;
    source.onmessage = (event) => {
      onMessage?.(JSON.parse(event.data));
    };
    source.onerror = () => {
      source.close();
    };
    return () => source.close();
  }, [url, onMessage]);
  return eventSourceRef;
}
