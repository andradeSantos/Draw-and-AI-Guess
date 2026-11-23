export interface HealthResponse {
  status: string;
  database: string;
  model_loaded: boolean;
  model_version: string;
}

export interface ClassInfo {
  index: number;
  label: string;
  display_pt: string;
  category: string;
}

export interface ClassesResponse {
  num_classes: number;
  classes: ClassInfo[];
  confidence_threshold: number;
  margin_threshold: number;
}

export interface TopKItem {
  label: string;
  display_name: string;
  confidence: number;
}

export interface PredictResponse {
  prediction_id: string;
  predicted_class: string;
  display_name: string;
  is_unknown: boolean;
  confidence: number;
  margin: number;
  reason: string | null;
  top_k: TopKItem[];
  latency_ms: number;
  model_version: string;
}

export interface FeedbackRequest {
  prediction_id: string;
  is_correct: boolean;
  actual_class?: string | null;
}

export interface FeedbackResponse {
  feedback_id: string;
  prediction_id: string;
  is_correct: boolean;
  actual_class: string | null;
}

export interface ConfusionPair {
  predicted_class: string;
  actual_class: string;
  count: number;
}

export interface ClassDistributionItem {
  predicted_class: string;
  count: number;
}

export interface StatsResponse {
  total_predictions: number;
  unknown_count: number;
  unknown_rate: number;
  feedback_count: number;
  accuracy_rate: number | null;
  top_confusions: ConfusionPair[];
  class_distribution: ClassDistributionItem[];
}

export interface ChatResponse {
  intent: string;
  reply: string;
  data: Record<string, unknown>;
}
