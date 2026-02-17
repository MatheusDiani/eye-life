<script lang="ts">
  import "../app.css";
  import { onMount } from "svelte";
  import { theme, themes, type ThemeName } from "$lib/stores/theme";
  import { settingsAPI } from "$lib/api/client";

  let { children } = $props();
  let showThemeMenu = $state(false);
  let carryoverEnabled = $state(false);

  onMount(async () => {
    theme.init();
    // Load carryover setting
    try {
      const settings = await settingsAPI.get();
      carryoverEnabled = settings.carryover_enabled;
    } catch (e) {
      // Silently fail
    }
  });

  function selectTheme(themeName: ThemeName) {
    theme.setTheme(themeName);
    showThemeMenu = false;
  }

  function toggleThemeMenu() {
    showThemeMenu = !showThemeMenu;
  }

  function closeThemeMenu(e: MouseEvent) {
    const target = e.target as HTMLElement;
    if (!target.closest(".settings-container")) {
      showThemeMenu = false;
    }
  }

  async function toggleCarryover() {
    carryoverEnabled = !carryoverEnabled;
    try {
      await settingsAPI.update({ carryover_enabled: carryoverEnabled });
    } catch (e) {
      carryoverEnabled = !carryoverEnabled; // Revert on error
    }
  }
</script>

<svelte:window onclick={closeThemeMenu} />

<div class="app-container">
  <nav class="sidebar">
    <div class="logo">
      <span class="logo-icon">◉</span>
      <span class="logo-text">Eye Life</span>
    </div>

    <ul class="nav-links">
      <li>
        <a href="/" class="nav-link">
          <span class="nav-icon">📊</span>
          <span>Início</span>
        </a>
      </li>
      <li>
        <a href="/habits" class="nav-link">
          <span class="nav-icon">✓</span>
          <span>Hábitos</span>
        </a>
      </li>
      <li>
        <a href="/notes" class="nav-link">
          <span class="nav-icon">📝</span>
          <span>Notas</span>
        </a>
      </li>
      <li>
        <a href="/stats" class="nav-link">
          <span class="nav-icon">📈</span>
          <span>Estatísticas</span>
        </a>
      </li>
    </ul>

    <div class="sidebar-footer">
      <p class="text-muted text-center footer-date">
        {new Date().toLocaleDateString("pt-BR", {
          weekday: "long",
          day: "numeric",
          month: "long",
        })}
      </p>

      <!-- Settings Button -->
      <div class="settings-container">
        <button
          class="settings-btn"
          onclick={toggleThemeMenu}
          title="Configurações"
        >
          ⚙️
        </button>

        {#if showThemeMenu}
          <div class="theme-menu animate-slide-up">
            <h4>Tema</h4>
            <div class="theme-options">
              {#each themes as t}
                <button
                  class="theme-option"
                  class:active={$theme === t.name}
                  onclick={() => selectTheme(t.name)}
                >
                  <span class="theme-emoji">{t.emoji}</span>
                  <span class="theme-label">{t.label}</span>
                  {#if $theme === t.name}
                    <span class="theme-check">✓</span>
                  {/if}
                </button>
              {/each}
            </div>

            <hr class="settings-divider" />

            <h4>Cronômetro</h4>
            <label class="toggle-option">
              <span class="toggle-label">Repassar tempo excedente</span>
              <button
                class="toggle-switch"
                class:active={carryoverEnabled}
                onclick={toggleCarryover}
              >
                <span class="toggle-slider"></span>
              </button>
            </label>
            <p class="toggle-hint">
              Tempo além do estimado é creditado no próximo dia
            </p>
          </div>
        {/if}
      </div>
    </div>
  </nav>

  <main class="main-content">
    {@render children()}
  </main>
</div>

<style>
  .app-container {
    display: flex;
    min-height: 100vh;
  }

  .sidebar {
    width: 240px;
    background-color: var(--color-surface);
    border-right: 1px solid var(--color-border);
    padding: var(--spacing-6);
    display: flex;
    flex-direction: column;
    position: fixed;
    height: 100vh;
  }

  .logo {
    display: flex;
    align-items: center;
    gap: var(--spacing-3);
    margin-bottom: var(--spacing-8);
  }

  .logo-icon {
    font-size: var(--font-size-2xl);
    color: var(--color-text-primary);
  }

  .logo-text {
    font-size: var(--font-size-xl);
    font-weight: var(--font-weight-bold);
    color: var(--color-text-primary);
    letter-spacing: -0.02em;
  }

  .nav-links {
    list-style: none;
    display: flex;
    flex-direction: column;
    gap: var(--spacing-2);
    flex: 1;
  }

  .nav-link {
    display: flex;
    align-items: center;
    gap: var(--spacing-3);
    padding: var(--spacing-3) var(--spacing-4);
    border-radius: var(--radius-md);
    color: var(--color-text-secondary);
    transition: all var(--transition-fast);
    font-weight: var(--font-weight-medium);
  }

  .nav-link:hover {
    background-color: var(--color-surface-hover);
    color: var(--color-text-primary);
  }

  .nav-icon {
    font-size: var(--font-size-lg);
    width: 24px;
    text-align: center;
  }

  .sidebar-footer {
    padding-top: var(--spacing-4);
    border-top: 1px solid var(--color-border);
  }

  .footer-date {
    font-size: var(--font-size-xs);
    margin-bottom: var(--spacing-3);
  }

  /* Settings Button & Theme Menu */
  .settings-container {
    position: relative;
  }

  .settings-btn {
    width: 100%;
    padding: var(--spacing-3);
    background-color: var(--color-surface-hover);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    font-size: var(--font-size-lg);
    cursor: pointer;
    transition: all var(--transition-fast);
  }

  .settings-btn:hover {
    border-color: var(--color-text-muted);
    transform: rotate(90deg);
  }

  .theme-menu {
    position: absolute;
    bottom: 100%;
    left: 0;
    right: 0;
    margin-bottom: var(--spacing-2);
    background-color: var(--color-surface-elevated);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-lg);
    padding: var(--spacing-4);
    box-shadow: var(--shadow-lg);
    z-index: var(--z-dropdown);
  }

  .theme-menu h4 {
    font-size: var(--font-size-sm);
    color: var(--color-text-muted);
    margin-bottom: var(--spacing-3);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .theme-options {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-1);
  }

  .theme-option {
    display: flex;
    align-items: center;
    gap: var(--spacing-3);
    padding: var(--spacing-2) var(--spacing-3);
    background: none;
    border: none;
    border-radius: var(--radius-md);
    cursor: pointer;
    transition: all var(--transition-fast);
    color: var(--color-text-secondary);
    text-align: left;
    width: 100%;
  }

  .theme-option:hover {
    background-color: var(--color-surface-hover);
    color: var(--color-text-primary);
  }

  .theme-option.active {
    background-color: var(--color-accent);
    color: var(--color-bg);
  }

  .theme-emoji {
    font-size: var(--font-size-lg);
  }

  .theme-label {
    flex: 1;
    font-size: var(--font-size-sm);
  }

  .theme-check {
    font-size: var(--font-size-sm);
  }

  .main-content {
    flex: 1;
    margin-left: 240px;
    padding: var(--spacing-8);
    max-width: calc(100% - 240px);
  }

  @media (max-width: 768px) {
    .sidebar {
      width: 100%;
      height: auto;
      position: relative;
      padding: var(--spacing-4);
    }

    .nav-links {
      flex-direction: row;
      justify-content: space-around;
    }

    .nav-link span:last-child {
      display: none;
    }

    .main-content {
      margin-left: 0;
      max-width: 100%;
      padding: var(--spacing-4);
    }

    .app-container {
      flex-direction: column;
    }

    .sidebar-footer {
      display: none;
    }
  }

  .settings-divider {
    border: none;
    border-top: 1px solid var(--color-border);
    margin: var(--spacing-3) 0;
  }

  .toggle-option {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: var(--spacing-2);
    padding: var(--spacing-2) 0;
    cursor: pointer;
  }

  .toggle-label {
    font-size: var(--font-size-sm);
    color: var(--color-text-secondary);
  }

  .toggle-switch {
    position: relative;
    width: 44px;
    height: 24px;
    background-color: var(--color-surface-hover);
    border: none;
    border-radius: 12px;
    cursor: pointer;
    transition: background-color var(--transition-fast);
  }

  .toggle-switch.active {
    background-color: var(--color-success);
  }

  .toggle-slider {
    position: absolute;
    top: 2px;
    left: 2px;
    width: 20px;
    height: 20px;
    background-color: white;
    border-radius: 50%;
    transition: transform var(--transition-fast);
  }

  .toggle-switch.active .toggle-slider {
    transform: translateX(20px);
  }

  .toggle-hint {
    font-size: 10px;
    color: var(--color-text-muted);
    margin-top: var(--spacing-1);
    line-height: 1.3;
  }
</style>
