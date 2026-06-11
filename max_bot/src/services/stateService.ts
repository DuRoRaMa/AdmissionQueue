import Redis from 'ioredis';
import { config } from '../config.js';

type State =
  | { kind: 'idle' }
  | { kind: 'waiting_talon_id' }
  | { kind: 'waiting_comment'; talonId: number };

const redis = new Redis(config.REDIS_URL);
const ttlSeconds = 30 * 60;

function key(userId: number): string {
  return `max-bot:state:${userId}`;
}

export async function getState(userId: number): Promise<State> {
  const raw = await redis.get(key(userId));

  if (!raw) {
    return { kind: 'idle' };
  }

  try {
    return JSON.parse(raw) as State;
  } catch {
    return { kind: 'idle' };
  }
}

export async function setState(
  userId: number,
  state: State,
): Promise<void> {
  await redis.set(
    key(userId),
    JSON.stringify(state),
    'EX',
    ttlSeconds,
  );
}

export async function clearState(
  userId: number,
): Promise<void> {
  await redis.del(key(userId));
}
