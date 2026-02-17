<script lang="ts">
    import { onMount } from "svelte";
    import { habits, activeHabits } from "$lib/stores/habits";
    import {
        habitsAPI,
        type HabitStats,
        type HabitDayLog,
    } from "$lib/api/client";
    import { formatTime } from "$lib/stores/timer";

    let selectedHabit = $state<number | null>(null);
    let habitStats = $state<HabitStats | null>(null);
    let loading = $state(false);

    // Calendar state
    let currentMonth = $state(new Date());
    let selectedDate = $state<Date | null>(null);
    let dayHabits = $state<HabitDayLog[]>([]);
    let loadingDay = $state(false);

    onMount(() => {
        habits.fetch();
    });

    async function loadStats(habitId: number) {
        selectedHabit = habitId;
        selectedDate = null;
        loading = true;
        habitStats = null;
        try {
            habitStats = await habitsAPI.getStats(habitId, 30);
        } finally {
            loading = false;
        }
    }

    function getCompletionColor(rate: number): string {
        if (rate >= 80) return "var(--color-success)";
        if (rate >= 50) return "var(--color-warning)";
        return "var(--color-text-muted)";
    }

    // Calendar functions
    function getMonthDays(date: Date): (Date | null)[] {
        const year = date.getFullYear();
        const month = date.getMonth();
        const firstDay = new Date(year, month, 1);
        const lastDay = new Date(year, month + 1, 0);

        const days: (Date | null)[] = [];

        // Add empty slots for days before the first day of month
        const startPadding =
            firstDay.getDay() === 0 ? 6 : firstDay.getDay() - 1;
        for (let i = 0; i < startPadding; i++) {
            days.push(null);
        }

        // Add all days of the month
        for (let d = 1; d <= lastDay.getDate(); d++) {
            days.push(new Date(year, month, d));
        }

        return days;
    }

    function prevMonth() {
        currentMonth = new Date(
            currentMonth.getFullYear(),
            currentMonth.getMonth() - 1,
            1,
        );
        selectedDate = null;
        dayHabits = [];
    }

    function nextMonth() {
        const now = new Date();
        const next = new Date(
            currentMonth.getFullYear(),
            currentMonth.getMonth() + 1,
            1,
        );
        // Don't allow future months
        if (next <= now) {
            currentMonth = next;
            selectedDate = null;
            dayHabits = [];
        }
    }

    function formatDateStr(date: Date): string {
        return date.toISOString().split("T")[0];
    }

    async function selectDay(day: Date) {
        const today = new Date();
        today.setHours(0, 0, 0, 0);

        // Don't allow selecting future dates
        if (day > today) return;

        selectedDate = day;
        selectedHabit = null;
        habitStats = null;
        loadingDay = true;

        try {
            dayHabits = await habitsAPI.getByDate(formatDateStr(day));
        } finally {
            loadingDay = false;
        }
    }

    async function toggleHabitCompletion(habit: HabitDayLog) {
        if (!selectedDate) return;

        try {
            await habitsAPI.updateByDate(
                formatDateStr(selectedDate),
                habit.habit_id,
                !habit.completed,
                habit.time_spent_seconds,
            );
            // Reload day data
            dayHabits = await habitsAPI.getByDate(formatDateStr(selectedDate));
        } catch (e) {
            console.error("Failed to update habit:", e);
        }
    }

    function isToday(date: Date): boolean {
        const today = new Date();
        return date.toDateString() === today.toDateString();
    }

    function isFuture(date: Date): boolean {
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        return date > today;
    }

    function isSelected(date: Date): boolean {
        return (
            selectedDate !== null &&
            date.toDateString() === selectedDate.toDateString()
        );
    }

    $effect(() => {
        // Get completion summary for visible days
    });
</script>

<svelte:head>
    <title>Estatísticas | Eye Life</title>
</svelte:head>

<div class="stats-page">
    <header class="page-header">
        <div>
            <h1>Estatísticas</h1>
            <p class="text-muted">Acompanhe seu progresso detalhado</p>
        </div>
    </header>

    <!-- Month Calendar -->
    <div class="card calendar-section">
        <div class="calendar-header">
            <button class="btn btn-ghost" onclick={prevMonth}>←</button>
            <h3>
                {currentMonth.toLocaleDateString("pt-BR", {
                    month: "long",
                    year: "numeric",
                })}
            </h3>
            <button
                class="btn btn-ghost"
                onclick={nextMonth}
                disabled={currentMonth.getMonth() === new Date().getMonth() &&
                    currentMonth.getFullYear() === new Date().getFullYear()}
                >→</button
            >
        </div>

        <div class="month-calendar">
            <div class="weekday-header">
                <span>Seg</span>
                <span>Ter</span>
                <span>Qua</span>
                <span>Qui</span>
                <span>Sex</span>
                <span>Sáb</span>
                <span>Dom</span>
            </div>
            <div class="calendar-days">
                {#each getMonthDays(currentMonth) as day}
                    {#if day === null}
                        <div class="day-cell empty"></div>
                    {:else}
                        <button
                            class="day-cell"
                            class:today={isToday(day)}
                            class:future={isFuture(day)}
                            class:selected={isSelected(day)}
                            onclick={() => selectDay(day)}
                            disabled={isFuture(day)}
                        >
                            {day.getDate()}
                        </button>
                    {/if}
                {/each}
            </div>
        </div>
    </div>

    <!-- Day Details or Habit Stats -->
    {#if selectedDate}
        <div class="card day-details animate-fade-in">
            <h3>
                {selectedDate.toLocaleDateString("pt-BR", {
                    weekday: "long",
                    day: "numeric",
                    month: "long",
                })}
            </h3>

            {#if loadingDay}
                <div class="loading-state">
                    <div class="spinner"></div>
                    <p>Carregando...</p>
                </div>
            {:else if dayHabits.length === 0}
                <p class="text-muted text-center">
                    Nenhum hábito encontrado para este dia
                </p>
            {:else}
                <div class="day-habits-list">
                    {#each dayHabits as habit (habit.habit_id)}
                        <div
                            class="day-habit-item"
                            class:scheduled={habit.is_scheduled}
                        >
                            <button
                                class="habit-checkbox"
                                class:completed={habit.completed}
                                onclick={() => toggleHabitCompletion(habit)}
                            >
                                {habit.completed ? "✓" : ""}
                            </button>
                            <div class="habit-info">
                                <span class="habit-name"
                                    >{habit.habit_name}</span
                                >
                                {#if habit.has_timer}
                                    <span class="badge badge-sm">
                                        ⏱ {formatTime(
                                            habit.time_spent_seconds,
                                        )}
                                    </span>
                                {/if}
                                {#if !habit.is_scheduled}
                                    <span class="badge badge-muted"
                                        >Não agendado</span
                                    >
                                {/if}
                                {#if habit.carryover_seconds > 0}
                                    <span
                                        class="badge badge-success"
                                        title="Crédito do dia anterior"
                                    >
                                        +{formatTime(habit.carryover_seconds)}
                                    </span>
                                {/if}
                                {#if habit.deficit_seconds > 0}
                                    <span
                                        class="badge badge-warning"
                                        title="Déficit do dia anterior"
                                    >
                                        -{formatTime(habit.deficit_seconds)}
                                    </span>
                                {/if}
                            </div>
                        </div>
                    {/each}
                </div>
            {/if}
        </div>
    {/if}

    <div class="stats-layout">
        <aside class="habits-sidebar">
            <h3>Seus Hábitos</h3>
            <div class="habits-list">
                {#each $activeHabits as habit (habit.id)}
                    <button
                        class="habit-btn"
                        class:active={selectedHabit === habit.id}
                        onclick={() => loadStats(habit.id)}
                    >
                        <span class="habit-name">{habit.name}</span>
                        {#if habit.streak > 0}
                            <span class="badge badge-success"
                                >🔥 {habit.streak}</span
                            >
                        {/if}
                    </button>
                {:else}
                    <p class="text-muted text-center">Nenhum hábito ativo</p>
                {/each}
            </div>
        </aside>

        <main class="stats-content">
            {#if !selectedHabit}
                <div class="empty-state card">
                    <span class="empty-state-icon">📈</span>
                    <p>Selecione um hábito para ver estatísticas detalhadas</p>
                </div>
            {:else if loading}
                <div class="loading-state">
                    <div class="spinner"></div>
                    <p>Carregando estatísticas...</p>
                </div>
            {:else if habitStats}
                <div class="stats-detail animate-fade-in">
                    <div class="stats-header card">
                        <h2>{habitStats.habit_name}</h2>
                        <p class="text-muted">
                            Últimos {habitStats.period_days} dias
                        </p>
                    </div>

                    <div class="stats-grid">
                        <div class="card stat-card">
                            <span
                                class="stat-value"
                                style="color: {getCompletionColor(
                                    habitStats.completion_rate,
                                )}"
                            >
                                {habitStats.completion_rate}%
                            </span>
                            <span class="stat-label">Taxa de Conclusão</span>
                        </div>

                        <div class="card stat-card">
                            <span class="stat-value"
                                >{habitStats.completed_days}</span
                            >
                            <span class="stat-label">Dias Completos</span>
                        </div>

                        <div class="card stat-card">
                            <span class="stat-value"
                                >🔥 {habitStats.current_streak}</span
                            >
                            <span class="stat-label">Sequência Atual</span>
                        </div>

                        {#if habitStats.total_time_seconds > 0}
                            <div class="card stat-card">
                                <span class="stat-value text-mono"
                                    >{formatTime(
                                        habitStats.total_time_seconds,
                                    )}</span
                                >
                                <span class="stat-label">Tempo Total</span>
                            </div>
                        {/if}
                    </div>

                    <div class="card calendar-card">
                        <h3>Histórico de Conclusão</h3>
                        <div class="calendar-grid">
                            {#each habitStats.logs as log}
                                <div
                                    class="calendar-day"
                                    class:completed={log.completed}
                                    title={`${new Date(log.date).toLocaleDateString("pt-BR")} - ${log.completed ? "Completo" : "Não completo"}`}
                                >
                                    <span class="day-number"
                                        >{new Date(log.date).getDate()}</span
                                    >
                                </div>
                            {/each}
                        </div>
                    </div>
                </div>
            {/if}
        </main>
    </div>
</div>

<style>
    .stats-page {
        max-width: 1200px;
        margin: 0 auto;
    }

    .page-header {
        margin-bottom: var(--spacing-6);
    }

    .page-header h1 {
        margin-bottom: var(--spacing-1);
    }

    /* Calendar Section */
    .calendar-section {
        margin-bottom: var(--spacing-6);
        padding: var(--spacing-3);
        max-width: 320px;
    }

    .calendar-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: var(--spacing-2);
    }

    .calendar-header h3 {
        text-transform: capitalize;
        margin: 0;
        font-size: var(--font-size-sm);
    }

    .month-calendar {
        width: 100%;
    }

    .weekday-header {
        display: grid;
        grid-template-columns: repeat(7, 1fr);
        text-align: center;
        font-size: 10px;
        color: var(--color-text-muted);
        margin-bottom: var(--spacing-1);
    }

    .calendar-days {
        display: grid;
        grid-template-columns: repeat(7, 1fr);
        gap: 2px;
    }

    .day-cell {
        width: 32px;
        height: 32px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: var(--radius-sm);
        border: none;
        background-color: var(--color-surface-hover);
        color: var(--color-text-primary);
        font-size: 11px;
        cursor: pointer;
        transition: all var(--transition-fast);
    }

    .day-cell:hover:not(.future):not(.empty) {
        background-color: var(--color-accent);
        color: var(--color-bg);
    }

    .day-cell.empty {
        background: transparent;
        cursor: default;
    }

    .day-cell.today {
        border: 2px solid var(--color-accent);
    }

    .day-cell.future {
        opacity: 0.3;
        cursor: not-allowed;
    }

    .day-cell.selected {
        background-color: var(--color-accent);
        color: var(--color-bg);
    }

    /* Day Details */
    .day-details {
        margin-bottom: var(--spacing-6);
        padding: var(--spacing-4);
    }

    .day-details h3 {
        text-transform: capitalize;
        margin-bottom: var(--spacing-4);
    }

    .day-habits-list {
        display: flex;
        flex-direction: column;
        gap: var(--spacing-2);
    }

    .day-habit-item {
        display: flex;
        align-items: center;
        gap: var(--spacing-3);
        padding: var(--spacing-3);
        background-color: var(--color-surface-hover);
        border-radius: var(--radius-md);
    }

    .day-habit-item:not(.scheduled) {
        opacity: 0.6;
    }

    .habit-checkbox {
        width: 28px;
        height: 28px;
        border-radius: var(--radius-sm);
        border: 2px solid var(--color-border);
        background-color: var(--color-surface);
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: var(--font-size-sm);
        color: var(--color-bg);
        transition: all var(--transition-fast);
    }

    .habit-checkbox:hover {
        border-color: var(--color-accent);
    }

    .habit-checkbox.completed {
        background-color: var(--color-success);
        border-color: var(--color-success);
    }

    .habit-info {
        display: flex;
        align-items: center;
        gap: var(--spacing-2);
        flex-wrap: wrap;
    }

    .badge-sm {
        font-size: 10px;
        padding: 2px 6px;
    }

    .badge-muted {
        background-color: var(--color-surface-hover);
        color: var(--color-text-muted);
    }

    .badge-warning {
        background-color: var(--color-warning-muted);
        color: var(--color-warning);
    }

    /* Stats Layout */
    .stats-layout {
        display: grid;
        grid-template-columns: 280px 1fr;
        gap: var(--spacing-6);
    }

    .habits-sidebar {
        background-color: var(--color-surface);
        border-radius: var(--radius-lg);
        padding: var(--spacing-4);
        height: fit-content;
        position: sticky;
        top: var(--spacing-4);
    }

    .habits-sidebar h3 {
        margin-bottom: var(--spacing-4);
        padding-bottom: var(--spacing-2);
        border-bottom: 1px solid var(--color-border);
    }

    .habits-list {
        display: flex;
        flex-direction: column;
        gap: var(--spacing-2);
    }

    .habit-btn {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: var(--spacing-3) var(--spacing-4);
        border: 1px solid var(--color-border);
        border-radius: var(--radius-md);
        background-color: var(--color-surface);
        color: var(--color-text-secondary);
        cursor: pointer;
        transition: all var(--transition-fast);
        text-align: left;
    }

    .habit-btn:hover {
        background-color: var(--color-surface-hover);
        color: var(--color-text-primary);
    }

    .habit-btn.active {
        background-color: var(--color-accent);
        color: var(--color-bg);
        border-color: var(--color-accent);
    }

    .habit-name {
        flex: 1;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .stats-content {
        min-height: 400px;
    }

    .stats-header {
        padding: var(--spacing-6);
        margin-bottom: var(--spacing-4);
    }

    .stats-header h2 {
        margin-bottom: var(--spacing-1);
    }

    .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: var(--spacing-4);
        margin-bottom: var(--spacing-4);
    }

    .stat-card {
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
        padding: var(--spacing-6);
    }

    .stat-value {
        font-size: var(--font-size-2xl);
        font-weight: var(--font-weight-bold);
        margin-bottom: var(--spacing-2);
    }

    .stat-label {
        font-size: var(--font-size-sm);
        color: var(--color-text-muted);
    }

    .calendar-card {
        padding: var(--spacing-6);
    }

    .calendar-card h3 {
        margin-bottom: var(--spacing-4);
    }

    .calendar-grid {
        display: flex;
        flex-wrap: wrap;
        gap: var(--spacing-2);
    }

    .calendar-day {
        width: 36px;
        height: 36px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: var(--radius-sm);
        background-color: var(--color-surface-hover);
        cursor: default;
        transition: all var(--transition-fast);
    }

    .calendar-day.completed {
        background-color: var(--color-success);
        color: var(--color-bg);
    }

    .day-number {
        font-size: var(--font-size-xs);
        font-weight: var(--font-weight-medium);
    }

    .loading-state,
    .empty-state {
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

    @media (max-width: 768px) {
        .stats-layout {
            grid-template-columns: 1fr;
        }

        .habits-sidebar {
            position: static;
        }

        .stats-grid {
            grid-template-columns: repeat(2, 1fr);
        }
    }
</style>
