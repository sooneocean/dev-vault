export class ApiError extends Error {
  constructor(
    message: string,
    public readonly statusCode: number,
    public readonly endpoint?: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export class AuthError extends Error {
  constructor(message = "Authentication failed") {
    super(message);
    this.name = "AuthError";
  }
}

export class ValidationError extends Error {
  constructor(
    message: string,
    public readonly fields?: string[],
  ) {
    super(message);
    this.name = "ValidationError";
  }
}

export function toMcpError(error: unknown): { isError: true; content: Array<{ type: "text"; text: string }> } {
  if (error instanceof AuthError) {
    return {
      isError: true,
      content: [{ type: "text", text: `Authentication error: ${error.message}` }],
    };
  }
  if (error instanceof ApiError) {
    return {
      isError: true,
      content: [{ type: "text", text: `API error (${error.statusCode}): ${error.message}` }],
    };
  }
  if (error instanceof ValidationError) {
    return {
      isError: true,
      content: [{ type: "text", text: `Validation error: ${error.message}` }],
    };
  }
  const message = error instanceof Error ? error.message : "Unknown error";
  return {
    isError: true,
    content: [{ type: "text", text: `Error: ${message}` }],
  };
}
