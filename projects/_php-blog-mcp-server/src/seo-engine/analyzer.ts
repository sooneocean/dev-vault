export interface SeoScore {
  total: number;
  maxScore: number;
  breakdown: {
    title: { score: number; max: number; issues: string[]; suggestions: string[] };
    metaDescription: { score: number; max: number; issues: string[]; suggestions: string[] };
    contentStructure: { score: number; max: number; issues: string[]; suggestions: string[] };
    keywordDensity: { score: number; max: number; issues: string[]; suggestions: string[] };
    readability: { score: number; max: number; issues: string[]; suggestions: string[] };
  };
}

export interface AnalyzeInput {
  title: string;
  content: string;
  metaDescription?: string;
  focusKeyword?: string;
  language?: string;
}

function stripHtml(html: string): string {
  return html
    .replace(/<[^>]*>/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function countOccurrences(text: string, keyword: string): number {
  const escaped = keyword.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const matches = text.match(new RegExp(escaped, "gi"));
  return matches?.length ?? 0;
}

function extractHeadings(html: string): { h2: string[]; h3: string[] } {
  const h2Matches = html.match(/<h2[^>]*>(.*?)<\/h2>/gi) ?? [];
  const h3Matches = html.match(/<h3[^>]*>(.*?)<\/h3>/gi) ?? [];
  return {
    h2: h2Matches.map((h) => stripHtml(h)),
    h3: h3Matches.map((h) => stripHtml(h)),
  };
}

function analyzeTitle(title: string, keyword?: string): SeoScore["breakdown"]["title"] {
  const issues: string[] = [];
  const suggestions: string[] = [];
  let score = 20;

  const len = title.length;
  if (len < 30) {
    issues.push(`Title too short (${len} chars). Recommended: 30-60.`);
    suggestions.push("Expand the title to include more descriptive keywords.");
    score -= 8;
  } else if (len > 60) {
    issues.push(`Title too long (${len} chars). Recommended: 30-60.`);
    suggestions.push("Shorten the title to prevent truncation in SERPs.");
    score -= 5;
  }

  if (keyword) {
    const titleLower = title.toLowerCase();
    const kwLower = keyword.toLowerCase();
    if (!titleLower.includes(kwLower)) {
      issues.push("Focus keyword not found in title.");
      suggestions.push("Include the focus keyword near the beginning of the title.");
      score -= 7;
    }
  }

  return { score: Math.max(0, score), max: 20, issues, suggestions };
}

function analyzeMetaDescription(
  metaDesc: string | undefined,
  content: string,
  keyword?: string,
): SeoScore["breakdown"]["metaDescription"] {
  const issues: string[] = [];
  const suggestions: string[] = [];
  let score = 20;

  if (!metaDesc) {
    issues.push("No meta description provided.");
    suggestions.push("Add a meta description (120-160 chars) summarizing the content.");
    score -= 12;
    return { score: Math.max(0, score), max: 20, issues, suggestions };
  }

  const len = metaDesc.length;
  if (len < 120) {
    issues.push(`Meta description too short (${len} chars). Recommended: 120-160.`);
    suggestions.push("Expand the meta description to provide more context.");
    score -= 5;
  } else if (len > 160) {
    issues.push(`Meta description too long (${len} chars). Recommended: 120-160.`);
    suggestions.push("Shorten to prevent truncation in SERPs.");
    score -= 5;
  }

  if (keyword) {
    const descLower = metaDesc.toLowerCase();
    const kwLower = keyword.toLowerCase();
    if (!descLower.includes(kwLower)) {
      issues.push("Focus keyword not found in meta description.");
      suggestions.push("Include the focus keyword naturally in the meta description.");
      score -= 5;
    }
  }

  return { score: Math.max(0, score), max: 20, issues, suggestions };
}

function analyzeContentStructure(html: string): SeoScore["breakdown"]["contentStructure"] {
  const issues: string[] = [];
  const suggestions: string[] = [];
  let score = 20;

  const headings = extractHeadings(html);
  const plainText = stripHtml(html);
  const wordCount = plainText.split(/\s+/).filter(Boolean).length;

  if (headings.h2.length === 0) {
    issues.push("No H2 headings found.");
    suggestions.push("Add H2 headings to structure your content into sections.");
    score -= 7;
  }

  if (wordCount < 300) {
    issues.push(`Content is short (${wordCount} words). Recommended: 600+.`);
    suggestions.push("Add more substantive content to improve SEO value.");
    score -= 8;
  }

  const hasLists = /<[uo]l[^>]*>/i.test(html);
  if (!hasLists && wordCount > 500) {
    suggestions.push("Consider adding bullet/numbered lists to improve readability.");
    score -= 2;
  }

  return { score: Math.max(0, score), max: 20, issues, suggestions };
}

function analyzeKeywordDensity(
  html: string,
  keyword?: string,
): SeoScore["breakdown"]["keywordDensity"] {
  const issues: string[] = [];
  const suggestions: string[] = [];
  let score = 20;

  if (!keyword) {
    issues.push("No focus keyword specified.");
    suggestions.push("Set a focus keyword to analyze keyword density.");
    return { score: 10, max: 20, issues, suggestions };
  }

  const plainText = stripHtml(html).toLowerCase();
  const kwLower = keyword.toLowerCase();
  const wordCount = plainText.split(/\s+/).filter(Boolean).length;
  const occurrences = countOccurrences(plainText, kwLower);

  if (wordCount === 0) {
    return { score: 0, max: 20, issues: ["No content to analyze"], suggestions: [] };
  }

  const density = (occurrences / wordCount) * 100;

  if (occurrences === 0) {
    issues.push(`Focus keyword "${keyword}" not found in content.`);
    suggestions.push("Include the focus keyword naturally in the content.");
    score -= 15;
  } else if (density < 0.5) {
    issues.push(`Keyword density is low (${density.toFixed(2)}%). Target: 1-3%.`);
    suggestions.push("Use the focus keyword more frequently (naturally).");
    score -= 7;
  } else if (density > 3) {
    issues.push(`Keyword density is high (${density.toFixed(2)}%). Risk of keyword stuffing.`);
    suggestions.push("Reduce keyword usage to avoid over-optimization.");
    score -= 8;
  }

  return { score: Math.max(0, score), max: 20, issues, suggestions };
}

function analyzeReadability(html: string): SeoScore["breakdown"]["readability"] {
  const issues: string[] = [];
  const suggestions: string[] = [];
  let score = 20;

  const plainText = stripHtml(html);
  const sentences = plainText.split(/[.!?]+/).filter((s) => s.trim().length > 0);

  if (sentences.length === 0) {
    return { score: 0, max: 20, issues: ["No sentences detected"], suggestions: [] };
  }

  const avgSentenceLength = plainText.split(/\s+/).length / sentences.length;
  if (avgSentenceLength > 25) {
    issues.push(`Average sentence length is high (${avgSentenceLength.toFixed(0)} words). Recommended: < 20.`);
    suggestions.push("Break long sentences into shorter ones for better readability.");
    score -= 7;
  }

  const passiveMatches = plainText.match(/\b(is|are|was|were|been|being)\s+\w+ed\b/gi);
  const passiveRatio = passiveMatches ? passiveMatches.length / sentences.length : 0;
  if (passiveRatio > 0.3) {
    issues.push("High usage of passive voice detected.");
    suggestions.push("Rewrite sentences in active voice where possible.");
    score -= 5;
  }

  return { score: Math.max(0, score), max: 20, issues, suggestions };
}

export function analyzeContent(input: AnalyzeInput): SeoScore {
  const titleResult = analyzeTitle(input.title, input.focusKeyword);
  const metaResult = analyzeMetaDescription(
    input.metaDescription,
    input.content,
    input.focusKeyword,
  );
  const structureResult = analyzeContentStructure(input.content);
  const keywordResult = analyzeKeywordDensity(input.content, input.focusKeyword);
  const readabilityResult = analyzeReadability(input.content);

  const total =
    titleResult.score +
    metaResult.score +
    structureResult.score +
    keywordResult.score +
    readabilityResult.score;

  return {
    total,
    maxScore: 100,
    breakdown: {
      title: titleResult,
      metaDescription: metaResult,
      contentStructure: structureResult,
      keywordDensity: keywordResult,
      readability: readabilityResult,
    },
  };
}
