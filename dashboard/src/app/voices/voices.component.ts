import { CommonModule } from '@angular/common';
import { Component, EventEmitter, OnInit, Output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../api.service';
import { Voice } from '../api.models';
import { extractErrorMessage } from '../error-utils';

@Component({
  selector: 'app-voices',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './voices.component.html',
  styleUrl: './voices.component.css',
})
export class VoicesComponent implements OnInit {
  @Output() voicesChanged = new EventEmitter<Voice[]>();

  voices = signal<Voice[]>([]);
  loading = signal(false);
  errorMessage = signal<string | null>(null);

  uploading = signal(false);
  uploadError = signal<string | null>(null);
  selectedFile: File | null = null;
  voiceId = '';
  voiceName = '';
  language = 'it';
  promptText = '';

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.refresh();
  }

  refresh(): void {
    this.loading.set(true);
    this.errorMessage.set(null);
    this.api.listVoices().subscribe({
      next: (list) => {
        this.voices.set(list.data);
        this.voicesChanged.emit(list.data);
        this.loading.set(false);
      },
      error: async (err) => {
        this.errorMessage.set(await extractErrorMessage(err));
        this.loading.set(false);
      },
    });
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.selectedFile = input.files && input.files.length > 0 ? input.files[0] : null;
  }

  createVoice(): void {
    if (!this.selectedFile) {
      this.uploadError.set('Seleziona un file audio WAV di riferimento.');
      return;
    }
    if (!this.voiceId.trim()) {
      this.uploadError.set('Inserisci un ID voce.');
      return;
    }

    this.uploading.set(true);
    this.uploadError.set(null);
    this.api
      .createVoice({
        file: this.selectedFile,
        voiceId: this.voiceId.trim(),
        name: this.voiceName.trim() || undefined,
        language: this.language.trim() || undefined,
        promptText: this.promptText.trim() || undefined,
      })
      .subscribe({
        next: () => {
          this.uploading.set(false);
          this.selectedFile = null;
          this.voiceId = '';
          this.voiceName = '';
          this.promptText = '';
          this.refresh();
        },
        error: async (err) => {
          this.uploadError.set(await extractErrorMessage(err));
          this.uploading.set(false);
        },
      });
  }

  deleteVoice(voiceId: string): void {
    if (!confirm(`Eliminare la voce "${voiceId}"?`)) return;
    this.api.deleteVoice(voiceId).subscribe({
      next: () => this.refresh(),
      error: async (err) => {
        this.errorMessage.set(await extractErrorMessage(err));
      },
    });
  }

  formatDate(unixSeconds: number): string {
    return new Date(unixSeconds * 1000).toLocaleString();
  }
}
