import { HttpClient } from '@angular/common/http';
import { Injectable, signal } from '@angular/core';
import { Observable } from 'rxjs';
import {
  CreateSpeechRequest,
  HealthStatus,
  ModelList,
  TranscriptionResponse,
  VoiceCreateResponse,
  VoiceList,
} from './api.models';

const STORAGE_KEY = 'fishs2_api_base_url';
const DEFAULT_BASE_URL = 'http://localhost:8020';

@Injectable({ providedIn: 'root' })
export class ApiService {
  readonly baseUrl = signal(localStorage.getItem(STORAGE_KEY) || DEFAULT_BASE_URL);

  constructor(private http: HttpClient) {}

  setBaseUrl(url: string): void {
    const trimmed = url.trim().replace(/\/+$/, '');
    this.baseUrl.set(trimmed || DEFAULT_BASE_URL);
    localStorage.setItem(STORAGE_KEY, this.baseUrl());
  }

  health(): Observable<HealthStatus> {
    return this.http.get<HealthStatus>(`${this.baseUrl()}/health`);
  }

  listModels(): Observable<ModelList> {
    return this.http.get<ModelList>(`${this.baseUrl()}/v1/models`);
  }

  listVoices(): Observable<VoiceList> {
    return this.http.get<VoiceList>(`${this.baseUrl()}/v1/audio/voices`);
  }

  createVoice(options: {
    file: File;
    voiceId: string;
    name?: string;
    language?: string;
    promptText?: string;
  }): Observable<VoiceCreateResponse> {
    const form = new FormData();
    form.append('audio_sample', options.file);
    form.append('voice_id', options.voiceId);
    if (options.name) form.append('name', options.name);
    if (options.language) form.append('language', options.language);
    if (options.promptText) form.append('prompt_text', options.promptText);
    return this.http.post<VoiceCreateResponse>(`${this.baseUrl()}/v1/audio/voices`, form);
  }

  transcribe(file: File, language?: string): Observable<TranscriptionResponse> {
    const form = new FormData();
    form.append('file', file);
    if (language) form.append('language', language);
    return this.http.post<TranscriptionResponse>(`${this.baseUrl()}/v1/audio/transcriptions`, form);
  }

  deleteVoice(voiceId: string): Observable<unknown> {
    return this.http.delete(`${this.baseUrl()}/v1/audio/voices/${encodeURIComponent(voiceId)}`);
  }

  generateSpeech(request: CreateSpeechRequest): Observable<Blob> {
    return this.http.post(`${this.baseUrl()}/v1/audio/speech`, request, {
      responseType: 'blob',
    });
  }
}
