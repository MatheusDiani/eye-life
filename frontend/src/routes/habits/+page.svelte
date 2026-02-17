<script lang="ts">
    import { onMount } from "svelte";
    import {
        todayHabits,
        completionPercentage,
        habits,
    } from "$lib/stores/habits";
    import { timer, formatTime } from "$lib/stores/timer";
    import type { Habit } from "$lib/api/client";

    let showForm = $state(false);
    let newHabitName = $state("");
    let newHabitDesc = $state("");
    let newHabitRepeatable = $state(true);
    let newHabitTimer = $state(false);
    let estimatedHours = $state(0);
    let estimatedMinutes = $state(30);
    let selectedDays = $state<number[]>([]);
    let startDate = $state(new Date().toISOString().split("T")[0]); // Default: today
    let submitting = $state(false);

    // Estado para edição de tempo
    let editingTimeHabitId = $state<number | null>(null);
    let editTimeHours = $state(0);
    let editTimeMinutes = $state(0);
    let editTimeSeconds = $state(0);

    const weekDays = [
        { value: 0, label: "Seg" },
        { value: 1, label: "Ter" },
        { value: 2, label: "Qua" },
        { value: 3, label: "Qui" },
        { value: 4, label: "Sex" },
        { value: 5, label: "Sáb" },
        { value: 6, label: "Dom" },
    ];

    onMount(() => {
        habits.fetch();
    });

    async function handleSubmit() {
        if (!newHabitName.trim()) return;

        submitting = true;
        try {
            await habits.create({
                name: newHabitName.trim(),
                description: newHabitDesc.trim() || undefined,
                is_repeatable: newHabitRepeatable,
                has_timer: newHabitTimer,
                estimated_duration_seconds: newHabitTimer
                    ? estimatedHours * 3600 + estimatedMinutes * 60
                    : undefined,
                schedule_days:
                    selectedDays.length > 0 ? selectedDays : undefined,
                start_date: startDate,
            });

            // Reset form
            newHabitName = "";
            newHabitDesc = "";
            newHabitRepeatable = true;
            newHabitTimer = false;
            estimatedHours = 0;
            estimatedMinutes = 30;
            selectedDays = [];
            showForm = false;
        } finally {
            submitting = false;
        }
    }

    async function toggleHabit(habit: Habit) {
        await habits.toggleComplete(habit.id, !habit.completed_today);
    }

    async function handleStartTimer(habit: Habit) {
        if ($timer) {
            await timer.stop();
        }
        await timer.start(habit.id);
    }

    function handlePauseResume() {
        if ($timer?.isPaused) {
            timer.resume();
        } else {
            timer.pause();
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

    function openTimeEditor(habit: Habit) {
        const seconds = habit.time_spent_today;
        editTimeHours = Math.floor(seconds / 3600);
        editTimeMinutes = Math.floor((seconds % 3600) / 60);
        editTimeSeconds = seconds % 60;
        editingTimeHabitId = habit.id;
    }

    function closeTimeEditor() {
        editingTimeHabitId = null;
    }

    async function saveEditedTime() {
        if (editingTimeHabitId === null) return;
        const totalSeconds =
            editTimeHours * 3600 + editTimeMinutes * 60 + editTimeSeconds;
        await habits.updateTimeSpent(editingTimeHabitId, totalSeconds);
        closeTimeEditor();
    }

    function toggleDay(day: number) {
        if (selectedDays.includes(day)) {
            selectedDays = selectedDays.filter((d) => d !== day);
        } else {
            selectedDays = [...selectedDays, day];
        }
    }
</script>

<svelte:head>
    <title>Hábitos | Eye Life</title>
</svelte:head>

<div class="habits-page">
    <header class="page-header">
        <div>
            <h1>Hábitos de Hoje</h1>
            <p class="text-muted">
                Progresso: {$completionPercentage}%
            </p>
        </div>
        <div class="header-actions">
            <a href="/habits/manage" class="btn">⚙️ Gerenciar</a>
            <button
                class="btn btn-primary"
                onclick={() => (showForm = !showForm)}
            >
                {showForm ? "Cancelar" : "+ Novo Hábito"}
            </button>
        </div>
    </header>

    {#if showForm}
        <form
            class="card habit-form animate-slide-up"
            onsubmit={(e) => {
                e.preventDefault();
                handleSubmit();
            }}
        >
            <h3>Novo Hábito</h3>

            <div class="form-group">
                <label class="label" for="habit-name">Nome</label>
                <input
                    type="text"
                    id="habit-name"
                    class="input"
                    placeholder="Ex: Exercício físico"
                    bind:value={newHabitName}
                    required
                />
            </div>

            <div class="form-group">
                <label class="label" for="habit-desc"
                    >Descrição (opcional)</label
                >
                <textarea
                    id="habit-desc"
                    class="textarea"
                    placeholder="Descreva seu hábito..."
                    bind:value={newHabitDesc}
                    style="min-height: 60px;"
                ></textarea>
            </div>

            <div class="form-group">
                <label class="label">Dias da semana</label>
                <div class="days-selector">
                    {#each weekDays as day}
                        <button
                            type="button"
                            class="day-btn"
                            class:selected={selectedDays.includes(day.value)}
                            onclick={() => toggleDay(day.value)}
                        >
                            {day.label}
                        </button>
                    {/each}
                </div>
                <span class="text-muted text-sm">
                    {selectedDays.length === 0
                        ? "Todos os dias"
                        : "Dias selecionados"}
                </span>
            </div>

            <div class="form-group">
                <label class="label">Data de início</label>
                <input type="date" class="input" bind:value={startDate} />
                <span class="text-muted text-sm"
                    >O hábito só aparecerá a partir desta data</span
                >
            </div>

            <div class="form-row">
                <label class="checkbox-wrapper">
                    <input
                        type="checkbox"
                        class="checkbox"
                        bind:checked={newHabitRepeatable}
                    />
                    <span>Repetível diariamente</span>
                </label>

                <label class="checkbox-wrapper">
                    <input
                        type="checkbox"
                        class="checkbox"
                        bind:checked={newHabitTimer}
                    />
                    <span>Ativar cronômetro</span>
                </label>
            </div>

            {#if newHabitTimer}
                <div class="form-group">
                    <label class="label">Tempo estimado diário</label>
                    <div class="time-inputs">
                        <div class="time-input-group">
                            <input
                                type="number"
                                class="input time-input"
                                min="0"
                                max="23"
                                bind:value={estimatedHours}
                            />
                            <span class="time-label">h</span>
                        </div>
                        <div class="time-input-group">
                            <input
                                type="number"
                                class="input time-input"
                                min="0"
                                max="59"
                                bind:value={estimatedMinutes}
                            />
                            <span class="time-label">min</span>
                        </div>
                    </div>
                    <span class="text-muted text-sm"
                        >Usado para repassar tempo excedente</span
                    >
                </div>
            {/if}

            <div class="form-actions">
                <button
                    type="submit"
                    class="btn btn-primary"
                    disabled={submitting}
                >
                    {submitting ? "Salvando..." : "Criar Hábito"}
                </button>
            </div>
        </form>
    {/if}

    <div class="progress-section">
        <div class="progress-bar progress-bar-success">
            <div
                class="progress-bar-fill"
                style="width: {$completionPercentage}%"
            ></div>
        </div>
    </div>

    {#if $todayHabits.length === 0}
        <div class="empty-state card">
            <span class="empty-state-icon">✓</span>
            <p>Nenhum hábito para hoje</p>
            <button class="btn btn-primary" onclick={() => (showForm = true)}>
                Criar novo hábito
            </button>
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
                            <h3 class="habit-name">{habit.name}</h3>
                            {#if habit.description}
                                <p class="habit-desc">{habit.description}</p>
                            {/if}
                            <div class="habit-meta">
                                {#if habit.streak > 0}
                                    <span class="badge badge-success"
                                        >🔥 {habit.streak} dias</span
                                    >
                                {/if}
                                {#if habit.has_timer && habit.estimated_duration_seconds}
                                    {#if editingTimeHabitId === habit.id}
                                        <div class="time-editor">
                                            <input
                                                type="number"
                                                min="0"
                                                max="23"
                                                class="time-input"
                                                bind:value={editTimeHours}
                                            />
                                            <span>:</span>
                                            <input
                                                type="number"
                                                min="0"
                                                max="59"
                                                class="time-input"
                                                bind:value={editTimeMinutes}
                                            />
                                            <span>:</span>
                                            <input
                                                type="number"
                                                min="0"
                                                max="59"
                                                class="time-input"
                                                bind:value={editTimeSeconds}
                                            />
                                            <button
                                                class="btn btn-sm btn-primary"
                                                onclick={saveEditedTime}
                                                >✓</button
                                            >
                                            <button
                                                class="btn btn-sm"
                                                onclick={closeTimeEditor}
                                                >✕</button
                                            >
                                        </div>
                                    {:else}
                                        <button
                                            class="badge badge-clickable"
                                            class:badge-success={habit.time_spent_today >=
                                                habit.estimated_duration_seconds}
                                            onclick={() =>
                                                openTimeEditor(habit)}
                                            title="Clique para editar o tempo"
                                        >
                                            ⏱ {formatTime(
                                                habit.time_spent_today,
                                            )} / {formatTime(
                                                habit.estimated_duration_seconds,
                                            )}
                                        </button>
                                    {/if}
                                {/if}
                            </div>
                        </div>
                    </div>
                </div>
            {/each}
        </div>
    {/if}
</div>

<style>
    .habits-page {
        max-width: 800px;
        margin: 0 auto;
    }

    .page-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: var(--spacing-6);
    }

    .page-header h1 {
        margin-bottom: var(--spacing-1);
    }

    .header-actions {
        display: flex;
        gap: var(--spacing-2);
    }

    .progress-section {
        margin-bottom: var(--spacing-6);
    }

    .habit-form {
        margin-bottom: var(--spacing-6);
    }

    .habit-form h3 {
        margin-bottom: var(--spacing-4);
    }

    .form-group {
        margin-bottom: var(--spacing-4);
    }

    .form-row {
        display: flex;
        gap: var(--spacing-6);
        margin-bottom: var(--spacing-4);
    }

    .form-actions {
        display: flex;
        justify-content: flex-end;
    }

    .time-inputs {
        display: flex;
        gap: var(--spacing-3);
        margin-bottom: var(--spacing-2);
    }

    .time-input-group {
        display: flex;
        align-items: center;
        gap: var(--spacing-1);
    }

    .time-input-group .time-input {
        width: 60px;
    }

    .time-input-group .time-label {
        font-size: var(--font-size-sm);
        color: var(--color-text-muted);
    }

    .days-selector {
        display: flex;
        gap: var(--spacing-2);
        margin-bottom: var(--spacing-2);
    }

    .day-btn {
        padding: var(--spacing-2) var(--spacing-3);
        border: 1px solid var(--color-border);
        border-radius: var(--radius-md);
        background-color: var(--color-surface);
        color: var(--color-text-secondary);
        cursor: pointer;
        transition: all var(--transition-fast);
        font-size: var(--font-size-sm);
    }

    .day-btn:hover {
        background-color: var(--color-surface-hover);
    }

    .day-btn.selected {
        background-color: var(--color-accent);
        color: var(--color-bg);
        border-color: var(--color-accent);
    }

    .habits-list {
        display: flex;
        flex-direction: column;
        gap: var(--spacing-3);
    }

    .habit-card {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: var(--spacing-4) var(--spacing-5);
        transition: all var(--transition-fast);
    }

    .habit-card.completed {
        opacity: 0.7;
    }

    .habit-card.completed .habit-name {
        text-decoration: line-through;
        color: var(--color-text-muted);
    }

    .habit-main {
        display: flex;
        align-items: center;
        gap: var(--spacing-4);
        flex: 1;
    }

    .habit-info {
        flex: 1;
    }

    .habit-name {
        font-size: var(--font-size-base);
        font-weight: var(--font-weight-medium);
        margin-bottom: var(--spacing-1);
    }

    .habit-desc {
        font-size: var(--font-size-sm);
        color: var(--color-text-muted);
        margin-bottom: var(--spacing-2);
    }

    .habit-meta {
        display: flex;
        gap: var(--spacing-2);
        align-items: center;
    }

    .habit-actions {
        display: flex;
        align-items: center;
        gap: var(--spacing-2);
    }

    .timer-controls {
        display: flex;
        align-items: center;
        gap: var(--spacing-3);
        padding: var(--spacing-2) var(--spacing-3);
        background-color: var(--color-surface-hover);
        border-radius: var(--radius-md);
    }

    .timer-display {
        font-family: var(--font-mono);
        font-weight: var(--font-weight-bold);
        font-size: var(--font-size-lg);
        min-width: 80px;
    }

    .timer-buttons {
        display: flex;
        gap: var(--spacing-1);
    }

    .btn-warning {
        background-color: var(--color-warning-muted);
        color: var(--color-warning);
        border-color: transparent;
    }

    .badge-clickable {
        cursor: pointer;
        border: none;
        background-color: var(--color-surface-hover);
        transition: all var(--transition-fast);
    }

    .badge-clickable:hover {
        background-color: var(--color-accent);
        color: var(--color-bg);
    }

    .time-editor {
        display: flex;
        align-items: center;
        gap: var(--spacing-1);
        padding: var(--spacing-1);
        background-color: var(--color-surface-hover);
        border-radius: var(--radius-md);
    }

    .time-input {
        width: 40px;
        padding: var(--spacing-1);
        text-align: center;
        font-family: var(--font-mono);
        font-size: var(--font-size-sm);
        border: 1px solid var(--color-border);
        border-radius: var(--radius-sm);
        background-color: var(--color-surface);
        color: var(--color-text-primary);
    }

    .time-input::-webkit-inner-spin-button,
    .time-input::-webkit-outer-spin-button {
        -webkit-appearance: none;
        margin: 0;
    }

    .empty-state {
        padding: var(--spacing-12);
        text-align: center;
    }

    @media (max-width: 640px) {
        .page-header {
            flex-direction: column;
            gap: var(--spacing-4);
        }

        .header-actions {
            width: 100%;
        }

        .form-row {
            flex-direction: column;
            gap: var(--spacing-3);
        }

        .days-selector {
            flex-wrap: wrap;
        }

        .habit-card {
            flex-direction: column;
            align-items: flex-start;
            gap: var(--spacing-4);
        }

        .habit-actions {
            width: 100%;
            justify-content: flex-end;
        }

        .timer-controls {
            flex-wrap: wrap;
        }
    }
</style>
