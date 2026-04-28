import type { Bot, Context } from '@maxhub/max-bot-api';

import {
  BotActions,
  buildBackToMenuKeyboard,
} from '../services/messages.js';

import {
  clearSession,
  getSession,
  setSession,
} from '../services/session.js';

function getMessageText(ctx: Context): string {
  const rawCtx = ctx as any;

  return (
    rawCtx.message?.body?.text ??
    rawCtx.message?.text ??
    ''
  ).trim();
}

async function showHelperStub(ctx: Context) {
  setSession(ctx, { state: 'waiting_helper_bind_code' });

  await ctx.reply(
    [
      'Раздел помощника пока не подключен к базе данных.',
      '',
      'Позже здесь будет проверка, привязан ли ваш аккаунт MAX к сотруднику приемной комиссии.',
      '',
      'Сейчас можно ввести тестовый код привязки.',
    ].join('\n'),
    {
      attachments: [buildBackToMenuKeyboard()],
    },
  );
}

export function registerHelperHandlers(bot: Bot<Context>) {
  bot.command('helper', async (ctx) => {
    await showHelperStub(ctx);
  });

  bot.action(BotActions.HELPER_MENU, async (ctx) => {
    await showHelperStub(ctx);
  });

  bot.on('message_created', async (ctx) => {
    const session = getSession(ctx);

    if (session.state !== 'waiting_helper_bind_code') {
      return;
    }

    const text = getMessageText(ctx);

    if (!text) {
      await ctx.reply('Не удалось прочитать код. Попробуйте еще раз.');
      return;
    }

    clearSession(ctx);

    await ctx.reply(
      [
        `Принял код привязки помощника: ${text}`,
        '',
        'Пока база данных не подключена, код не проверяется.',
      ].join('\n'),
      {
        attachments: [buildBackToMenuKeyboard()],
      },
    );
  });
}