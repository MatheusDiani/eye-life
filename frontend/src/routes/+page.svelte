<script lang="ts">
    import { onMount } from "svelte";
    import {
        dashboardAPI,
        habitsAPI,
        type DashboardStats,
        type DailyProgress,
        type HabitDayLog,
    } from "$lib/api/client";
    import {
        todayHabits,
        habits,
        completionPercentage,
        completedToday,
        totalHabitsToday,
    } from "$lib/stores/habits";
    import { timer, formatTime } from "$lib/stores/timer";
    import type { Habit } from "$lib/api/client";

    const timerLoading = timer.loading;

    let stats: DashboardStats | null = $state(null);
    let progress: DailyProgress[] = $state([]);
    let loading = $state(true);
    let error = $state<string | null>(null);

    // Weekly bar click state
    let selectedDay = $state<string | null>(null);
    let selectedDayHabits = $state<HabitDayLog[]>([]);
    let loadingDayHabits = $state(false);

    // Reactive computed values from habits store
    let currentStreak = $derived(calculateStreak());

    function calculateStreak(): number {
        // Calculate from habits store directly
        const completed = $todayHabits.filter((h) => h.completed_today).length;
        const total = $todayHabits.length;
        if (total > 0 && completed === total) {
            return stats?.current_streak || 0;
        }
        return stats?.current_streak || 0;
    }

    async function loadData() {
        try {
            const [statsData, progressData] = await Promise.all([
                dashboardAPI.getStats(),
                dashboardAPI.getProgress(7),
                habits.fetch(),
            ]);
            stats = statsData;
            progress = progressData;
        } catch (e) {
            error = e instanceof Error ? e.message : "Erro ao carregar dados";
        } finally {
            loading = false;
        }
    }

    onMount(() => {
        loadData();
    });

    function isToday(dateString: string): boolean {
        const today = new Date().toISOString().split("T")[0];
        return dateString === today;
    }

    function formatDateLabel(dateString: string): string {
        const date = new Date(dateString + "T12:00:00"); // Add time to avoid timezone issues
        const day = date.getDate().toString().padStart(2, "0");
        const month = (date.getMonth() + 1).toString().padStart(2, "0");
        return `${day}/${month}`;
    }

    function getProgressBarWidth(percentage: number): string {
        return `${Math.min(percentage, 100)}%`;
    }

    async function toggleHabit(habit: Habit) {
        await habits.toggleComplete(habit.id, !habit.completed_today);
        // Refresh stats after toggle
        try {
            const [statsData, progressData] = await Promise.all([
                dashboardAPI.getStats(),
                dashboardAPI.getProgress(7),
            ]);
            stats = statsData;
            progress = progressData;
        } catch (e) {
            // Silently fail, habit is already toggled in local store
        }
    }

    async function handleStartTimer(habit: Habit) {
        if ($timer) {
            await timer.stop();
        }
        // Continue from saved time if any
        await timer.start(habit.id, habit.time_spent_today || 0);
    }

    async function handlePauseResume() {
        if ($timer?.isPaused) {
            await timer.resume();
        } else {
            await timer.pause();
        }
    }

    async function handleStopTimer() {
        await timer.stop();
    }

    function handleResetTimer() {
        timer.reset();
    }

    function isTimerRunning(habitId: number): boolean {
        return $timer?.habitId === habitId;
    }

    // Get today's progress from local store for real-time updates
    function getTodayProgress(): number {
        const total = $todayHabits.length;
        const completed = $todayHabits.filter((h) => h.completed_today).length;
        return total > 0 ? Math.round((completed / total) * 100) : 0;
    }

    // Check if all habits are completed today
    function allCompleted(): boolean {
        return (
            $todayHabits.length > 0 &&
            $todayHabits.every((h) => h.completed_today)
        );
    }

    async function selectProgressDay(dateStr: string) {
        if (selectedDay === dateStr) {
            selectedDay = null;
            selectedDayHabits = [];
            return;
        }
        selectedDay = dateStr;
        loadingDayHabits = true;
        try {
            selectedDayHabits = await habitsAPI.getByDate(dateStr);
        } catch (e) {
            selectedDayHabits = [];
        } finally {
            loadingDayHabits = false;
        }
    }

    function formatSelectedDate(dateStr: string): string {
        const date = new Date(dateStr + "T12:00:00");
        return date.toLocaleDateString("pt-BR", {
            weekday: "long",
            day: "numeric",
            month: "long",
        });
    }
</script>

<svelte:head>
    <title>Meu Dia | Eye Life</title>
</svelte:head>

<div class="dashboard">
    <header class="page-header">
        <h1>Meu Dia</h1>
        <p class="text-muted">
            {new Date().toLocaleDateString("pt-BR", {
                weekday: "long",
                day: "numeric",
                month: "long",
            })}
        </p>
    </header>

    {#if loading}
        <div class="loading-state">
            <div class="spinner"></div>
            <p>Carregando...</p>
        </div>
    {:else if error}
        <div class="error-state card">
            <p>❌ {error}</p>
            <button class="btn" onclick={() => window.location.reload()}>
                Tentar novamente
            </button>
        </div>
    {:else}
        <div class="stats-grid">
            <div class="card stat-card">
                <span class="stat-value">{getTodayProgress()}%</span>
                <span class="stat-label">Progresso Hoje</span>
                <div
                    class="progress-bar progress-bar-success"
                    style="margin-top: var(--spacing-3);"
                >
                    <div
                        class="progress-bar-fill"
                        style="width: {getProgressBarWidth(getTodayProgress())}"
                    ></div>
                </div>
            </div>

            <div class="card stat-card">
                <span class="stat-value"
                    >{$completedToday}/{$totalHabitsToday}</span
                >
                <span class="stat-label">Hábitos Completos</span>
            </div>

            <div class="card stat-card">
                <span class="stat-value">{stats?.current_streak || 0}</span>
                <span class="stat-label">Dias Seguidos</span>
                {#if allCompleted()}
                    <span
                        class="badge badge-success"
                        style="margin-top: var(--spacing-2);"
                    >
                        🔥 Em sequência!
                    </span>
                {/if}
            </div>
        </div>

        <!-- Habits Section (Today or Selected Day) -->
        <section class="section">
            <div class="section-header">
                {#if selectedDay && !isToday(selectedDay)}
                    <h2>{formatSelectedDate(selectedDay)}</h2>
                    <button
                        class="btn btn-sm"
                        onclick={() => {
                            selectedDay = null;
                            selectedDayHabits = [];
                        }}>← Voltar para hoje</button
                    >
                {:else}
                    <h2>Hábitos de Hoje</h2>
                    <a href="/habits" class="btn btn-sm">Ver todos →</a>
                {/if}
            </div>

            {#if selectedDay && !isToday(selectedDay)}
                {#if loadingDayHabits}
                    <div
                        class="loading-state"
                        style="padding: var(--spacing-8);"
                    >
                        <div class="spinner"></div>
                        <p>Carregando...</p>
                    </div>
                {:else if selectedDayHabits.length === 0}
                    <div class="card empty-habits">
                        <p class="text-muted">
                            Nenhum hábito encontrado para este dia
                        </p>
                    </div>
                {:else}
                    <div class="habits-list">
                        {#each selectedDayHabits as habit (habit.habit_id)}
                            <div
                                class="card habit-card"
                                class:completed={habit.completed}
                            >
                                <div class="habit-main">
                                    <span class="day-habit-check"
                                        >{habit.completed ? "✓" : "—"}</span
                                    >
                                    <div class="habit-info">
                                        <span class="habit-name"
                                            >{habit.habit_name}</span
                                        >
                                        {#if habit.has_timer}
                                            <span
                                                class="badge badge-sm"
                                                class:badge-success={habit.estimated_duration_seconds &&
                                                    habit.time_spent_seconds >=
                                                        habit.estimated_duration_seconds}
                                            >
                                                ⏱ {formatTime(
                                                    habit.time_spent_seconds,
                                                )}{#if habit.estimated_duration_seconds}
                                                    / {formatTime(
                                                        habit.estimated_duration_seconds,
                                                    )}{/if}
                                            </span>
                                        {/if}
                                    </div>
                                </div>
                            </div>
                        {/each}
                    </div>
                {/if}
            {:else if $todayHabits.length === 0}
                <div class="card empty-habits">
                    <p class="text-muted">Nenhum hábito para hoje</p>
                    <a href="/habits" class="btn btn-primary">Criar hábito</a>
                </div>
            {:else}
                <div class="habits-list">
                    {#each $todayHabits as habit (habit.id)}
                        <div
                            class="card habit-card"
                            class:completed={habit.completed_today}
                        >
                            <div class="habit-main">
                                <label class="checkbox-wrapper">
                                    <input
                                        type="checkbox"
                                        class="checkbox"
                                        checked={habit.completed_today}
                                        onchange={() => toggleHabit(habit)}
                                    />
                                </label>
                                <div class="habit-info">
                                    <span class="habit-name">{habit.name}</span>
                                    {#if habit.streak > 0}
                                        <span
                                            class="badge badge-success badge-sm"
                                            >🔥 {habit.streak}</span
                                        >
                                    {/if}
                                    {#if habit.has_timer && habit.estimated_duration_seconds}
                                        {@const currentTime = isTimerRunning(
                                            habit.id,
                                        )
                                            ? $timer?.elapsedSeconds || 0
                                            : habit.time_spent_today}
                                        {@const totalRequired =
                                            habit.estimated_duration_seconds +
                                            (habit.deficit_seconds || 0)}
                                        <span
                                            class="badge badge-sm"
                                            class:badge-success={currentTime >=
                                                totalRequired}
                                            class:badge-warning={habit.deficit_seconds >
                                                0 &&
                                                currentTime < totalRequired}
                                            title={habit.deficit_seconds > 0
                                                ? `Inclui ${formatTime(habit.deficit_seconds)} de déficit de ontem`
                                                : ""}
                                        >
                                            ⏱ {formatTime(currentTime)} / {formatTime(
                                                totalRequired,
                                            )}
                                        </span>
                                    {/if}
                                </div>
                                {#if habit.has_timer && !habit.completed_today}
                                    {#if isTimerRunning(habit.id)}
                                        <button
                                            class="btn btn-sm"
                                            class:btn-warning={!$timer?.isPaused &&
                                                !$timerLoading}
                                            class:btn-success={$timer?.isPaused &&
                                                !$timerLoading}
                                            disabled={$timerLoading}
                                            onclick={(e) => {
                                                e.stopPropagation();
                                                handlePauseResume();
                                            }}
                                        >
                                            {#if $timerLoading}
                                                <span class="btn-spinner"
                                                ></span>
                                            {:else}
                                                {$timer?.isPaused ? "▶" : "⏸"}
                                            {/if}
                                        </button>
                                    {:else}
                                        <button
                                            class="btn btn-sm"
                                            onclick={(e) => {
                                                e.stopPropagation();
                                                handleStartTimer(habit);
                                            }}>▶</button
                                        >
                                    {/if}
                                {/if}
                            </div>
                        </div>
                    {/each}
                </div>
            {/if}
        </section>

        <!-- Weekly Progress Section -->
        <section class="section">
            <h2>Progresso Semanal</h2>
            <div class="weekly-chart card">
                <div class="chart-bars">
                    {#each progress as day}
                        {@const todayProgress = isToday(day.date)
                            ? getTodayProgress()
                            : day.percentage}
                        <div
                            class="chart-bar-container"
                            class:today={isToday(day.date)}
                            class:selected-bar={selectedDay === day.date}
                            onclick={() => selectProgressDay(day.date)}
                            role="button"
                            tabindex="0"
                            onkeydown={(e) =>
                                e.key === "Enter" &&
                                selectProgressDay(day.date)}
                        >
                            <div
                                class="chart-bar"
                                class:today-bar={isToday(day.date)}
                                style="height: {Math.max(todayProgress, 5)}%"
                            >
                                <span class="chart-value"
                                    >{Math.round(todayProgress)}%</span
                                >
                            </div>
                            <span class="chart-label"
                                >{formatDateLabel(day.date)}</span
                            >
                            {#if isToday(day.date)}
                                <span class="today-indicator">Hoje</span>
                            {/if}
                        </div>
                    {/each}
                </div>
            </div>
        </section>

        <!-- Quick Actions -->
        <section class="section">
            <div class="section-header">
                <h2>Ações Rápidas</h2>
            </div>
            <div class="quick-actions">
                <a href="/habits/manage" class="card action-card">
                    <span class="action-icon">⚙️</span>
                    <span class="action-title">Gerenciar Hábitos</span>
                </a>
                <a href="/notes" class="card action-card">
                    <span class="action-icon">📝</span>
                    <span class="action-title">Nova Nota</span>
                </a>
                <a href="/stats" class="card action-card">
                    <span class="action-icon">📈</span>
                    <span class="action-title">Estatísticas</span>
                </a>
            </div>
        </section>
    {/if}
</div>

<style>
    .dashboard {
        max-width: 1000px;
        margin: 0 auto;
    }

    .page-header {
        margin-bottom: var(--spacing-6);
    }

    .page-header h1 {
        margin-bottom: var(--spacing-1);
    }

    .stats-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: var(--spacing-4);
        margin-bottom: var(--spacing-6);
    }

    .section {
        margin-bottom: var(--spacing-6);
    }

    .section h2 {
        margin-bottom: var(--spacing-4);
        font-size: var(--font-size-lg);
    }

    .section-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: var(--spacing-4);
    }

    .section-header h2 {
        margin-bottom: 0;
    }

    /* Habits List */
    .habits-list {
        display: flex;
        flex-direction: column;
        gap: var(--spacing-2);
    }

    .habit-card {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: var(--spacing-3) var(--spacing-4);
    }

    .habit-card.completed {
        opacity: 0.6;
    }

    .habit-card.completed .habit-name {
        text-decoration: line-through;
        color: var(--color-text-muted);
    }

    .habit-main {
        display: flex;
        align-items: center;
        gap: var(--spacing-3);
    }

    .habit-info {
        display: flex;
        align-items: center;
        gap: var(--spacing-2);
    }

    .habit-name {
        font-weight: var(--font-weight-medium);
    }

    .badge-sm {
        font-size: var(--font-size-xs);
        padding: 2px 6px;
    }

    .badge-warning {
        background-color: var(--color-warning-muted);
        color: var(--color-warning);
        border: 1px solid var(--color-warning);
    }

    .empty-habits {
        text-align: center;
        padding: var(--spacing-6);
    }

    .empty-habits p {
        margin-bottom: var(--spacing-3);
    }

    /* Weekly Chart */
    .weekly-chart {
        padding: var(--spacing-6);
    }

    .chart-bars {
        display: flex;
        justify-content: space-between;
        align-items: flex-end;
        height: 180px;
        gap: var(--spacing-2);
    }

    .chart-bar-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        flex: 1;
        height: 100%;
    }

    .chart-bar-container.today {
        position: relative;
    }

    .chart-bar {
        width: 100%;
        max-width: 50px;
        background: linear-gradient(
            180deg,
            var(--color-surface-hover) 0%,
            var(--color-border) 100%
        );
        border-radius: var(--radius-md) var(--radius-md) 0 0;
        display: flex;
        align-items: flex-start;
        justify-content: center;
        padding-top: var(--spacing-2);
        margin-top: auto;
        transition: height var(--transition-normal);
    }

    .chart-bar.today-bar {
        background: linear-gradient(
            180deg,
            var(--color-accent) 0%,
            var(--color-surface-hover) 100%
        );
    }

    .chart-value {
        font-size: var(--font-size-xs);
        font-weight: var(--font-weight-semibold);
        color: var(--color-text-primary);
    }

    .today-bar .chart-value {
        color: var(--color-bg);
    }

    .chart-label {
        font-size: var(--font-size-xs);
        color: var(--color-text-muted);
        margin-top: var(--spacing-2);
        font-family: var(--font-mono);
    }

    .chart-bar-container.today .chart-label {
        color: var(--color-text-primary);
        font-weight: var(--font-weight-semibold);
    }

    .today-indicator {
        font-size: 10px;
        color: var(--color-accent);
        font-weight: var(--font-weight-bold);
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .chart-bar-container {
        cursor: pointer;
    }

    .chart-bar-container:hover .chart-bar {
        opacity: 0.8;
    }

    .chart-bar-container.selected-bar {
        position: relative;
    }

    .chart-bar-container.selected-bar .chart-bar {
        background: linear-gradient(
            180deg,
            var(--color-accent) 0%,
            var(--color-surface-hover) 100%
        );
    }

    .chart-bar-container.selected-bar .chart-label {
        color: var(--color-accent);
        font-weight: var(--font-weight-semibold);
    }

    /* Day habit check icon */
    .day-habit-check {
        font-weight: var(--font-weight-bold);
        font-size: var(--font-size-sm);
        color: var(--color-text-muted);
        width: 20px;
        text-align: center;
    }

    .habit-card.completed .day-habit-check {
        color: var(--color-success);
    }

    /* Quick Actions */
    .quick-actions {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: var(--spacing-3);
    }

    .action-card {
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
        padding: var(--spacing-5);
        cursor: pointer;
        text-decoration: none;
    }

    .action-card:hover {
        transform: translateY(-2px);
    }

    .action-icon {
        font-size: 1.5rem;
        margin-bottom: var(--spacing-2);
    }

    .action-title {
        font-weight: var(--font-weight-medium);
        color: var(--color-text-primary);
        font-size: var(--font-size-sm);
    }

    /* Loading & Error */
    .loading-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: var(--spacing-16);
        color: var(--color-text-muted);
    }

    .spinner {
        width: 40px;
        height: 40px;
        border: 3px solid var(--color-border);
        border-top-color: var(--color-accent);
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin-bottom: var(--spacing-4);
    }

    @keyframes spin {
        to {
            transform: rotate(360deg);
        }
    }

    .error-state {
        text-align: center;
        padding: var(--spacing-8);
    }

    .btn-warning {
        background-color: var(--color-warning-muted);
        color: var(--color-warning);
        border-color: transparent;
    }

    @media (max-width: 768px) {
        .stats-grid {
            grid-template-columns: 1fr;
        }

        .quick-actions {
            grid-template-columns: 1fr;
        }

        .chart-bars {
            height: 140px;
        }
    }

    .btn-spinner {
        display: inline-block;
        width: 14px;
        height: 14px;
        border: 2px solid var(--color-text-muted);
        border-top-color: transparent;
        border-radius: 50%;
        animation: spin 0.6s linear infinite;
    }
</style>
