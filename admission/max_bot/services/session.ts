import type { Context } from "@maxhub/max-bot-api";

export type UserSessions =
    | { state: 'idle'}
    | { state: 'waiting_talon_id' }
    | { state: 'waiting_helper_bind_code' };

const sessions = new Map<string, UserSessions>()

export function getContextKey(ctx: Context): string {
    const rawCtx = ctx as any;

    const userId =
        rawCtx.user?.user_id ??
        rawCtx.update?.user?.user_id ??
        rawCtx.message?.sender?.user_id;

    const chatId =
        rawCtx.chat?.chat_id ??
        rawCtx.update?.chat_id ??
        rawCtx.message?.recipient?.chat_id;

    return String(userId ?? chatId ?? 'unknown');    
}

export function getSession(ctx: Context): UserSessions {
  const key = getContextKey(ctx);
  return sessions.get(key) ?? { state: 'idle' };
}

export function setSession(ctx: Context, session: UserSessions) {
  const key = getContextKey(ctx);
  sessions.set(key, session);
}

export function clearSession(ctx: Context) {
  const key = getContextKey(ctx);
  sessions.set(key, { state: 'idle' });
}
