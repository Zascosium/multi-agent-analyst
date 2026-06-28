<script lang="ts">
  import '../app.css';
  let { children } = $props();
</script>

<div class="min-h-screen bg-surface-50 font-sans">
  {@render children()}
</div>
