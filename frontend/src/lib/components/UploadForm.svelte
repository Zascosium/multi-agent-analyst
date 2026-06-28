<script lang="ts">
  let {
    status,
    onsubmit,
  }: {
    status: 'idle' | 'uploading' | 'running' | 'complete' | 'error';
    onsubmit: (file: File, question: string) => void;
  } = $props();

  let file = $state<File | null>(null);
  let question = $state('Give me a comprehensive analysis of this dataset.');
  let isDragging = $state(false);
  let fileInputRef = $state<HTMLInputElement | null>(null);

  function handleDragOver(e: DragEvent) {
    e.preventDefault();
    isDragging = true;
  }

  function handleDragLeave() {
    isDragging = false;
  }

  function handleDrop(e: DragEvent) {
    e.preventDefault();
    isDragging = false;
    const dropped = e.dataTransfer?.files[0];
    if (dropped?.name.endsWith('.csv')) file = dropped;
  }

  function handleFileInput(e: Event) {
    const input = e.target as HTMLInputElement;
    file = input.files?.[0] ?? null;
  }

  function handleSubmit() {
    if (file) onsubmit(file, question);
  }
</script>

<div class="space-y-6 max-w-xl">
  <!-- Drop zone -->
  <!-- svelte-ignore a11y_interactive_supports_focus -->
  <div
    role="button"
    aria-label="Upload CSV file"
    class="relative border-2 border-dashed rounded-xl p-10 flex flex-col items-center justify-center gap-3 cursor-pointer transition-colors duration-200 {isDragging
      ? 'border-brand-500 bg-brand-50'
      : file
        ? 'border-green-400 bg-green-50'
        : 'border-surface-200 bg-white hover:border-brand-400 hover:bg-brand-50'}"
    ondragover={handleDragOver}
    ondragleave={handleDragLeave}
    ondrop={handleDrop}
    onclick={() => fileInputRef?.click()}
    onkeydown={(e) => e.key === 'Enter' && fileInputRef?.click()}
  >
    {#if file}
      <!-- File selected icon -->
      <svg class="w-10 h-10 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
          d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <p class="text-sm font-semibold text-green-700">{file.name}</p>
      <p class="text-xs text-green-600">{(file.size / 1024).toFixed(1)} KB · CSV ready</p>
    {:else}
      <!-- Upload icon -->
      <svg class="w-10 h-10 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
          d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
      </svg>
      <p class="text-sm font-medium text-slate-600">
        Drop your CSV here, or <span class="text-brand-600 font-semibold">browse</span>
      </p>
      <p class="text-xs text-slate-400">CSV files only</p>
    {/if}

    <input
      bind:this={fileInputRef}
      type="file"
      accept=".csv"
      class="sr-only"
      onchange={handleFileInput}
    />
  </div>

  <!-- Question textarea -->
  <div class="space-y-1.5">
    <label for="question" class="block text-sm font-semibold text-slate-700">
      Analysis question or goal
    </label>
    <textarea
      id="question"
      rows="3"
      bind:value={question}
      class="w-full rounded-lg border border-surface-200 bg-white px-3 py-2.5 text-sm text-slate-700 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent resize-none transition"
      placeholder="Describe what you want to learn from this dataset…"
    ></textarea>
  </div>

  <!-- Submit button -->
  <button
    type="button"
    disabled={!file || status === 'uploading'}
    onclick={handleSubmit}
    class="inline-flex items-center gap-2 px-6 py-2.5 rounded-lg text-sm font-semibold bg-brand-600 text-white hover:bg-brand-700 active:bg-brand-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-150 shadow-sm"
  >
    {#if status === 'uploading'}
      <span class="w-4 h-4 border-2 border-white border-t-transparent rounded-full spinner"></span>
      Uploading…
    {:else}
      <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5m0 0l-5 5m5-5H6" />
      </svg>
      Analyze Dataset
    {/if}
  </button>
</div>
