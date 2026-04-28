import 'dotenv/config';

import { Bot, type Context } from '@maxhub/max-bot-api';

import { registerTalonHandlers } from './handlers/talon.js';
import { registerHelperHandlers } from './handlers/helper.js';

const token = process.env.MAX_BOT_TOKEN;

if (!token) {
  throw new Error('MAX_BOT_TOKEN is not set');
}

const bot = new Bot<Context>(token);

async function main() {
  registerTalonHandlers(bot);
  registerHelperHandlers(bot);

  await bot.start();

  console.log('MAX bot started');
}

main().catch((error) => {
  console.error('MAX bot failed:', error);
  process.exit(1);
});