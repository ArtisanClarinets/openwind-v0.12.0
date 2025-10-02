import { useCallback } from 'react';
import axios from 'axios';

const client = axios.create({
  baseURL: 'http://127.0.0.1:8001/api/v1',
  timeout: 20000
});

export function useApi() {
  const get = useCallback(async (path) => {
    const response = await client.get(path);
    return response.data;
  }, []);

  const postJSON = useCallback(async (path, payload, config = {}) => {
    const response = await client.post(path, payload, config);
    return response.data;
  }, []);

  const postStream = useCallback((path, params, onMessage) => {
    const url = new URL(client.defaults.baseURL + path);
    Object.entries(params || {}).forEach(([key, value]) => url.searchParams.set(key, value));
    const eventSource = new EventSource(url);
    eventSource.onmessage = (event) => {
      if (onMessage) {
        onMessage(JSON.parse(event.data));
      }
    };
    return () => eventSource.close();
  }, []);

  return { get, postJSON, postStream };
}
