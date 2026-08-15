import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const client = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000,
});

export function sendPrompt(query, sessionId) {
  return client.post('/prompt', { query, session_id: sessionId });
}

export function analyzeEmotion(text) {
  return client.post('/analyze-emotion', { text });
}

export function getEmotionGraph() {
  return client.get('/emotion-graph');
}

export function getRandomQuote() {
  return client.get('/random-quote');
}

export default client;