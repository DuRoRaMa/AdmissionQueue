import type { Bot, Context } from '@maxhub/max-bot-api';

import {
  BotActions,
  buildBackToMenuKeyboard,
  buildMainMenuKeyboard,
  buildStartMessage,
} from '../services/messages.js';

import {
  clearSession,
  getSession,
  setSession,
} from '../services/session.js';

function getStartPayload(ctx: Context): string | null {
  const rawCtx = ctx as any;
  return rawCtx.update?.payload ?? rawCtx.payload ?? null;
}

function getMessageText(ctx: Context): string {
  const rawCtx = ctx as any;

  return (
    rawCtx.message?.body?.text ??
    rawCtx.message?.text ??
    ''
  ).trim();
}

export async function showMainMenu(ctx: Context, payload?: string | null) {
  clearSession(ctx);

  await ctx.reply(buildStartMessage(payload), {
    attachments: [buildMainMenuKeyboard()],
  });
}

export function registerTalonHandlers(bot: Bot<Context>) {
  bot.on('bot_started', async (ctx) => {
    const payload = getStartPayload(ctx);
    await showMainMenu(ctx, payload);
  });

  bot.command('start', async (ctx) => {
    await showMainMenu(ctx);
  });

  bot.action(BotActions.MAIN_MENU, async (ctx) => {
    await showMainMenu(ctx);
  });

  bot.action(BotActions.TALONS_LIST, async (ctx) => {
    clearSession(ctx);

    await ctx.reply(
      [
        'Раздел «Мои талоны» пока не подключен.',
        '',
        'Следующим этапом мы добавим модели Django и будем получать талоны из базы данных.',
      ].join('\n'),
      {
        attachments: [buildBackToMenuKeyboard()],
      },
    );
  });

  bot.action(BotActions.TALONS_SUBSCRIBE, async (ctx) => {
    setSession(ctx, { state: 'waiting_talon_id' });

    await ctx.reply(
      [
        'Введите номер талона, чтобы подписаться на его обновления.',
        '',
        'Пока база данных не подключена, я только проверю сценарий ввода.',
      ].join('\n'),
      {
        attachments: [buildBackToMenuKeyboard()],
      },
    );
  });

  bot.on('message_created', async (ctx) => {
    const session = getSession(ctx);

    if (session.state !== 'waiting_talon_id') {
      return;
    }

    const text = getMessageText(ctx);

    if (!text) {
      await ctx.reply('Не удалось прочитать номер талона. Попробуйте еще раз.');
      return;
    }

    clearSession(ctx);

    await ctx.reply(
      [
        `Принял номер талона: ${text}`,
        '',
        'Пока база данных не подключена, подписка не сохраняется.',
      ].join('\n'),
      {
        attachments: [buildBackToMenuKeyboard()],
      },
    );
  });
}