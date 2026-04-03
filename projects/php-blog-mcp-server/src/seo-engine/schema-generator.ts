import type { Post } from "../types.js";

export interface SitemapEntry {
  loc: string;
  lastmod: string;
  changefreq: "always" | "hourly" | "daily" | "weekly" | "monthly" | "yearly" | "never";
  priority: number;
}

export function generateSitemapXml(baseUrl: string, posts: Post[]): string {
  const entries: SitemapEntry[] = posts.map((post) => ({
    loc: post.link ?? `${baseUrl}/${post.slug}`,
    lastmod: post.modified_gmt ?? post.date_gmt,
    changefreq: "weekly" as const,
    priority: post.status === "publish" ? 0.8 : 0.4,
  }));

  const xmlEntries = entries
    .map(
      (e) => `  <url>
    <loc>${escapeXml(e.loc)}</loc>
    <lastmod>${e.lastmod}</lastmod>
    <changefreq>${e.changefreq}</changefreq>
    <priority>${e.priority}</priority>
  </url>`,
    )
    .join("\n");

  return `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${xmlEntries}
</urlset>`;
}

function escapeXml(str: string): string {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
}

export interface ArticleSchema {
  "@context": "https://schema.org";
  "@type": "Article";
  headline: string;
  datePublished: string;
  dateModified: string;
  author: {
    "@type": "Person" | "Organization";
    name: string;
  };
  publisher?: {
    "@type": "Organization";
    name: string;
    logo?: { "@type": "ImageObject"; url: string };
  };
  description?: string;
  image?: string;
  mainEntityOfPage?: {
    "@type": "WebPage";
    "@id": string;
  };
}

export function generateArticleSchema(
  post: Post,
  baseUrl: string,
  authorName?: string,
  siteName?: string,
): ArticleSchema {
  const schema: ArticleSchema = {
    "@context": "https://schema.org",
    "@type": "Article",
    headline: post.title.rendered,
    datePublished: post.date,
    dateModified: post.modified,
    author: {
      "@type": authorName ? "Person" : "Organization",
      name: authorName ?? siteName ?? "Admin",
    },
    mainEntityOfPage: {
      "@type": "WebPage",
      "@id": post.link ?? `${baseUrl}/${post.slug}`,
    },
  };

  if (siteName) {
    schema.publisher = {
      "@type": "Organization",
      name: siteName,
    };
  }

  const plainExcerpt = post.excerpt?.rendered?.replace(/<[^>]*>/g, "").trim();
  if (plainExcerpt) {
    schema.description = plainExcerpt.slice(0, 200);
  }

  return schema;
}
