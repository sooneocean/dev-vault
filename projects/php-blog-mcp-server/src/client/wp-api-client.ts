import axios, { type AxiosInstance, type AxiosResponse } from "axios";
import type {
  Post,
  CreatePostInput,
  UpdatePostInput,
  Category,
  Tag,
  Media,
  SiteSettings,
  ListParams,
  PaginatedResult,
} from "../types.js";
import { ApiError, AuthError } from "../utils/errors.js";
import { logger } from "../utils/logger.js";

export interface WpClientConfig {
  baseUrl: string;
  username: string;
  appPassword: string;
  maxRetries?: number;
  timeoutMs?: number;
}

export class WpApiClient {
  private http: AxiosInstance;

  constructor(private config: WpClientConfig) {
    this.http = axios.create({
      baseURL: `${config.baseUrl.replace(/\/$/, "")}/wp-json/wp/v2`,
      timeout: config.timeoutMs ?? 10000,
      auth: {
        username: config.username,
        password: config.appPassword,
      },
      headers: {
        "Content-Type": "application/json",
      },
    });

    this.http.interceptors.response.use(
      (response) => response,
      (error) => {
        if (axios.isAxiosError(error)) {
          const status = error.response?.status;
          if (status === 401 || status === 403) {
            throw new AuthError(
              `Authentication failed (${status}): ${error.response?.data?.message ?? "Unauthorized"}`,
            );
          }
          if (status) {
            throw new ApiError(
              error.response?.data?.message ?? error.message,
              status,
              error.config?.url,
            );
          }
          throw new ApiError(`Network error: ${error.message}`, 0);
        }
        throw error;
      },
    );

    this.http.interceptors.request.use((config) => {
      logger.debug("WP API request", {
        method: config.method,
        url: config.url,
      });
      return config;
    });
  }

  // --- Posts ---

  async listPosts(
    params?: ListParams,
  ): Promise<PaginatedResult<Post>> {
    const response = await this.http.get<Post[]>("/posts", { params });
    return this.wrapPaginated(response);
  }

  async getPost(id: number): Promise<Post> {
    const response = await this.http.get<Post>(`/posts/${id}`);
    return response.data;
  }

  async createPost(data: CreatePostInput): Promise<Post> {
    const response = await this.http.post<Post>("/posts", data);
    return response.data;
  }

  async updatePost(id: number, data: UpdatePostInput): Promise<Post> {
    const response = await this.http.put<Post>(`/posts/${id}`, data);
    return response.data;
  }

  async deletePost(id: number, force = false): Promise<{ deleted: boolean; previous: Post }> {
    const response = await this.http.delete(`/posts/${id}`, {
      params: { force },
    });
    return response.data;
  }

  // --- Pages ---

  async listPages(params?: ListParams): Promise<PaginatedResult<Post>> {
    const response = await this.http.get<Post[]>("/pages", { params });
    return this.wrapPaginated(response);
  }

  // --- Categories ---

  async listCategories(params?: ListParams): Promise<PaginatedResult<Category>> {
    const response = await this.http.get<Category[]>("/categories", { params });
    return this.wrapPaginated(response);
  }

  async createCategory(data: { name: string; slug?: string; parent?: number; description?: string }): Promise<Category> {
    const response = await this.http.post<Category>("/categories", data);
    return response.data;
  }

  async updateCategory(id: number, data: Partial<{ name: string; slug: string; parent: number; description: string }>): Promise<Category> {
    const response = await this.http.put<Category>(`/categories/${id}`, data);
    return response.data;
  }

  async deleteCategory(id: number): Promise<void> {
    await this.http.delete(`/categories/${id}`);
  }

  // --- Tags ---

  async listTags(params?: ListParams): Promise<PaginatedResult<Tag>> {
    const response = await this.http.get<Tag[]>("/tags", { params });
    return this.wrapPaginated(response);
  }

  async createTag(data: { name: string; slug?: string; description?: string }): Promise<Tag> {
    const response = await this.http.post<Tag>("/tags", data);
    return response.data;
  }

  async updateTag(id: number, data: Partial<{ name: string; slug: string; description: string }>): Promise<Tag> {
    const response = await this.http.put<Tag>(`/tags/${id}`, data);
    return response.data;
  }

  async deleteTag(id: number): Promise<void> {
    await this.http.delete(`/tags/${id}`);
  }

  // --- Media ---

  async listMedia(params?: ListParams): Promise<PaginatedResult<Media>> {
    const response = await this.http.get<Media[]>("/media", { params });
    return this.wrapPaginated(response);
  }

  async uploadMedia(file: Buffer, filename: string, mimeType?: string): Promise<Media> {
    const response = await this.http.post<Media>("/media", file, {
      headers: {
        "Content-Type": mimeType ?? "application/octet-stream",
        "Content-Disposition": `attachment; filename="${filename}"`,
      },
    });
    return response.data;
  }

  async deleteMedia(id: number, force = true): Promise<void> {
    await this.http.delete(`/media/${id}`, { params: { force } });
  }

  // --- Settings ---

  async getSettings(): Promise<SiteSettings> {
    const response = await this.http.get<SiteSettings>("/settings");
    return response.data;
  }

  async updateSettings(data: Partial<SiteSettings>): Promise<SiteSettings> {
    const response = await this.http.put<SiteSettings>("/settings", data);
    return response.data;
  }

  // --- Helpers ---

  private wrapPaginated<T>(response: AxiosResponse<T[]>): PaginatedResult<T> {
    const totalItems = parseInt(response.headers["x-wp-total"] ?? "0", 10);
    const totalPages = parseInt(response.headers["x-wp-totalpages"] ?? "0", 10);
    const page = parseInt(
      new URL(response.config.url ?? "", "http://localhost").searchParams.get("page") ?? "1",
      10,
    );
    const perPage = parseInt(
      new URL(response.config.url ?? "", "http://localhost").searchParams.get("per_page") ?? "10",
      10,
    );
    return {
      items: response.data,
      totalItems,
      totalPages,
      page,
      perPage,
    };
  }
}
