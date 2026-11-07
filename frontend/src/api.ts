export type ArtStyle = { id: number; name: string; kind: "style" | "category" | "theme" };
export type Artwork = {
  id: string;
  title: string;
  description: string;
  original_filename: string;
  mime_type: string;
  byte_size: number;
  created_at: string;
  styles: ArtStyle[];
  image_url: string;
};
export type CommissionService = {
  id: number;
  name: string;
  description: string;
  price_min: string;
  price_max: string;
  currency: string;
  active: boolean;
  created_at: string;
};
export type Health = { status: string; service: string };
export type MonitorStatus = { api_configured: boolean; api_approved: boolean; can_scan: boolean; message: string };
export type Subreddit = { id: number; name: string; active: boolean; priority: number; poll_interval_minutes: number; max_posts_per_check: number; include_keywords: string[]; exclude_keywords: string[]; created_at: string };
export type MonitoredPost = { id: number; reddit_id: string; subreddit_id: number; title: string; body: string; permalink: string; created_utc: string; fetched_at: string };
export type SearchRun = { id: number; subreddit_id: number; status: string; posts_fetched: number; posts_matched: number; message: string; started_at: string; finished_at: string | null };
export type AIStatus = {
  base_url: string;
  reachable: boolean;
  model_configured: boolean;
  configured_model: string | null;
  model_installed: boolean;
  embedding_model_configured: boolean;
  configured_embedding_model: string | null;
  embedding_model_installed: boolean;
  available_models: { name: string; size_bytes: number | null; parameter_size: string | null; quantization: string | null }[];
  message: string;
};
export type ArtworkAnalysis = {
  id: number;
  artwork_id: string;
  model: string;
  prompt_version: string;
  result: {
    visual_description: string;
    styles: string[];
    themes: string[];
    subjects: string[];
    composition: string;
    color_palette: string[];
    complexity: number;
    confidence: number;
    uncertainties: string[];
  };
  created_at: string;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `/api/v1${path}`;
  const response = init ? await fetch(url, init) : await fetch(url);
  if (!response.ok) {
    let message = `Falha na solicitação (${response.status})`;
    try {
      const body = await response.json();
      message = body.detail ?? message;
    } catch { /* A resposta pode não conter JSON. */ }
    throw new Error(message);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const getApiHealth = () => request<Health>("/health");
export const getMonitorStatus = () => request<MonitorStatus>("/monitor/status");
export const listSubreddits = () => request<Subreddit[]>("/monitor/subreddits");
export const listMonitoredPosts = () => request<MonitoredPost[]>("/monitor/posts?limit=50");
export const listSearchRuns = () => request<SearchRun[]>("/monitor/runs?limit=20");
export const createSubreddit = (value: Pick<Subreddit, "name" | "include_keywords" | "exclude_keywords">) => request<Subreddit>("/monitor/subreddits", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(value) });
export const deleteSubreddit = (id: number) => request<void>(`/monitor/subreddits/${id}`, { method: "DELETE" });
export const scanSubreddit = (id: number) => request<SearchRun>(`/monitor/subreddits/${id}/scan`, { method: "POST" });
export const getAIStatus = () => request<AIStatus>("/ai/status");
export const analyzeArtwork = (id: string) => request<ArtworkAnalysis>(`/ai/artworks/${id}/analyze`, { method: "POST" });
export const getArtworkAnalyses = (id: string) => request<ArtworkAnalysis[]>(`/ai/artworks/${id}/analyses`);
export const embedText = (text: string) => request<{ model: string; dimensions: number; embedding: number[] }>("/ai/embed", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ text }) });
export const listArtworks = () => request<Artwork[]>("/profile/artworks");
export const listStyles = () => request<ArtStyle[]>("/profile/styles");
export const listServices = () => request<CommissionService[]>("/profile/services");
export const createStyle = (value: Pick<ArtStyle, "name" | "kind">) => request<ArtStyle>("/profile/styles", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(value) });
export const deleteStyle = (id: number) => request<void>(`/profile/styles/${id}`, { method: "DELETE" });
export const createService = (value: Omit<CommissionService, "id" | "created_at">) => request<CommissionService>("/profile/services", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(value) });
export const updateService = (id: number, value: Omit<CommissionService, "id" | "created_at">) => request<CommissionService>(`/profile/services/${id}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify(value) });
export const deleteService = (id: number) => request<void>(`/profile/services/${id}`, { method: "DELETE" });
export const updateArtwork = (id: string, value: { title: string; description: string; style_ids: number[] }) => request<Artwork>(`/profile/artworks/${id}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify(value) });
export const deleteArtwork = (id: string) => request<void>(`/profile/artworks/${id}`, { method: "DELETE" });

export async function uploadArtwork(file: File, title: string, description: string, styleIds: number[]) {
  const body = new FormData();
  body.append("image", file);
  body.append("title", title);
  body.append("description", description);
  styleIds.forEach((id) => body.append("style_ids", String(id)));
  return request<Artwork>("/profile/artworks", { method: "POST", body });
}
