function stripHtml(html: string): string {
  return html.replace(/<[^>]*>/g, " ").replace(/\s+/g, " ").trim();
}

function truncate(text: string, maxLen: number): string {
  if (text.length <= maxLen) return text;
  return text.slice(0, maxLen - 3).trimEnd() + "...";
}

function extractFirstSentence(text: string): string {
  const plain = stripHtml(text);
  const match = plain.match(/^[^.!?]*[.!?]/);
  return (match?.[0] ?? plain.slice(0, 200)).trim();
}

export interface GeneratedMeta {
  title: string;
  description: string;
  ogTitle: string;
  ogDescription: string;
  ogType: string;
  twitterCard: string;
  twitterTitle: string;
  twitterDescription: string;
}

export function generateMeta(
  title: string,
  content: string,
  focusKeyword?: string,
  siteName?: string,
): GeneratedMeta {
  const plainContent = stripHtml(content);

  // Generate meta title (30-60 chars)
  let metaTitle = title;
  if (siteName) {
    const withSite = `${title} | ${siteName}`;
    metaTitle = withSite.length <= 60 ? withSite : truncate(title, 55);
  }
  if (metaTitle.length < 30 && focusKeyword) {
    metaTitle = `${focusKeyword}: ${metaTitle}`;
  }
  metaTitle = truncate(metaTitle, 60);

  // Generate meta description (120-160 chars)
  let description = extractFirstSentence(content);
  if (description.length < 120) {
    const secondSentence = plainContent.slice(description.length).match(/[^.!?]*[.!?]/)?.[0];
    if (secondSentence) {
      description = (description + " " + secondSentence.trim()).trim();
    }
  }
  if (focusKeyword && !description.toLowerCase().includes(focusKeyword.toLowerCase())) {
    description = `${focusKeyword} - ${description}`;
  }
  description = truncate(description, 160);

  return {
    title: metaTitle,
    description,
    ogTitle: metaTitle,
    ogDescription: description,
    ogType: "article",
    twitterCard: "summary_large_image",
    twitterTitle: metaTitle,
    twitterDescription: description,
  };
}
