import { CommonModule } from '@angular/common';
import { Component, Input, OnChanges, OnDestroy, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../api.service';
import { Voice } from '../api.models';
import { extractErrorMessage } from '../error-utils';

@Component({
  selector: 'app-speech',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './speech.component.html',
  styleUrl: './speech.component.css',
})
export class SpeechComponent implements OnChanges, OnDestroy {
  @Input() voices: Voice[] = [];

  model = 'fishaudio/s2-pro';
  voiceId = 'default';
  inputText = '';
  speed = 1.0;

  advancedOpen = false;
  maxNewTokens: number | null = null;
  temperature: number | null = null;
  topP: number | null = null;
  topK: number | null = null;

  generating = signal(false);
  errorMessage = signal<string | null>(null);
  audioUrl = signal<string | null>(null);
  audioFileName = signal<string>('output.mp3');

  constructor(private api: ApiService) {}

  ngOnChanges(): void {
    if (this.voiceId !== 'default' && !this.voices.some((v) => v.voice_id === this.voiceId)) {
      this.voiceId = 'default';
    }
  }

  ngOnDestroy(): void {
    this.revokeCurrentUrl();
  }

  private revokeCurrentUrl(): void {
    const current = this.audioUrl();
    if (current) URL.revokeObjectURL(current);
  }

  generate(): void {
    if (!this.inputText.trim()) {
      this.errorMessage.set('Inserisci il testo da far pronunciare.');
      return;
    }

    this.generating.set(true);
    this.errorMessage.set(null);

    const fishs2 =
      this.maxNewTokens != null || this.temperature != null || this.topP != null || this.topK != null
        ? {
            max_new_tokens: this.maxNewTokens ?? undefined,
            temperature: this.temperature ?? undefined,
            top_p: this.topP ?? undefined,
            top_k: this.topK ?? undefined,
          }
        : undefined;

    this.api
      .generateSpeech({
        model: this.model.trim(),
        input: this.inputText.trim(),
        voice: this.voiceId.trim() || 'default',
        response_format: 'mp3',
        speed: this.speed,
        fishs2,
      })
      .subscribe({
        next: (blob) => {
          this.revokeCurrentUrl();
          this.audioUrl.set(URL.createObjectURL(blob));
          this.audioFileName.set(`${this.voiceId || 'speech'}_${Date.now()}.mp3`);
          this.generating.set(false);
        },
        error: async (err) => {
          this.errorMessage.set(await extractErrorMessage(err));
          this.generating.set(false);
        },
      });
  }
}
