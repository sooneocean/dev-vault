export interface Post {
  id: number;
  date: string;
  date_gmt: string;
  modified: string;
  modified_gmt: string;
  slug: string;
  status: "publish" | "draft" | "pending" | "private" | "trash";
  type: string;
  title: { rendered: string };
  content: { rendered: string; protected: boolean };
  excerpt: { rendered: string; protected: boolean };
  author: number;
  featured_media: number;
  categories: number[];
  tags: number[];
  link?: string;
  meta: Record<string, unknown>;
  yoast_meta?: YoastMeta;
  _links?: Record<string, unknown>;
}

export interface YoastMeta {
  yoast_wpseo_title?: string;
  yoast_wpseo_metadesc?: string;
  yoast_wpseo_focuskw?: string;
}

export interface CreatePostInput {
  title: string;
  content: string;
  status?: "publish" | "draft" | "pending" | "private";
  categories?: number[];
  tags?: number[];
  date?: string;
  excerpt?: string;
  featured_media?: number;
  meta?: Record<string, unknown>;
}

export interface UpdatePostInput {
  title?: string;
  content?: string;
  status?: "publish" | "draft" | "pending" | "private" | "trash";
  categories?: number[];
  tags?: number[];
  date?: string;
  excerpt?: string;
  featured_media?: number;
  meta?: Record<string, unknown>;
}

export interface Category {
  id: number;
  count: number;
  description: string;
  link: string;
  name: string;
  slug: string;
  parent: number;
  meta: Record<string, unknown>;
}

export interface Tag {
  id: number;
  count: number;
  description: string;
  link: string;
  name: string;
  slug: string;
  meta: Record<string, unknown>;
}

export interface Media {
  id: number;
  date: string;
  slug: string;
  type: string;
  title: { rendered: string };
  author: number;
  media_type: string;
  mime_type: string;
  source_url: string;
  media_details: {
    width: number;
    height: number;
    file: string;
    sizes: Record<string, { source_url: string; width: number; height: number }>;
  };
}

export interface SiteSettings {
  title: string;
  description: string;
  url: string;
  email: string;
  timezone: string;
  date_format: string;
  time_format: string;
  language: string;
  permalink_structure: string;
}

export interface ListParams {
  page?: number;
  per_page?: number;
  search?: string;
  status?: string;
  categories?: string;
  tags?: string;
  after?: string;
  before?: string;
  orderby?: string;
  order?: "asc" | "desc";
}

export interface PaginatedResult<T> {
  items: T[];
  totalItems: number;
  totalPages: number;
  page: number;
  perPage: number;
}
