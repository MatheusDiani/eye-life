<script lang="ts">
    import { onMount } from "svelte";
    import { habits, activeHabits, archivedHabits } from "$lib/stores/habits";
    import type { Habit } from "$lib/api/client";

    let showArchived = $state(false);
    let editingHabit = $state<Habit | null>(null);
    let editName = $state("");
    let editDesc = $state("");
    let editTimer = $state(false);
    let editEstimatedHours = $state(0);
    let editEstimatedMinutes = $state(30);
    let editDays = $state<number[]>([]);
    let saving = $state(false);

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
        habits.fetch(true); // Include archived
    });

    function startEdit(habit: Habit) {
        editingHabit = habit;
        editName = habit.name;
        editDesc = habit.description || "";
        editTimer = habit.has_timer;
        const estimatedSeconds = habit.estimated_duration_seconds || 1800;
        editEstimatedHours = Math.floor(estimatedSeconds / 3600);
        editEstimatedMinutes = Math.floor((estimatedSeconds % 3600) / 60);
        editDays = habit.schedule_days || [];
    }

    function cancelEdit() {
        editingHabit = null;
    }

    async function saveEdit() {
        if (!editingHabit || !editName.trim()) return;

        saving = true;
        try {
            await habits.updateHabit(editingHabit.id, {
                name: editName.trim(),
                description: editDesc.trim() || undefined,
                has_timer: editTimer,
                estimated_duration_seconds: editTimer
                    ? editEstimatedHours * 3600 + editEstimatedMinutes * 60
                    : null,
                schedule_days: editDays.length > 0 ? editDays : undefined,
            });
            // Refresh habits to get updated data from server
            await habits.fetch(true);
            editingHabit = null;
        } finally {
            saving = false;
        }
    }

    async function archiveHabit(habit: Habit) {
        await habits.archive(habit.id);
    }

    async function unarchiveHabit(habit: Habit) {
        await habits.unarchive(habit.id);
    }

    async function deleteHabit(habit: Habit) {
        if (
            confirm(
                `Tem certeza que deseja excluir "${habit.name}"? Esta ação não pode ser desfeita.`,
            )
        ) {
            await habits.delete(habit.id);
        }
    }

    function toggleDay(day: number) {
        if (editDays.includes(day)) {
            editDays = editDays.filter((d) => d !== day);
        } else {
            editDays = [...editDays, day];
        }
    }

    function formatDays(days: number[] | null): string {
        if (!days || days.length === 0) return "Todos os dias";
        if (days.length === 7) return "Todos os dias";
        return days.map((d) => weekDays[d].label).join(", ");
    }
</script>

<svelte:head>
    <title>Gerenciar Hábitos | Eye Life</title>
</svelte:head>

<div class="manage-page">
    <header class="page-header">
        <div>
            <h1>Gerenciar Hábitos</h1>
            <p class="text-muted">Edite, arquive ou exclua seus hábitos</p>
        </div>
        <a href="/habits" class="btn btn-primary">← Voltar</a>
    </header>

    <div class="tabs">
        <button
            class="tab"
            class:active={!showArchived}
            onclick={() => (showArchived = false)}
        >
            Ativos ({$activeHabits.length})
        </button>
        <button
            class="tab"
            class:active={showArchived}
            onclick={() => (showArchived = true)}
        >
            Arquivados ({$archivedHabits.length})
        </button>
    </div>

    {#if editingHabit}
        <div class="card edit-form animate-slide-up">
            <h3>Editar Hábito</h3>

            <div class="form-group">
                <label class="label" for="edit-name">Nome</label>
                <input
                    type="text"
                    id="edit-name"
                    class="input"
                    bind:value={editName}
                    required
                />
            </div>

            <div class="form-group">
                <label class="label" for="edit-desc">Descrição</label>
                <textarea id="edit-desc" class="textarea" bind:value={editDesc}
                ></textarea>
            </div>

            <div class="form-group">
                <label class="label">Dias da semana</label>
                <div class="days-selector">
                    {#each weekDays as day}
                        <button
                            type="button"
                            class="day-btn"
                            class:selected={editDays.includes(day.value)}
                            onclick={() => toggleDay(day.value)}
                        >
                            {day.label}
                        </button>
                    {/each}
                </div>
                <span class="text-muted text-sm">
                    {editDays.length === 0
                        ? "Todos os dias"
                        : "Dias selecionados"}
                </span>
            </div>

            <label class="checkbox-wrapper">
                <input
                    type="checkbox"
                    class="checkbox"
                    bind:checked={editTimer}
                />
                <span>Ativar cronômetro</span>
            </label>

            {#if editTimer}
                <div class="form-group">
                    <label class="label">Tempo estimado diário</label>
                    <div class="time-inputs">
                        <div class="time-input-group">
                            <input
                                type="number"
                                class="input time-input"
                                min="0"
                                max="23"
                                bind:value={editEstimatedHours}
                            />
                            <span class="time-label">h</span>
                        </div>
                        <div class="time-input-group">
                            <input
                                type="number"
                                class="input time-input"
                                min="0"
                                max="59"
                                bind:value={editEstimatedMinutes}
                            />
                            <span class="time-label">min</span>
                        </div>
                    </div>
                </div>
            {/if}

            <div class="form-actions">
                <button class="btn" onclick={cancelEdit}>Cancelar</button>
                <button
                    class="btn btn-primary"
                    onclick={saveEdit}
                    disabled={saving}
                >
                    {saving ? "Salvando..." : "Salvar"}
                </button>
            </div>
        </div>
    {/if}

    <div class="habits-list">
        {#each showArchived ? $archivedHabits : $activeHabits as habit (habit.id)}
            <div class="card habit-item">
                <div class="habit-info">
                    <h3>{habit.name}</h3>
                    {#if habit.description}
                        <p class="text-muted">{habit.description}</p>
                    {/if}
                    <div class="habit-meta">
                        <span class="badge"
                            >{formatDays(habit.schedule_days)}</span
                        >
                        {#if habit.has_timer}
                            <span class="badge">⏱ Cronômetro</span>
                        {/if}
                    </div>
                </div>

                <div class="habit-actions">
                    {#if !habit.is_archived}
                        <button
                            class="btn btn-sm"
                            onclick={() => startEdit(habit)}
                            title="Editar"
                        >
                            ✏️
                        </button>
                        <button
                            class="btn btn-sm"
                            onclick={() => archiveHabit(habit)}
                            title="Arquivar"
                        >
                            📦
                        </button>
                    {:else}
                        <button
                            class="btn btn-sm btn-primary"
                            onclick={() => unarchiveHabit(habit)}
                            title="Restaurar"
                        >
                            ↩️
                        </button>
                    {/if}
                    <button
                        class="btn btn-sm btn-danger"
                        onclick={() => deleteHabit(habit)}
                        title="Excluir"
                    >
                        🗑
                    </button>
                </div>
            </div>
        {:else}
            <div class="empty-state card">
                <p>
                    {showArchived
                        ? "Nenhum hábito arquivado"
                        : "Nenhum hábito ativo"}
                </p>
            </div>
        {/each}
    </div>
</div>

<style>
    .manage-page {
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

    .tabs {
        display: flex;
        gap: var(--spacing-2);
        margin-bottom: var(--spacing-6);
        border-bottom: 1px solid var(--color-border);
        padding-bottom: var(--spacing-2);
    }

    .tab {
        padding: var(--spacing-2) var(--spacing-4);
        border: none;
        background: none;
        color: var(--color-text-secondary);
        cursor: pointer;
        transition: all var(--transition-fast);
        border-bottom: 2px solid transparent;
        margin-bottom: -2px;
    }

    .tab.active {
        color: var(--color-text-primary);
        border-bottom-color: var(--color-accent);
    }

    .edit-form {
        margin-bottom: var(--spacing-6);
        padding: var(--spacing-6);
    }

    .edit-form h3 {
        margin-bottom: var(--spacing-4);
    }

    .form-group {
        margin-bottom: var(--spacing-4);
    }

    .form-actions {
        display: flex;
        gap: var(--spacing-2);
        justify-content: flex-end;
        margin-top: var(--spacing-4);
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

    .time-inputs {
        display: flex;
        gap: var(--spacing-3);
    }

    .time-input-group {
        display: flex;
        align-items: center;
        gap: var(--spacing-1);
    }

    .time-input {
        width: 60px;
        text-align: center;
    }

    .time-label {
        color: var(--color-text-muted);
        font-size: var(--font-size-sm);
    }

    .habits-list {
        display: flex;
        flex-direction: column;
        gap: var(--spacing-3);
    }

    .habit-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: var(--spacing-4) var(--spacing-5);
    }

    .habit-info h3 {
        margin-bottom: var(--spacing-1);
    }

    .habit-info .text-muted {
        margin-bottom: var(--spacing-2);
        font-size: var(--font-size-sm);
    }

    .habit-meta {
        display: flex;
        gap: var(--spacing-2);
    }

    .habit-actions {
        display: flex;
        gap: var(--spacing-1);
    }

    .empty-state {
        text-align: center;
        padding: var(--spacing-8);
        color: var(--color-text-muted);
    }

    @media (max-width: 640px) {
        .page-header {
            flex-direction: column;
            gap: var(--spacing-4);
        }

        .habit-item {
            flex-direction: column;
            align-items: flex-start;
            gap: var(--spacing-3);
        }

        .habit-actions {
            width: 100%;
            justify-content: flex-end;
        }

        .days-selector {
            flex-wrap: wrap;
        }
    }
</style>
