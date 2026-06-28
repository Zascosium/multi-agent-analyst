<script lang="ts">
  import { marked } from 'marked';
  import type { Report } from '$lib/api';

  let { report }: { report: Report } = $props();

  function renderReport(md: string, charts: Report['charts']): string {
    // Replace ![alt](chart:N) references with inline HTML figures
    const withCharts = md.replace(
      /!\[([^\]]*)\]\(chart:(\d+)\)/g,
      (_, alt: string, idxStr: string) => {
        const idx = parseInt(idxStr, 10);
        const chart = charts[idx];
        if (!chart) return '';
        return `<figure class="my-6 text-center">
  <img src="data:image/png;base64,${chart.image_b64}" alt="${chart.title}"
       style="max-width:100%;border-radius:0.5rem;border:1px solid #e2e8f0;box-shadow:0 1px 3px rgba(0,0,0,.08);" />
  <figcaption style="margin-top:0.5rem;font-size:0.8rem;color:#64748b;">${chart.title} — ${chart.description}</figcaption>
</figure>`;
      }
    );
    return marked.parse(withCharts, { async: false }) as string;
  }

  const renderedHtml = $derived(renderReport(report.report, report.charts));

  const gridCols = $derived(
    report.charts.length === 1
      ? 'grid-cols-1'
      : report.charts.length === 2
        ? 'grid-cols-1 sm:grid-cols-2'
        : 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3'
  );
</script>

<div class="space-y-8">
  <!-- Chart gallery -->
  {#if report.charts.length > 0}
    <section>
      <h3 class="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-4 flex items-center gap-2">
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
        Charts ({report.charts.length})
      </h3>
      <div class="grid gap-4 {gridCols}">
        {#each report.charts as chart}
          <figure class="bg-white rounded-xl border border-surface-200 shadow-sm overflow-hidden m-0">
            <img
              src="data:image/png;base64,{chart.image_b64}"
              alt={chart.title}
              class="w-full object-contain max-h-72"
            />
            <figcaption class="px-4 py-3 border-t border-surface-100">
              <p class="text-sm font-semibold text-slate-700">{chart.title}</p>
              <p class="text-xs text-slate-500 mt-0.5">{chart.description}</p>
            </figcaption>
          </figure>
        {/each}
      </div>
    </section>
  {/if}

  <!-- Rendered markdown report -->
  <section>
    <h3 class="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-4 flex items-center gap-2">
      <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
          d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
      Full Report
    </h3>
    <article class="prose max-w-none">
      {@html renderedHtml}
    </article>
  </section>
</div>
