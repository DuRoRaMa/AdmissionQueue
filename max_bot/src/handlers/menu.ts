import type { Bot } from '@maxhub/max-bot-api';
import { mainKeyboard } from '../keyboards/mainKeyboard.js';

const greeting = [
  'Привет!',
  'Это бот электронной очереди Приёмной комиссии ДВФУ.',
  '',
  'Чтобы узнавать о событиях талона, нажмите «Подписаться».',
  'Чтобы посмотреть свои талоны или оставить отзыв, откройте «Мои талоны».',
].join('\n');

export function registerMenuHandlers(bot: Bot) {
  const showMenu = async (ctx: any) => {
    await ctx.reply(greeting, {
      attachments: [mainKeyboard()],
    });
  };

  bot.command('start', showMenu);
  bot.action('menu:main', showMenu);
  bot.on('bot_started', showMenu);
}
