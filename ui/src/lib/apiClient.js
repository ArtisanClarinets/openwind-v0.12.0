import axios from 'axios';

const api = axios.create({
  baseURL: 'http://127.0.0.1:8001/api/v1',
  timeout: 20000
});

export async function getHealth() {
  const response = await api.get('/health');
  return response.data;
}

export async function fetchPreset() {
  const response = await api.get('/presets/bb_clarinet');
  return response.data;
}

export async function recommend(body) {
  const response = await api.post('/recommend', body);
  return response.data;
}

export async function simulate(body) {
  const response = await api.post('/simulate', body);
  return response.data;
}

export async function startOptimization(body) {
  const response = await api.post('/optimize', body);
  return response.data;
}

export async function fetchOptimizationResult(jobId) {
  const response = await api.get(`/optimize/result/${jobId}`);
  return response.data;
}

export async function exportGeometry(fmt, body) {
  const response = await api.post(`/export/${fmt}`, body);
  return response.data;
}

export { api };
