<script lang="ts">
  import type { StreamEvent } from '$lib/api';

  let { events }: { events: StreamEvent[] } = $props();

  const STAGES = [
    {
      key: 'orchestrator',
      label: 'Orchestrator',
      subtitle: 'Planning analysis',
      colorClass: 'text-violet-600',
      bgClass: 'bg-violet-100',
      borderClass: 'border-violet-300',
      logColor: 'text-violet-400',
    },
    {
      key: 'analyst',
      label: 'Analyst',
      subtitle: 'Running code',
      colorClass: 'text-cyan-600',
      bgClass: 'bg-cyan-100',
      borderClass: 'border-cyan-300',
      logColor: 'text-cyan-400',
    },
    {
      key: 'visualizer',
      label: 'Visualizer',
      subtitle: 'Generating charts',
      colorClass: 'text-emerald-600',
      bgClass: 'bg-emerald-100',
      borderClass: 'border-emerald-300',
      logColor: 'text-emerald-400',
    },
    {
      key: 'writer',
      label: 'Writer',
      subtitle: 'Writing report',
      colorClass: 'text-amber-600',
      bgClass: 'bg-amber-100',
      borderClass: 'border-amber-300',
      logColor: 'text-amber-400',
    },
  ] as const;

  const startedAgents = $derived(
    new Set(events.filter((e) => e.event === 'agent_start').map((e) => e.agent))
  );

  const activeAgent = $derived(
    events.filter((e) => e.event === 'agent_start').at(-1)?.agent ?? null
  );

  const isComplete = $derived(events.some((e) => e.event === 'complete'));

  function stageStatus(key: string): 'pending' | 'active' | 'done' {
    if (!startedAgents.has(key)) return 'pending';
    if (isComplete) return 'done';
    const stageIdx = STAGES.findIndex((s) => s.key === key);
    const activeIdx = STAGES.findIndex((s) => s.key === activeAgent);
    if (stageIdx < activeIdx) return 'done';
    if (stageIdx === activeIdx) return 'active';
    return 'pending';
  }

  function logColor(agent?: string): string {
    return STAGES.find((s) => s.key === agent)?.logColor ?? 'text-slate-400';
  }
</script>

<div class="space-y-6">
  <!-- Pipeline progress -->
  <div class="relative px-4">
    <!-- Connector line -->
    <div class="absolute top-5 left-14 right-14 h-0.5 bg-surface-200"></div>

    <ol class="relative flex justify-between">
      {#each STAGES as stage, i}
        {@const st = stageStatus(stage.key)}
        <li class="flex flex-col items-center gap-2 flex-1">
          <div
            class="w-10 h-10 rounded-full flex items-center justify-center border-2 transition-all duration-500 z-10 {st ===
            'done'
              ? 'bg-green-500 border-green-500'
              : st === 'active'
                ? stage.bgClass + ' ' + stage.borderClass
                : 'bg-white border-surface-200'}"
          >
            {#if st === 'done'}
              <svg class="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7" />
              </svg>
            {:else if st === 'active'}
              <div class="w-4 h-4 border-2 {stage.borderClass} border-t-transparent rounded-full spinner"></div>
            {:else}
              <span class="text-xs font-semibold text-slate-400">{i + 1}</span>
            {/if}
          </div>

          <div class="text-center">
            <p class="text-xs font-semibold {st === 'pending' ? 'text-slate-400' : stage.colorClass}">
              {stage.label}
            </p>
            <p class="text-xs text-slate-400">{stage.subtitle}</p>
          </div>
        </li>
      {/each}
    </ol>
  </div>

  <!-- Terminal log -->
  <div class="bg-slate-900 rounded-xl p-4 h-44 overflow-y-auto font-mono text-xs space-y-1">
    {#each events as ev}
      {#if ev.event === 'agent_start'}
        <p class="text-slate-300">
          <span class="text-slate-500 select-none">▶ </span>
          <span class="{logColor(ev.agent)} font-semibold">[{ev.agent}]</span>
          <span class="text-slate-400"> started</span>
        </p>
      {:else if ev.event === 'agent_output' && ev.data}
        <p class="text-slate-500 pl-4 truncate">{String(ev.data)}</p>
      {:else if ev.event === 'complete'}
        <p class="text-green-400 font-semibold">✓ Analysis complete</p>
      {/if}
    {/each}
    {#if !isComplete}
      <p class="text-slate-600"><span class="blink">_</span></p>
    {/if}
  </div>
</div>
