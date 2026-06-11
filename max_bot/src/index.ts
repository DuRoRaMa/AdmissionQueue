import { bot } from './bot.js';
import { startInternalServer } from './internalServer.js';
import { logger } from './logger.js';

async function main(): Promise<void> {
  try {
    await startInternalServer();

    logger.info('Starting MAX bot');
    await bot.start();
  } catch (error) {
    logger.error(error);
    process.exit(1);
  }
}

void main();
