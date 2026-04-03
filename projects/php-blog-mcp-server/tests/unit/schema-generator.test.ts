import { describe, it, expect } from "vitest";
import {
  generateSitemapXml,
  generateArticleSchema,
} from "../../src/seo-engine/schema-generator.js";
import type { Post } from "../../src/types.js";

function makePost(overrides: Partial<Post> = {}): Post {
  return {
    id: 1,
    date: "2026-01-15T10:00:00",
    date_gmt: "2026-01-15T10:00:00",
    modified: "2026-03-01T12:00:00",
    modified_gmt: "2026-03-01T12:00:00",
    slug: "test-post",
    status: "publish",
    type: "post",
    title: { rendered: "Test Post Title" },
    content: { rendered: "<p>Test content</p>", protected: false },
    excerpt: { rendered: "<p>Test excerpt</p>", protected: false },
    author: 1,
    featured_media: 0,
    categories: [1],
    tags: [],
    meta: {},
    link: "https://example.com/test-post",
    ...overrides,
  };
}

describe("generateSitemapXml", () => {
  it("should generate valid XML structure", () => {
    const xml = generateSitemapXml("https://example.com", [makePost()]);
    expect(xml).toContain('<?xml version="1.0" encoding="UTF-8"?>');
    expect(xml).toContain("<urlset");
    expect(xml).toContain("</urlset>");
  });

  it("should include post URLs", () => {
    const xml = generateSitemapXml("https://example.com", [makePost()]);
    expect(xml).toContain("https://example.com/test-post");
  });

  it("should include lastmod dates", () => {
    const xml = generateSitemapXml("https://example.com", [makePost()]);
    expect(xml).toContain("2026-03-01T12:00:00");
  });

  it("should handle multiple posts", () => {
    const posts = [
      makePost({ id: 1, slug: "post-1", link: "https://example.com/post-1" }),
      makePost({ id: 2, slug: "post-2", link: "https://example.com/post-2" }),
    ];
    const xml = generateSitemapXml("https://example.com", posts);
    expect(xml).toContain("post-1");
    expect(xml).toContain("post-2");
  });

  it("should escape XML special characters", () => {
    const post = makePost({
      link: "https://example.com/post?a=1&b=2",
    });
    const xml = generateSitemapXml("https://example.com", [post]);
    expect(xml).toContain("&amp;");
  });
});

describe("generateArticleSchema", () => {
  it("should generate valid JSON-LD structure", () => {
    const schema = generateArticleSchema(makePost(), "https://example.com");
    expect(schema["@context"]).toBe("https://schema.org");
    expect(schema["@type"]).toBe("Article");
  });

  it("should include headline from post title", () => {
    const schema = generateArticleSchema(makePost(), "https://example.com");
    expect(schema.headline).toBe("Test Post Title");
  });

  it("should include dates", () => {
    const schema = generateArticleSchema(makePost(), "https://example.com");
    expect(schema.datePublished).toBe("2026-01-15T10:00:00");
    expect(schema.dateModified).toBe("2026-03-01T12:00:00");
  });

  it("should use author name when provided", () => {
    const schema = generateArticleSchema(
      makePost(),
      "https://example.com",
      "John Doe",
    );
    expect(schema.author.name).toBe("John Doe");
    expect(schema.author["@type"]).toBe("Person");
  });

  it("should include publisher when site name provided", () => {
    const schema = generateArticleSchema(
      makePost(),
      "https://example.com",
      undefined,
      "My Blog",
    );
    expect(schema.publisher?.name).toBe("My Blog");
  });

  it("should include mainEntityOfPage", () => {
    const schema = generateArticleSchema(makePost(), "https://example.com");
    expect(schema.mainEntityOfPage?.["@id"]).toBe(
      "https://example.com/test-post",
    );
  });
});
