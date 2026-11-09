// Single place to change the backend URL. Override with VITE_API_BASE_URL at build time.
export const API_BASE_URL: string =
  (import.meta.env["VITE_API_BASE_URL"] as string | undefined) ?? "http://127.0.0.1:8000";

export type Lang = "en" | "hi" | "or";
export interface Source { source: string; publisher: string; url: string; publication_date: string }
export interface ChatResponse {
  response: string; language: string; intent: string; is_emergency: boolean;
  risk_level: string | null; sources: Source[]; disclaimer: string; provider_used: string | null;
}
export interface RiskRequest {
  age_group: string; symptoms: string[]; duration_days?: number | undefined; temperature_celsius?: number | undefined;
  existing_conditions?: string[] | undefined; pregnant?: boolean | undefined;
}
export interface RiskResponse {
  risk_level: "low" | "moderate" | "high"; factors_considered: string[]; recommendation: string; disclaimer: string;
}
export type Verdict = "supported" | "misleading" | "unsupported" | "false" | "insufficient_evidence";
export interface MisinfoResponse { claim: string; verdict: Verdict; explanation: string; sources: Source[] }

export class ApiError extends Error {}

async function request<T>(path: string, body?: unknown): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, {
      method: body ? "POST" : "GET",
      headers: body ? { "Content-Type": "application/json" } : {},
      body: body ? JSON.stringify(body) : null,
    });
  } catch {
    throw new ApiError("unreachable");
  }
  if (!res.ok) throw new ApiError(`status_${res.status}`);
  return res.json() as Promise<T>;
}

export const api = {
  chat: (message: string, language: Lang, session_id?: string) =>
    request<ChatResponse>("/chat", { message, language, session_id }),
  risk: (b: RiskRequest) => request<RiskResponse>("/risk-assessment", b),
  misinfo: (claim: string) => request<MisinfoResponse>("/misinformation-check", { claim }),
  diseases: () => request<{ diseases: string[]; count: number }>("/diseases"),
  resources: () => request<{ message: string; official_links: { name: string; url: string }[] }>("/health-resources"),
  sources: () => request<{ trusted_sources: { name: string; url: string }[] }>("/sources"),
};
