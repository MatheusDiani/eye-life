<script lang="ts">
    import { onMount } from "svelte";
    import { notes } from "$lib/stores/notes";
    import type { Note } from "$lib/api/client";

    let showForm = $state(false);
    let editingNote: Note | null = $state(null);
    let noteContent = $state("");
    let submitting = $state(false);

    const today = new Date().toISOString().split("T")[0];

    onMount(() => {
        notes.fetchToday();
    });

    function resetForm() {
        noteContent = "";
        editingNote = null;
        showForm = false;
    }

    function editNote(note: Note) {
        editingNote = note;
        noteContent = note.content;
        showForm = true;
    }

    async function handleSubmit() {
        if (!noteContent.trim()) return;

        submitting = true;
        try {
            if (editingNote) {
                await notes.updateNote(editingNote.id, {
                    content: noteContent.trim(),
                });
            } else {
                await notes.create({
                    content: noteContent.trim(),
                    date: today,
                });
            }
            resetForm();
        } finally {
            submitting = false;
        }
    }

    async function deleteNote(id: number) {
        if (confirm("Tem certeza que deseja excluir esta nota?")) {
            await notes.delete(id);
        }
    }

    function formatTime(dateString: string): string {
        return new Date(dateString).toLocaleTimeString("pt-BR", {
            hour: "2-digit",
            minute: "2-digit",
        });
    }

    function getPreview(content: string): string {
        if (content.length <= 50) return content;
        return content.substring(0, 50) + "...";
    }
</script>

<svelte:head>
    <title>Notas | Eye Life</title>
</svelte:head>

<div class="notes-page">
    <header class="page-header">
        <div>
            <h1>Notas do Dia</h1>
            <p class="text-muted">
                {new Date().toLocaleDateString("pt-BR", {
                    weekday: "long",
                    day: "numeric",
                    month: "long",
                })}
            </p>
        </div>
        <div class="header-actions">
            <a href="/history" class="btn">📅 Ver Histórico</a>
            <button
                class="btn btn-primary"
                onclick={() => {
                    resetForm();
                    showForm = !showForm;
                }}
            >
                {showForm ? "Cancelar" : "+ Nova Nota"}
            </button>
        </div>
    </header>

    {#if showForm}
        <form
            class="card note-form animate-slide-up"
            onsubmit={(e) => {
                e.preventDefault();
                handleSubmit();
            }}
        >
            <h3>{editingNote ? "Editar Nota" : "Nova Nota"}</h3>

            <div class="form-group">
                <textarea
                    id="note-content"
                    class="textarea"
                    placeholder="Escreva sua nota aqui..."
                    bind:value={noteContent}
                    required
                ></textarea>
            </div>

            <div class="form-actions">
                {#if editingNote}
                    <button type="button" class="btn" onclick={resetForm}
                        >Cancelar</button
                    >
                {/if}
                <button
                    type="submit"
                    class="btn btn-primary"
                    disabled={submitting}
                >
                    {submitting
                        ? "Salvando..."
                        : editingNote
                          ? "Salvar"
                          : "Criar Nota"}
                </button>
            </div>
        </form>
    {/if}

    {#if $notes.length === 0}
        <div class="empty-state card">
            <span class="empty-state-icon">📝</span>
            <p>Nenhuma nota registrada hoje</p>
            <button class="btn btn-primary" onclick={() => (showForm = true)}>
                Criar primeira nota
            </button>
        </div>
    {:else}
        <div class="notes-list">
            {#each $notes as note (note.id)}
                <article class="card note-card">
                    <div class="note-header">
                        <span class="note-time"
                            >{formatTime(note.created_at)}</span
                        >
                    </div>

                    <p class="note-content">{note.content}</p>

                    <div class="note-actions">
                        <button
                            class="btn btn-ghost btn-sm"
                            onclick={() => editNote(note)}
                        >
                            ✏️ Editar
                        </button>
                        <button
                            class="btn btn-ghost btn-sm"
                            onclick={() => deleteNote(note.id)}
                        >
                            🗑 Excluir
                        </button>
                    </div>
                </article>
            {/each}
        </div>
    {/if}
</div>

<style>
    .notes-page {
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

    .note-form {
        margin-bottom: var(--spacing-6);
    }

    .note-form h3 {
        margin-bottom: var(--spacing-4);
    }

    .form-group {
        margin-bottom: var(--spacing-4);
    }

    .form-actions {
        display: flex;
        justify-content: flex-end;
        gap: var(--spacing-2);
    }

    .notes-list {
        display: flex;
        flex-direction: column;
        gap: var(--spacing-4);
    }

    .note-card {
        padding: var(--spacing-5);
    }

    .note-header {
        display: flex;
        justify-content: flex-end;
        margin-bottom: var(--spacing-3);
    }

    .note-time {
        font-size: var(--font-size-xs);
        color: var(--color-text-muted);
        font-family: var(--font-mono);
    }

    .note-content {
        color: var(--color-text-primary);
        line-height: var(--line-height-relaxed);
        margin-bottom: var(--spacing-4);
        white-space: pre-wrap;
    }

    .note-actions {
        display: flex;
        gap: var(--spacing-2);
        border-top: 1px solid var(--color-border);
        padding-top: var(--spacing-3);
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
            flex-direction: column;
        }
    }
</style>
