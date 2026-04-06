import { describe, it, expect } from "vitest";
import { ApiError, AuthError, ValidationError, toMcpError } from "../../src/utils/errors.js";

describe("Error classes", () => {
  it("ApiError should have correct properties", () => {
    const err = new ApiError("Not found", 404, "/posts/999");
    expect(err.name).toBe("ApiError");
    expect(err.statusCode).toBe(404);
    expect(err.endpoint).toBe("/posts/999");
    expect(err.message).toBe("Not found");
  });

  it("AuthError should have default message", () => {
    const err = new AuthError();
    expect(err.name).toBe("AuthError");
    expect(err.message).toBe("Authentication failed");
  });

  it("AuthError should accept custom message", () => {
    const err = new AuthError("Token expired");
    expect(err.message).toBe("Token expired");
  });

  it("ValidationError should have fields", () => {
    const err = new ValidationError("Invalid input", ["title", "content"]);
    expect(err.name).toBe("ValidationError");
    expect(err.fields).toEqual(["title", "content"]);
  });
});

describe("toMcpError", () => {
  it("should handle AuthError", () => {
    const result = toMcpError(new AuthError("Bad creds"));
    expect(result.isError).toBe(true);
    expect(result.content[0].text).toContain("Authentication error");
    expect(result.content[0].text).toContain("Bad creds");
  });

  it("should handle ApiError", () => {
    const result = toMcpError(new ApiError("Not found", 404));
    expect(result.isError).toBe(true);
    expect(result.content[0].text).toContain("API error (404)");
  });

  it("should handle ValidationError", () => {
    const result = toMcpError(new ValidationError("Bad field", ["title"]));
    expect(result.isError).toBe(true);
    expect(result.content[0].text).toContain("Validation error");
  });

  it("should handle generic Error", () => {
    const result = toMcpError(new Error("Something broke"));
    expect(result.isError).toBe(true);
    expect(result.content[0].text).toContain("Something broke");
  });

  it("should handle non-Error values", () => {
    const result = toMcpError("string error");
    expect(result.isError).toBe(true);
    expect(result.content[0].text).toContain("Unknown error");
  });
});
