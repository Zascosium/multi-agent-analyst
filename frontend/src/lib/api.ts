export interface AnalyzeResponse {
  job_id: string;
  stream_url: string;
  report_url: string;
}

export interface StreamEvent {
  event: 'agent_start' | 'agent_output' | 'complete' | 'error';
  agent?: string;
  data?: unknown;
}

export interface Report {
  job_id: string;
  report: string;
  charts: { title: string; description: string; image_b64: string }[];
}

export async function submitAnalysis(file: File, question: string): Promise<AnalyzeResponse> {
  const form = new FormData();
  form.append('file', file);
  form.append('question', question);
  const res = await fetch('/analyze', { method: 'POST', body: form });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export function streamJob(streamUrl: string, onEvent: (e: StreamEvent) => void): () => void {
  const source = new EventSource(streamUrl);
  source.onmessage = (e) => {
    const event: StreamEvent = JSON.parse(e.data);
    onEvent(event);
    if (event.event === 'complete' || event.event === 'error') source.close();
  };
  source.onerror = () => {
    onEvent({ event: 'error', data: 'Connection lost' });
    source.close();
  };
  return () => source.close();
}

export async function fetchReport(reportUrl: string): Promise<Report> {
  const res = await fetch(reportUrl);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
