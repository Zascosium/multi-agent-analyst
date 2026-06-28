<script lang="ts">
  import { fetchReport, streamJob, submitAnalysis, type Report, type StreamEvent } from '$lib/api';
  import UploadForm from '$lib/components/UploadForm.svelte';
  import AgentPipeline from '$lib/components/AgentPipeline.svelte';
  import ReportView from '$lib/components/ReportView.svelte';

  let status = $state<'idle' | 'uploading' | 'running' | 'complete' | 'error'>('idle');
  let events = $state<StreamEvent[]>([]);
  let report = $state<Report | null>(null);
  let errorMsg = $state('');

  async function handleSubmit(file: File, question: string) {
    status = 'uploading';
    events = [];
    report = null;
    errorMsg = '';

    try {
      const { stream_url, report_url } = await submitAnalysis(file, question);
      status = 'running';
      let streamFailed = false;

      await new Promise<void>((resolve) => {
        streamJob(stream_url, (event) => {
          events = [...events, event];
          if (event.event === 'complete') resolve();
          if (event.event === 'error') {
            errorMsg = String(event.data ?? 'Unknown error');
            status = 'error';
            streamFailed = true;
            resolve();
          }
        });
      });

      if (!streamFailed) {
        report = await fetchReport(report_url);
        status = 'complete';
      }
    } catch (err) {
      errorMsg = String(err);
      status = 'error';
    }
  }

  function reset() {
    status = 'idle';
    events = [];
    report = null;
    errorMsg = '';
  }
</script>

<div class="max-w-5xl mx-auto px-4 py-10 space-y-8">
  <!-- Header -->
  <header class="flex items-start gap-4">
    <div class="w-10 h-10 rounded-xl bg-brand-600 flex items-center justify-center shadow-sm flex-shrink-0 mt-0.5">
      <svg class="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
          d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
    </div>
    <div>
      <h1 class="text-2xl font-bold text-slate-900 tracking-tight">Multi-Agent Data Analyst</h1>
      <p class="text-slate-500 text-sm mt-0.5">
        Upload a CSV — a crew of LLM agents will analyze it and produce a full report with charts.
      </p>
    </div>
  </header>

  <!-- Upload form -->
  {#if status === 'idle' || status === 'uploading'}
    <section class="bg-white rounded-2xl border border-surface-200 shadow-sm p-6 sm:p-8">
      <h2 class="text-base font-semibold text-slate-700 mb-6">Upload your data</h2>
      <UploadForm {status} onsubmit={handleSubmit} />
    </section>
  {/if}

  <!-- Agent pipeline -->
  {#if status === 'running'}
    <section class="bg-white rounded-2xl border border-surface-200 shadow-sm p-6 sm:p-8">
      <h2 class="text-base font-semibold text-slate-700 mb-6">Agents at work</h2>
      <AgentPipeline {events} />
    </section>
  {/if}

  <!-- Error -->
  {#if status === 'error'}
    <section class="bg-red-50 border border-red-200 rounded-2xl p-6 space-y-4">
      <div class="flex items-start gap-3">
        <div class="w-8 h-8 rounded-full bg-red-100 flex items-center justify-center flex-shrink-0">
          <svg class="w-4 h-4 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <div class="space-y-1 min-w-0">
          <h2 class="font-semibold text-red-800">Analysis failed</h2>
          <p class="text-sm text-red-700 font-mono break-all">{errorMsg}</p>
        </div>
      </div>
      <button
        onclick={reset}
        class="inline-flex items-center gap-2 px-4 py-2 bg-white border border-red-300 text-red-700 rounded-lg text-sm font-semibold hover:bg-red-50 transition"
      >
        <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        Try again
      </button>
    </section>
  {/if}

  <!-- Results -->
  {#if status === 'complete' && report}
    <section class="space-y-4">
      <div class="flex items-center justify-between">
        <h2 class="text-xl font-bold text-slate-900">Analysis Report</h2>
        <button
          onclick={reset}
          class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm text-slate-600 border border-surface-200 hover:bg-surface-100 transition"
        >
          <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Analyze another file
        </button>
      </div>

      <div class="bg-white rounded-2xl border border-surface-200 shadow-sm p-6 sm:p-8">
        <ReportView {report} />
      </div>
    </section>
  {/if}
</div>
