type LogLevel = "debug" | "info" | "warn" | "error";

const LEVEL_ORDER: Record<LogLevel, number> = {
  debug: 0,
  info: 1,
  warn: 2,
  error: 3,
};

let currentLevel: LogLevel = "info";

export function setLogLevel(level: LogLevel): void {
  currentLevel = level;
}

function shouldLog(level: LogLevel): boolean {
  return LEVEL_ORDER[level] >= LEVEL_ORDER[currentLevel];
}

function formatMessage(
  level: LogLevel,
  message: string,
  context?: Record<string, unknown>,
): string {
  const entry: Record<string, unknown> = {
    timestamp: new Date().toISOString(),
    level,
    message,
    ...context,
  };
  return JSON.stringify(entry);
}

export const logger = {
  debug(message: string, context?: Record<string, unknown>): void {
    if (shouldLog("debug")) {
      process.stderr.write(formatMessage("debug", message, context) + "\n");
    }
  },
  info(message: string, context?: Record<string, unknown>): void {
    if (shouldLog("info")) {
      process.stderr.write(formatMessage("info", message, context) + "\n");
    }
  },
  warn(message: string, context?: Record<string, unknown>): void {
    if (shouldLog("warn")) {
      process.stderr.write(formatMessage("warn", message, context) + "\n");
    }
  },
  error(message: string, context?: Record<string, unknown>): void {
    if (shouldLog("error")) {
      process.stderr.write(formatMessage("error", message, context) + "\n");
    }
  },
};
