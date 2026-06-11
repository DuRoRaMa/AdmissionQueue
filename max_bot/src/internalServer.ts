import Fastify from 'fastify';
import { z } from 'zod';

import { config } from './config.js';
import { logger } from './logger.js';
import { sendMaxNotification } from './services/notificationService.js';

const notificationSchema = z.object({
  external_user_id: z.string().min(1),
  type: z.enum([
    'assigned',
    'cancelled',
    'completed',
  ]),
  talon: z.object({
    id: z.number().int().positive(),
    name: z.string().min(1),
  }),
  location: z.string().nullable().optional(),
});

export async function startInternalServer(): Promise<void> {
  const app = Fastify({
    logger: false,
  });

  app.get('/health/', async () => ({
    status: 'ok',
  }));

  app.post(
    '/internal/notifications/',
    async (request, reply) => {
      const token = request.headers[
        'x-internal-token'
      ];

      if (
        typeof token !== 'string' ||
        token !== config.MAX_BOT_SERVICE_TOKEN
      ) {
        return reply.code(403).send({
          detail: 'Недействительный внутренний токен.',
        });
      }

      const parsed = notificationSchema.safeParse(
        request.body,
      );

      if (!parsed.success) {
        return reply.code(400).send({
          detail: 'Некорректные данные уведомления.',
          errors: parsed.error.flatten(),
        });
      }

      try {
        await sendMaxNotification(parsed.data);
      } catch (error) {
        logger.error(
          {
            error,
            payload: parsed.data,
          },
          'MAX notification failed',
        );

        return reply.code(502).send({
          detail: 'Не удалось отправить уведомление MAX.',
        });
      }

      return reply.code(200).send({
        status: 'sent',
      });
    },
  );

  await app.listen({
    host: config.MAX_BOT_HTTP_HOST,
    port: config.MAX_BOT_HTTP_PORT,
  });

  logger.info(
    {
      host: config.MAX_BOT_HTTP_HOST,
      port: config.MAX_BOT_HTTP_PORT,
    },
    'MAX internal HTTP server started',
  );
}
