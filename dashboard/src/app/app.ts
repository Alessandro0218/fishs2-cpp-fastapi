import { CommonModule } from '@angular/common';
import { Component, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ApiService } from './api.service';
import { HealthStatus, Voice } from './api.models';
import { VoicesComponent } from './voices/voices.component';
import { SpeechComponent } from './speech/speech.component';

type Tab = 'speech' | 'voices';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, FormsModule, VoicesComponent, SpeechComponent],
  templateUrl: './app.html',
  styleUrl: './app.css',
})
export class App implements OnInit {
  activeTab = signal<Tab>('speech');
  baseUrlInput = '';
  health = signal<HealthStatus | null>(null);
  healthError = signal<string | null>(null);
  voices = signal<Voice[]>([]);

  constructor(protected api: ApiService) {
    this.baseUrlInput = api.baseUrl();
  }

  ngOnInit(): void {
    this.checkHealth();
  }

  setTab(tab: Tab): void {
    this.activeTab.set(tab);
  }

  applyBaseUrl(): void {
    this.api.setBaseUrl(this.baseUrlInput);
    this.checkHealth();
  }

  checkHealth(): void {
    this.healthError.set(null);
    this.api.health().subscribe({
      next: (status) => this.health.set(status),
      error: () => {
        this.health.set(null);
        this.healthError.set('Server non raggiungibile a questo indirizzo.');
      },
    });
  }

  onVoicesChanged(voices: Voice[]): void {
    this.voices.set(voices);
  }
}
