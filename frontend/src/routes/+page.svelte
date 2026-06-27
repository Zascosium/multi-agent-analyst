<script lang="ts">
  import { fetchReport, streamJob, submitAnalysis, type Report, type StreamEvent } from '$lib/api';

  let file: File | null = null;
  let question = 'Give me a comprehensive analysis of this dataset.';
  let status: 'idle' | 'uploading' | 'running' | 'complete' | 'error' = 'idle';
  let events: StreamEvent[] = [];
  let report: Report | null = null;
  let errorMsg = '';

  function handleFile(e: Event) {
    const input = e.target as HTMLInputElement;
    file = input.files?.[0] ?? null;
  }

  async function handleSubmit() {
    if (!file) return;
    status = 'uploading';
    events = [];
    report = null;
    errorMsg = '';

    try {
      const { stream_url, report_url } = await submitAnalysis(file, question);
      status = 'running';

      await new Promise<void>((resolve) => {
        streamJob(stream_url, (event) => {
          events = [...events, event];
          if (event.event === 'complete') resolve();
          if (event.event === 'error') {
            errorMsg = String(event.data ?? 'Unknown error');
            status = 'error';
            resolve();
          }
        });
      });

      if (status !== 'error') {
        report = await fetchReport(report_url);
        status = 'complete';
      }
    } catch (err) {
      errorMsg = String(err);
      status = 'error';
    }
  }

  function agentLabel(agent?: string) {
    const labels: Record<string, string> = {
      orchestrator: 'Orchestrator planning analysis...',
      analyst: 'Analyst writing & executing code...',
      visualizer: 'Visualizer generating charts...',
      writer: 'Writer synthesizing report...',
    };
    return agent ? (labels[agent] ?? agent) : '';
  }
</script>

<main>
  <header>
    <h1>Multi-Agent Data Analyst</h1>
    <p>Upload a CSV. A crew of LLM agents will analyze it and produce a report.</p>
  </header>

  {#if status === 'idle' || status === 'uploading'}
    <section class="upload-form">
      <label>
        CSV file
        <input type="file" accept=".csv" on:change={handleFile} />
      </label>
      <label>
        Question / goal
        <textarea rows="3" bind:value={question}></textarea>
      </label>
      <button disabled={!file || status === 'uploading'} on:click={handleSubmit}>
        {status === 'uploading' ? 'Uploading…' : 'Analyze'}
      </button>
    </section>
  {/if}

  {#if status === 'running'}
    <section class="activity">
      <h2>Agents at work</h2>
      <ul>
        {#each events as ev}
          {#if ev.event === 'agent_start'}
            <li class="agent-step">{agentLabel(ev.agent)}</li>
          {/if}
        {/each}
      </ul>
      <div class="spinner" aria-label="Working…"></div>
    </section>
  {/if}

  {#if status === 'error'}
    <section class="error">
      <h2>Error</h2>
      <pre>{errorMsg}</pre>
      <button on:click={() => (status = 'idle')}>Try again</button>
    </section>
  {/if}

  {#if status === 'complete' && report}
    <section class="report">
      <h2>Analysis Report</h2>
      {#if report.charts.length}
        <div class="charts">
          {#each report.charts as chart}
            <figure>
              <img src="data:image/png;base64,{chart.image_b64}" alt={chart.title} />
              <figcaption>{chart.title} — {chart.description}</figcaption>
            </figure>
          {/each}
        </div>
      {/if}
      <div class="report-body">
        <pre>{report.report}</pre>
      </div>
      <button on:click={() => (status = 'idle')}>Analyze another file</button>
    </section>
  {/if}
</main>

<style>
  main {
    max-width: 860px;
    margin: 0 auto;
    padding: 2rem 1rem;
    font-family: system-ui, sans-serif;
  }
  header { margin-bottom: 2rem; }
  h1 { font-size: 1.8rem; margin: 0 0 0.4rem; }
  header p { color: #555; }

  .upload-form { display: flex; flex-direction: column; gap: 1rem; max-width: 540px; }
  label { display: flex; flex-direction: column; gap: 0.25rem; font-weight: 600; }
  input[type="file"], textarea { font-size: 1rem; padding: 0.4rem; border: 1px solid #ccc; border-radius: 4px; }
  button {
    padding: 0.6rem 1.4rem;
    background: #1a73e8;
    color: #fff;
    border: none;
    border-radius: 6px;
    font-size: 1rem;
    cursor: pointer;
    width: fit-content;
  }
  button:disabled { opacity: 0.5; cursor: not-allowed; }

  .activity { margin-top: 2rem; }
  .agent-step { margin: 0.4rem 0; color: #333; }
  .spinner {
    width: 2rem; height: 2rem;
    border: 3px solid #ddd;
    border-top-color: #1a73e8;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
    margin-top: 1rem;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  .error pre { background: #fee; padding: 1rem; border-radius: 4px; color: #c00; }

  .charts { display: flex; flex-wrap: wrap; gap: 1rem; margin: 1.5rem 0; }
  figure { margin: 0; }
  figure img { max-width: 400px; border: 1px solid #eee; border-radius: 6px; }
  figcaption { font-size: 0.8rem; color: #666; margin-top: 0.25rem; }

  .report-body pre {
    white-space: pre-wrap;
    background: #f8f8f8;
    padding: 1.5rem;
    border-radius: 6px;
    font-size: 0.9rem;
    line-height: 1.6;
  }
</style>
