import { Keyboard, type Bot } from '@maxhub/max-bot-api';
import {
  backToMenuKeyboard,
  mainKeyboard,
  talonKeyboard,
} from '../keyboards/mainKeyboard.js';
import {
  getMyTalons,
  getTalonDetails,
  saveTalonComment,
  subscribeToTalon,
} from '../services/queueService.js';
import {
  clearState,
  getState,
  setState,
} from '../services/stateService.js';
import { logger } from '../logger.js';

function getUserId(ctx: any): number | null {
  return ctx.user?.user_id ?? null;
}

function getMessageText(ctx: any): string {
  return String(ctx.message?.body?.text ?? '').trim();
}

function formatError(error: any): string {
  return (
    error?.response?.data?.detail ??
    'Не удалось выполнить действие. Попробуйте ещё раз.'
  );
}

export function registerTalonHandlers(bot: Bot) {
  bot.action('talons:subscribe', async (ctx: any) => {
    const userId = getUserId(ctx);

    if (!userId) {
      return;
    }

    await setState(userId, {
      kind: 'waiting_talon_id',
    });

    await ctx.reply(
      'Напишите код, указанный на талоне.',
      {
        attachments: [backToMenuKeyboard()],
      },
    );
  });

  bot.action('talons:list', async (ctx: any) => {
    const userId = getUserId(ctx);

    if (!userId) {
      return;
    }

    try {
      const talons = await getMyTalons(userId);

      if (talons.length === 0) {
        await ctx.reply(
          'У вас пока нет подключённых талонов.',
          {
            attachments: [mainKeyboard()],
          },
        );
        return;
      }

      const rows = talons.map((talon) => [
        // Одна кнопка на строку, чтобы длинный статус не сжимался.
        Keyboard.button.callback(
          `${talon.name} — ${talon.status_label}`,
          `talon:open:${talon.id}`,
        ),
      ]);

      rows.push([
        Keyboard.button.callback(
          'Меню',
          'menu:main',
        ),
      ]);

      await ctx.reply('Список ваших талонов:', {
        attachments: [
          Keyboard.inlineKeyboard(rows),
        ],
      });
    } catch (error) {
      logger.error(error);
      await ctx.reply(formatError(error));
    }
  });

  bot.action(
    /talon:open:(\d+)/,
    async (ctx: any) => {
      const userId = getUserId(ctx);
      const talonId = Number(ctx.match?.[1]);

      if (!userId || !Number.isFinite(talonId)) {
        return;
      }

      try {
        const talon = await getTalonDetails(
          userId,
          talonId,
        );

        const text = [
          `Номер талона: ${talon.name}`,
          `Дата создания: ${talon.created_at}`,
          `Статус: ${talon.status_label}`,
        ].join('\n');

        await ctx.reply(text, {
          attachments: [
            talonKeyboard(
              talon.id,
              Boolean(talon.comment),
            ),
          ],
        });
      } catch (error) {
        logger.error(error);
        await ctx.reply(formatError(error));
      }
    },
  );

  bot.action(
    /talon:comment:add:(\d+)/,
    async (ctx: any) => {
      const userId = getUserId(ctx);
      const talonId = Number(ctx.match?.[1]);

      if (!userId || !Number.isFinite(talonId)) {
        return;
      }

      await setState(userId, {
        kind: 'waiting_comment',
        talonId,
      });

      await ctx.reply(
        'Напишите отзыв о работе оператора.',
        {
          attachments: [backToMenuKeyboard()],
        },
      );
    },
  );

  bot.action(
    /talon:comment:(\d+)/,
    async (ctx: any) => {
      const userId = getUserId(ctx);
      const talonId = Number(ctx.match?.[1]);

      if (!userId || !Number.isFinite(talonId)) {
        return;
      }

      try {
        const talon = await getTalonDetails(
          userId,
          talonId,
        );

        await ctx.reply(
          talon.comment
            ? `${talon.comment}\n\nСпасибо за ваш отзыв!`
            : 'Отзыв ещё не оставлен.',
          {
            attachments: [mainKeyboard()],
          },
        );
      } catch (error) {
        logger.error(error);
        await ctx.reply(formatError(error));
      }
    },
  );

  bot.on('message_created', async (ctx: any) => {
    const userId = getUserId(ctx);
    const text = getMessageText(ctx);

    if (
      !userId ||
      !text ||
      text.startsWith('/')
    ) {
      return;
    }

    const state = await getState(userId);

    if (state.kind === 'waiting_talon_id') {
      const talonId = Number(text);

      if (!Number.isInteger(talonId)) {
        await ctx.reply(
          'Код талона должен быть числом. Попробуйте ещё раз.',
        );
        return;
      }

      try {
        const result = await subscribeToTalon(
          userId,
          talonId,
        );

        await clearState(userId);

        await ctx.reply(
          `Вы подписались на обновления талона ${result.name}.`,
          {
            attachments: [mainKeyboard()],
          },
        );
      } catch (error) {
        logger.error(error);
        await ctx.reply(formatError(error));
      }

      return;
    }

    if (state.kind === 'waiting_comment') {
      try {
        const talon = await saveTalonComment(
          userId,
          state.talonId,
          text,
        );

        await clearState(userId);

        await ctx.reply(
          `${talon.comment}\n\nСпасибо за ваш отзыв!`,
          {
            attachments: [mainKeyboard()],
          },
        );
      } catch (error) {
        logger.error(error);
        await ctx.reply(formatError(error));
      }
    }
  });
}
