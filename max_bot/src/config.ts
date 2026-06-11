import 'dotenv/config';
import { z } from 'zod';

const schema = z.object({
  MAX_BOT_TOKEN: z.string().min(1),
  DJANGO_API_URL: z.string().url(),
  DJANGO_INTERNAL_TOKEN: z.string().min(16),
  REDIS_URL: z.string().min(1),
  LOG_LEVEL: z.string().default('info'),
  MAX_BOT_HTTP_HOST: z.string().default('0.0.0.0'),
  MAX_BOT_HTTP_PORT: z.coerce.number().int().min(1).max(65535).default(3000),
  MAX_BOT_SERVICE_TOKEN: z.string().min(16),
});

const parsed = schema.safeParse(process.env);

if (!parsed.success) {
  console.error(parsed.error.flatten().fieldErrors);
  process.exit(1);
}

export const config = parsed.data;
