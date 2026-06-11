import axios from 'axios';
import { config } from '../config.js';

export const djangoClient = axios.create({
  baseURL: config.DJANGO_API_URL,
  timeout: 10_000,
  headers: {
    'X-Internal-Token': config.DJANGO_INTERNAL_TOKEN,
    'Content-Type': 'application/json',
  },
});
