import { Bot } from '@maxhub/max-bot-api'
import { config } from './config.js'
import { registerMenuHandlers } from './handlers/menu.js'
import { registerTalonHandlers } from './handlers/talons.js'
import { registerHelperHandlers } from './handlers/helpers.js'

export const bot = new Bot(config.MAX_BOT_TOKEN)

registerMenuHandlers(bot)
registerTalonHandlers(bot)
registerHelperHandlers(bot)