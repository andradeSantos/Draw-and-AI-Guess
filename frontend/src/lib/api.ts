import type {
  ChatResponse,
  ClassesResponse,
  FeedbackRequest,
  FeedbackResponse,
  HealthResponse,
  PredictResponse,
  StatsResponse,
} from "./types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "http://localhost:8000";

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });

  if (!response.ok) {
    let detail = `Erro HTTP ${response.status}`;
    try {
      const errBody = (await response.json()) as { detail?: string };
      if (errBody.detail) {
        detail = errBody.detail;
      }
    } catch {
      // Mantém mensagem padrão quando o corpo não é JSON
    }
    throw new ApiError(detail, response.status);
  }

  return (await response.json()) as T;
}

export function getHealth(): Promise<HealthResponse> {
  return requestJson<HealthResponse>("/health", { cache: "no-store" });
}

export function getClasses(): Promise<ClassesResponse> {
  return requestJson<ClassesResponse>("/classes");
}

export function predictDrawing(imageBase64: string): Promise<PredictResponse> {
  return requestJson<PredictResponse>("/predict", {
    method: "POST",
    body: JSON.stringify({ image_base64: imageBase64, source: "live_canvas" }),
  });
}

export function submitFeedback(payload: FeedbackRequest): Promise<FeedbackResponse> {
  return requestJson<FeedbackResponse>("/feedback", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getStats(): Promise<StatsResponse> {
  return requestJson<StatsResponse>("/stats", { cache: "no-store" });
}

export function sendChatMessage(message: string): Promise<ChatResponse> {
  return requestJson<ChatResponse>("/chat", {
    method: "POST",
    body: JSON.stringify({ message }),
  });
}
