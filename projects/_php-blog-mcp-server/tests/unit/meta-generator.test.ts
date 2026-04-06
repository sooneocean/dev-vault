import { describe, it, expect } from "vitest";
import { generateMeta } from "../../src/seo-engine/meta-generator.js";

describe("generateMeta", () => {
  const title = "Understanding SEO: A Complete Guide";
  const content = `<p>SEO is the practice of optimizing websites for search engines. Good SEO practices can significantly improve your website's visibility and organic traffic.</p>
<p>This comprehensive guide covers on-page optimization, technical SEO, and content strategy for beginners and professionals alike.</p>`;

  it("should generate meta title within 60 chars", () => {
    const meta = generateMeta(title, content);
    expect(meta.title.length).toBeLessThanOrEqual(60);
  });

  it("should generate meta description within 160 chars", () => {
    const meta = generateMeta(title, content);
    expect(meta.description.length).toBeLessThanOrEqual(160);
  });

  it("should include site name in title", () => {
    const meta = generateMeta(title, content, undefined, "MyBlog");
    expect(meta.title).toContain("MyBlog");
  });

  it("should truncate long title with site name", () => {
    const longTitle = "A Very Long Article Title That Will Definitely Exceed The Limit";
    const meta = generateMeta(longTitle, content, undefined, "MyBlog");
    expect(meta.title.length).toBeLessThanOrEqual(60);
  });

  it("should include focus keyword when provided", () => {
    const meta = generateMeta(title, content, "SEO optimization");
    const descLower = meta.description.toLowerCase();
    expect(
      descLower.includes("seo") || descLower.includes("seo optimization"),
    ).toBe(true);
  });

  it("should set Open Graph properties", () => {
    const meta = generateMeta(title, content);
    expect(meta.ogTitle).toBeTruthy();
    expect(meta.ogDescription).toBeTruthy();
    expect(meta.ogType).toBe("article");
  });

  it("should set Twitter Card properties", () => {
    const meta = generateMeta(title, content);
    expect(meta.twitterCard).toBe("summary_large_image");
    expect(meta.twitterTitle).toBeTruthy();
    expect(meta.twitterDescription).toBeTruthy();
  });

  it("should handle empty content gracefully", () => {
    const meta = generateMeta(title, "");
    expect(meta.title).toBeTruthy();
  });
});
