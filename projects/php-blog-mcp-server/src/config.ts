import { config } from "dotenv";
import { z } from "zod";

config();

const envSchema = z.object({
  WP_BASE_URL: z.string().url(),
  WP_USERNAME: z.string().min(1),
  WP_APP_PASSWORD: z.string().min(1),
  LOG_LEVEL: z.enum(["debug", "info", "warn", "error"]).default("info"),
  MAX_RETRIES: z.coerce.number().int().min(0).max(10).default(3),
  REQUEST_TIMEOUT_MS: z.coerce.number().int().min(1000).default(10000),
  DEFAULT_LANGUAGE: z.string().default("zh-TW"),
  SITEMAP_PING_GOOGLE: z.coerce.boolean().default(false),
});

export type Config = z.infer<typeof envSchema>;

let _config: Config | null = null;

export function getConfig(): Config {
  if (!_config) {
    const result = envSchema.safeParse(process.env);
    if (!result.success) {
      const errors = result.error.issues
        .map((i) => `  ${i.path.join(".")}: ${i.message}`)
        .join("\n");
      throw new Error(`Invalid environment configuration:\n${errors}`);
    }
    _config = result.data;
  }
  return _config;
}
