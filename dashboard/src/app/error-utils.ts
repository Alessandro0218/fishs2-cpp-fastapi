import { HttpErrorResponse } from '@angular/common/http';

export async function extractErrorMessage(err: unknown): Promise<string> {
  if (err instanceof HttpErrorResponse) {
    const body = err.error;
    if (body instanceof Blob) {
      try {
        const text = await body.text();
        const parsed = JSON.parse(text);
        if (parsed?.error?.message) return parsed.error.message;
        return text;
      } catch {
        return err.message;
      }
    }
    if (body?.error?.message) return body.error.message;
    if (typeof body === 'string' && body) return body;
    return err.message || `Errore HTTP ${err.status}`;
  }
  if (err instanceof Error) return err.message;
  return String(err);
}
