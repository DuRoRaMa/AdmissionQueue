import Fastify from 'fastify'
import { z } from 'zod'
import { config } from './config.js'
import { logger } from './logger.js'
import { sendMaxNotification } from './services/notificationService.js'

const notificationSchema = z.object({
  external_user_id: z.string().min(1),
  type: z.enum([
    'assigned',
    'called',
    'cancelled',
    'completed',
    'helper_request',
  ]),
  talon: z
    .object({
      id: z.number().int().positive(),
      name: z.string().min(1),
    })
    .optional(),
  location: z.string().nullable().optional(),
  helper_request: z
    .object({
      id: z.number().int().positive(),
      from: z.string(),
      theme: z.string(),
      priority: z.string(),
      text: z.string(),
      created_at: z.string(),
    })
    .optional(),
}).superRefine((value, ctx) => {
  if (value.type === 'helper_request' && !value.helper_request) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      path: ['helper_request'],
      message: 'Для helper_request требуется helper_request.',
    })
  }

  if (value.type !== 'helper_request' && !value.talon) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      path: ['talon'],
      message: 'Для уведомления по талону требуется talon.',
    })
  }
})

export async function startInternalServer(): Promise<void> {
  const app = Fastify({
    logger: false,
  })

  app.get('/health/', async () => ({
    status: 'ok',
  }))

  app.post(
    '/internal/notifications/',
    async (request, reply) => {
      const token = request.headers[
        'x-internal-token'
      ]

      if (
        typeof token !== 'string' ||
        token !== config.MAX_BOT_SERVICE_TOKEN
      ) {
        return reply.code(403).send({
          detail: 'Недействительный внутренний токен.',
        })
      }

      const parsed = notificationSchema.safeParse(
        request.body,
      )

      if (!parsed.success) {
        return reply.code(400).send({
          detail: 'Некорректные данные уведомления.',
          errors: parsed.error.flatten(),
        })
      }

      try {
        await sendMaxNotification(parsed.data as any)
      } catch (error) {
        logger.error(
          {
            error,
            payload: parsed.data,
          },
          'MAX notification failed',
        )

        return reply.code(502).send({
          detail: 'Не удалось отправить уведомление MAX.',
        })
      }

      return reply.code(200).send({
        status: 'sent',
      })
    },
  )

  await app.listen({
    host: config.MAX_BOT_HTTP_HOST,
    port: config.MAX_BOT_HTTP_PORT,
  })

  logger.info(
    {
      host: config.MAX_BOT_HTTP_HOST,
      port: config.MAX_BOT_HTTP_PORT,
    },
    'MAX internal HTTP server started',
  )
}