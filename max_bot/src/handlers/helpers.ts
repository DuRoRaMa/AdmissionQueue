import type { Bot } from '@maxhub/max-bot-api'
import {
  helperKeyboard,
  helperRequestKeyboard,
  mainKeyboard,
} from '../keyboards/mainKeyboard.js'
import {
  completeHelperRequest,
  getHelper,
  getHelperRequests,
  linkHelper,
  toggleHelperActive,
} from '../services/helperService.js'
import { logger } from '../logger.js'

function getUserId(ctx: any): number | null {
  const value =
    ctx.user?.user_id ??
    ctx.sender?.user_id ??
    ctx.message?.sender?.user_id ??
    ctx.message?.recipient?.user_id ??
    ctx.update?.user?.user_id ??
    ctx.update?.message?.sender?.user_id ??
    ctx.update?.message?.recipient?.user_id

  if (value === undefined || value === null) {
    logger.warn(
      {
        ctxKeys: Object.keys(ctx ?? {}),
        user: ctx.user,
        sender: ctx.sender,
        messageSender: ctx.message?.sender,
        messageRecipient: ctx.message?.recipient,
        updateUser: ctx.update?.user,
        updateMessageSender: ctx.update?.message?.sender,
      },
      'MAX user_id not found',
    )

    return null
  }

  const userId = Number(value)

  if (!Number.isFinite(userId)) {
    logger.warn(
      {
        value,
      },
      'MAX user_id is not a number',
    )

    return null
  }

  return userId
}

function getMessageText(ctx: any): string {
  return String(
    ctx.message?.body?.text ??
    ctx.message?.text ??
    ctx.update?.message?.body?.text ??
    ctx.update?.message?.text ??
    ctx.body?.text ??
    '',
  ).trim()
}

function formatError(error: any): string {
  return (
    error?.response?.data?.detail ??
    error?.message ??
    'Не удалось выполнить действие. Попробуйте ещё раз.'
  )
}

function helperName(helper: any): string {
  return helper.full_name || helper.username || 'помощник'
}

function helperStatusText(isActive: boolean): string {
  return isActive ? 'активен' : 'не активен'
}

function buildHelperText(helper: any): string {
  return [
    `Привет, ${helperName(helper)}!`,
    '',
    `Сектор: ${helper.sector}`,
    `Статус: ${helperStatusText(helper.is_active)}`,
    `Активных заявок: ${helper.active_requests_count}`,
    '',
    'Здесь можно менять активность помощника и смотреть незавершенные заявки.',
  ].join('\n')
}

function buildRequestText(request: any): string {
  return [
    'Вызов помощника',
    '',
    `От: ${request.from}`,
    `Срочность: ${request.priority}`,
    `Тема: ${request.theme}`,
    `Создано: ${request.created_at}`,
    '',
    `Текст:\n${request.text || 'Без комментария'}`,
  ].join('\n')
}

async function showHelperMenu(ctx: any) {
  const userId = getUserId(ctx)

  if (!userId) {
    await ctx.reply(
      'Не удалось определить пользователя MAX. Попробуйте написать /start и повторить действие.',
    )
    return
  }

  try {
    const helper = await getHelper(userId)

    await ctx.reply(
      buildHelperText(helper),
      {
        attachments: [
          helperKeyboard(helper.is_active),
        ],
      },
    )
  } catch (error) {
    logger.error(error)

    await ctx.reply(
      [
        'MAX не привязан к профилю помощника.',
        '',
        'Сначала получите код привязки в web-системе электронной очереди.',
        'После этого отправьте команду:',
        '/link КОД',
      ].join('\n'),
      {
        attachments: [
          mainKeyboard(),
        ],
      },
    )
  }
}

async function showHelperRequests(ctx: any) {
  const userId = getUserId(ctx)

  if (!userId) {
    await ctx.reply(
      'Не удалось определить пользователя MAX. Попробуйте написать /start и повторить действие.',
    )
    return
  }

  try {
    const requests = await getHelperRequests(userId)

    if (requests.length === 0) {
      await ctx.reply(
        'Активных заявок помощи нет.',
        {
          attachments: [
            helperKeyboard(false),
          ],
        },
      )
      return
    }

    for (const request of requests) {
      await ctx.reply(
        buildRequestText(request),
        {
          attachments: [
            helperRequestKeyboard(request.id),
          ],
        },
      )
    }
  } catch (error) {
    logger.error(error)
    await ctx.reply(formatError(error))
  }
}

async function handleLinkCommand(ctx: any) {
  const userId = getUserId(ctx)

  if (!userId) {
    await ctx.reply(
      'Не удалось определить пользователя MAX. Попробуйте написать /start и повторить привязку.',
    )
    return
  }

  const text = getMessageText(ctx)
  const code = text.replace(/^\/link\s*/i, '').trim().toUpperCase()

  logger.info(
    {
      userId,
      text,
      code,
    },
    'MAX helper link command received',
  )

  if (!code) {
    await ctx.reply('Отправьте команду в формате: /link КОД')
    return
  }

  try {
    const result = await linkHelper(userId, code)
    const helper = result.helper

    if (!helper) {
      await ctx.reply(
        result.detail ?? 'MAX успешно привязан.',
        {
          attachments: [
            mainKeyboard(),
          ],
        },
      )
      return
    }

    await ctx.reply(
      [
        result.detail ?? 'MAX успешно привязан к профилю помощника.',
        '',
        `Пользователь: ${helperName(helper)}`,
        `Сектор: ${helper.sector}`,
        `Статус: ${helperStatusText(helper.is_active)}`,
      ].join('\n'),
      {
        attachments: [
          helperKeyboard(helper.is_active),
        ],
      },
    )
  } catch (error) {
    logger.error(error)
    await ctx.reply(formatError(error))
  }
}

export function registerHelperHandlers(bot: Bot) {
  bot.command('link', handleLinkCommand)

  /**
   * Fallback для MAX:
   * bot.command('link') может не срабатывать на команду с аргументом `/link CODE`,
   * поэтому отдельно перехватываем обычное входящее сообщение.
   */
  bot.on('message_created', async (ctx: any, next?: any) => {
    const text = getMessageText(ctx)

    if (text.toLowerCase().startsWith('/link')) {
      await handleLinkCommand(ctx)
      return
    }

    if (typeof next === 'function') {
      return next()
    }
  })

  bot.command('helper', showHelperMenu)

  bot.action('helper:menu', showHelperMenu)

  bot.action('helper:toggle', async (ctx: any) => {
    const userId = getUserId(ctx)

    if (!userId) {
      await ctx.reply(
        'Не удалось определить пользователя MAX. Попробуйте написать /start и повторить действие.',
      )
      return
    }

    try {
      const helper = await toggleHelperActive(userId)

      await ctx.reply(
        [
          'Статус помощника обновлен.',
          '',
          `Текущий статус: ${helperStatusText(helper.is_active)}`,
        ].join('\n'),
        {
          attachments: [
            helperKeyboard(helper.is_active),
          ],
        },
      )
    } catch (error) {
      logger.error(error)
      await ctx.reply(formatError(error))
    }
  })

  bot.action('helper:requests', showHelperRequests)

  bot.action(
    /helper:complete:(\d+)/,
    async (ctx: any) => {
      const userId = getUserId(ctx)
      const requestId = Number(ctx.match?.[1])

      if (!userId || !Number.isFinite(requestId)) {
        await ctx.reply(
          'Не удалось определить пользователя MAX или номер заявки.',
        )
        return
      }

      try {
        const result = await completeHelperRequest(
          userId,
          requestId,
        )

        await ctx.reply(
          result.detail ?? 'Заявка помощи выполнена.',
          {
            attachments: [
              mainKeyboard(),
            ],
          },
        )
      } catch (error) {
        logger.error(error)
        await ctx.reply(formatError(error))
      }
    },
  )
}
