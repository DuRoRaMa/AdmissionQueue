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
  return ctx.user?.user_id ?? null
}

function getMessageText(ctx: any): string {
  return String(ctx.message?.body?.text ?? '').trim()
}

function formatError(error: any): string {
  return (
    error?.response?.data?.detail ??
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
    return
  }

  try {
    const requests = await getHelperRequests(userId)

    if (requests.length === 0) {
      await ctx.reply(
        'Активных заявок помощи нет.',
        {
          attachments: [
            mainKeyboard(),
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

export function registerHelperHandlers(bot: Bot) {
  bot.command('link', async (ctx: any) => {
    const userId = getUserId(ctx)

    if (!userId) {
      return
    }

    const text = getMessageText(ctx)
    const code = text.replace(/^\/link\s*/i, '').trim().toUpperCase()

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
  })

  bot.command('helper', showHelperMenu)

  bot.action('helper:menu', showHelperMenu)

  bot.action('helper:toggle', async (ctx: any) => {
    const userId = getUserId(ctx)

    if (!userId) {
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