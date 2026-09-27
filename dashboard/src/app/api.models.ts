export interface OpenAIModel {
  id: string;
  object: string;
  created: number;
  owned_by: string;
}

export interface ModelList {
  object: string;
  data: OpenAIModel[];
}

export interface VoiceFile {
  filename: string;
  size: number;
}

export interface Voice {
  voice_id: string;
  object: string;
  files: VoiceFile[];
  created: number;
  model: string | null;
  language: string | null;
  prompt_text: string | null;
}

export interface VoiceList {
  object: string;
  data: Voice[];
}

export interface VoiceCreateResponse {
  id: string;
  object: string;
  model: string | null;
  language: string | null;
  sample_count: number;
  created: number;
}

export interface FishS2Params {
  max_new_tokens?: number | null;
  temperature?: number | null;
  top_p?: number | null;
  top_k?: number | null;
  min_tokens_before_end?: number | null;
  n_threads?: number | null;
  verbose?: boolean | null;
}

export interface CreateSpeechRequest {
  model: string;
  input: string;
  voice: string;
  response_format: string;
  speed: number;
  fishs2?: FishS2Params | null;
  prompt_text?: string | null;
}

export interface HealthStatus {
  status: string;
  version: string;
  model_count: number;
  voice_count: number;
  backend: string;
  gpu_device: number | null;
}

export interface ApiErrorBody {
  error: {
    message: string;
    type: string;
    param?: string | null;
    code?: string | null;
  };
}
