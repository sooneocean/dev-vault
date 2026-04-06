import { describe, it, expect } from "vitest";
import { analyzeContent } from "../../src/seo-engine/analyzer.js";

describe("analyzeContent", () => {
  const baseInput = {
    title: "Understanding SEO: A Complete Guide for Beginners",
    content: `<h2>What is SEO?</h2>
<p>SEO stands for Search Engine Optimization. It is the practice of optimizing your website to rank higher in search engine results. Good SEO practices help increase organic traffic.</p>
<h2>Why SEO Matters</h2>
<p>SEO is essential for any website that wants to be found online. Without proper SEO, your content may never reach its intended audience. Search engines use complex algorithms to determine rankings.</p>
<h3>On-Page SEO</h3>
<p>On-page SEO includes optimizing title tags, meta descriptions, headings, and content quality. Each page should target a specific keyword naturally.</p>
<h3>Off-Page SEO</h3>
<p>Off-page SEO involves building backlinks and establishing authority. External signals help search engines trust your content.</p>`,
    metaDescription:
      "Learn the fundamentals of SEO including on-page and off-page optimization techniques. This complete guide covers everything beginners need to know about search engine optimization.",
    focusKeyword: "SEO",
  };

  it("should return a score between 0 and 100", () => {
    const result = analyzeContent(baseInput);
    expect(result.total).toBeGreaterThanOrEqual(0);
    expect(result.total).toBeLessThanOrEqual(100);
    expect(result.maxScore).toBe(100);
  });

  it("should have 5 breakdown dimensions", () => {
    const result = analyzeContent(baseInput);
    expect(result.breakdown).toHaveProperty("title");
    expect(result.breakdown).toHaveProperty("metaDescription");
    expect(result.breakdown).toHaveProperty("contentStructure");
    expect(result.breakdown).toHaveProperty("keywordDensity");
    expect(result.breakdown).toHaveProperty("readability");
  });

  it("should penalize short titles", () => {
    const result = analyzeContent({ ...baseInput, title: "SEO" });
    expect(result.breakdown.title.score).toBeLessThan(20);
    expect(result.breakdown.title.issues.length).toBeGreaterThan(0);
  });

  it("should penalize long titles", () => {
    const result = analyzeContent({
      ...baseInput,
      title:
        "Understanding SEO: A Complete and Comprehensive Guide for Absolute Beginners Who Want to Learn Everything About Search Engine Optimization",
    });
    expect(result.breakdown.title.score).toBeLessThan(20);
  });

  it("should penalize missing meta description", () => {
    const result = analyzeContent({ ...baseInput, metaDescription: undefined });
    expect(result.breakdown.metaDescription.score).toBeLessThan(20);
    expect(result.breakdown.metaDescription.issues).toContain(
      "No meta description provided.",
    );
  });

  it("should detect missing focus keyword in title", () => {
    const result = analyzeContent({
      ...baseInput,
      title: "A Complete Guide for Beginners",
    });
    expect(result.breakdown.title.issues).toContain(
      "Focus keyword not found in title.",
    );
  });

  it("should penalize low keyword density", () => {
    const result = analyzeContent({
      ...baseInput,
      focusKeyword: "nonexistentkeyword",
    });
    expect(result.breakdown.keywordDensity.score).toBeLessThan(20);
  });

  it("should detect missing H2 headings", () => {
    const result = analyzeContent({
      ...baseInput,
      content: "<p>Just plain text without any headings at all.</p>",
    });
    expect(result.breakdown.contentStructure.issues).toContain(
      "No H2 headings found.",
    );
  });

  it("should penalize very short content", () => {
    const result = analyzeContent({
      ...baseInput,
      content: "<p>Short content.</p>",
    });
    expect(result.breakdown.contentStructure.score).toBeLessThan(20);
  });

  it("should handle missing focus keyword gracefully", () => {
    const result = analyzeContent({
      title: baseInput.title,
      content: baseInput.content,
    });
    expect(result.breakdown.keywordDensity.score).toBe(10);
    expect(result.breakdown.keywordDensity.issues).toContain(
      "No focus keyword specified.",
    );
  });

  it("should give high score for well-optimized content", () => {
    const result = analyzeContent(baseInput);
    expect(result.total).toBeGreaterThan(60);
  });
});
