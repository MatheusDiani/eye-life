<script lang="ts">
    import { onMount } from "svelte";
    import { notesHistory } from "$lib/stores/notes";
    import type { NotesByDate } from "$lib/api/client";

    onMount(() => {
        notesHistory.fetch();
    });

    function formatDate(dateString: string): string {
        const date = new Date(dateString);
        const today = new Date();
        const yesterday = new Date(today);
        yesterday.setDate(yesterday.getDate() - 1);

        if (date.toDateString() === today.toDateString()) {
            return "Hoje";
        } else if (date.toDateString() === yesterday.toDateString()) {
            return "Ontem";
        }

        return date.toLocaleDateString("pt-BR", {
            weekday: "long",
            day: "numeric",
            month: "long",
            year:
                date.getFullYear() !== today.getFullYear()
                    ? "numeric"
                    : undefined,
        });
    }

    function formatTime(dateString: string): string {
        return new Date(dateString).toLocaleTimeString("pt-BR", {
            hour: "2-digit",
            minute: "2-digit",
        });
    }

    function formatDateForFile(dateString: string): string {
        const date = new Date(dateString);
        return date.toLocaleDateString("pt-BR", {
            weekday: "long",
            day: "numeric",
            month: "long",
            year: "numeric",
        });
    }

    function downloadAllNotes() {
        const history = $notesHistory as NotesByDate[];
        if (history.length === 0) return;

        let content =
            "═══════════════════════════════════════════════════════\n";
        content += "                    MINHAS NOTAS\n";
        content += "            Eye Life - Histórico Completo\n";
        content +=
            "═══════════════════════════════════════════════════════\n\n";

        for (const dayGroup of history) {
            const dateHeader = formatDateForFile(dayGroup.date);
            content += `\n▌ ${dateHeader.toUpperCase()}\n`;
            content +=
                "───────────────────────────────────────────────────────\n";

            for (const note of dayGroup.notes) {
                const time = formatTime(note.created_at);
                content += `\n[${time}]\n`;
                content += `${note.content}\n`;
            }

            content += "\n";
        }

        content +=
            "\n═══════════════════════════════════════════════════════\n";
        content += `Exportado em: ${new Date().toLocaleString("pt-BR")}\n`;
        content += "═══════════════════════════════════════════════════════\n";

        // Create and download file
        const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `notas-eye-life-${new Date().toISOString().split("T")[0]}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
</script>

<svelte:head>
    <title>Histórico de Notas | Eye Life</title>
</svelte:head>

<div class="history-page">
    <header class="page-header">
        <div>
            <h1>Histórico de Notas</h1>
            <p class="text-muted">Todas as suas notas organizadas por dia</p>
        </div>
        <div class="header-actions">
            {#if $notesHistory.length > 0}
                <button class="btn" onclick={downloadAllNotes}>
                    📥 Baixar Todas
                </button>
            {/if}
            <a href="/notes" class="btn btn-primary">+ Nova Nota</a>
        </div>
    </header>

    {#if $notesHistory.length === 0}
        <div class="empty-state card">
            <span class="empty-state-icon">📅</span>
            <p>Nenhuma nota registrada ainda</p>
            <a href="/notes" class="btn btn-primary">Criar primeira nota</a>
        </div>
    {:else}
        <div class="timeline">
            {#each $notesHistory as dayGroup (dayGroup.date)}
                <div class="timeline-day animate-fade-in">
                    <div class="timeline-date">
                        <span class="date-marker"></span>
                        <h2>{formatDate(dayGroup.date)}</h2>
                        <span class="note-count badge">
                            {dayGroup.notes.length} nota{dayGroup.notes
                                .length !== 1
                                ? "s"
                                : ""}
                        </span>
                    </div>

                    <div class="day-notes">
                        {#each dayGroup.notes as note (note.id)}
                            <article class="card note-card">
                                <div class="note-header">
                                    <span class="note-time"
                                        >{formatTime(note.created_at)}</span
                                    >
                                </div>

                                <p class="note-content">{note.content}</p>
                            </article>
                        {/each}
                    </div>
                </div>
            {/each}
        </div>
    {/if}
</div>

<style>
    .history-page {
        max-width: 800px;
        margin: 0 auto;
    }

    .page-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: var(--spacing-8);
    }

    .page-header h1 {
        margin-bottom: var(--spacing-1);
    }

    .header-actions {
        display: flex;
        gap: var(--spacing-2);
    }

    .timeline {
        position: relative;
    }

    .timeline::before {
        content: "";
        position: absolute;
        left: 8px;
        top: 0;
        bottom: 0;
        width: 2px;
        background: linear-gradient(
            180deg,
            var(--color-border) 0%,
            transparent 100%
        );
    }

    .timeline-day {
        position: relative;
        padding-left: var(--spacing-10);
        margin-bottom: var(--spacing-8);
    }

    .timeline-date {
        display: flex;
        align-items: center;
        gap: var(--spacing-3);
        margin-bottom: var(--spacing-4);
    }

    .date-marker {
        position: absolute;
        left: 0;
        width: 18px;
        height: 18px;
        background-color: var(--color-surface);
        border: 2px solid var(--color-accent);
        border-radius: 50%;
    }

    .timeline-date h2 {
        font-size: var(--font-size-lg);
        font-weight: var(--font-weight-semibold);
        text-transform: capitalize;
    }

    .note-count {
        font-size: var(--font-size-xs);
    }

    .day-notes {
        display: flex;
        flex-direction: column;
        gap: var(--spacing-3);
    }

    .note-card {
        padding: var(--spacing-5);
        border-left: 3px solid var(--color-accent);
    }

    .note-header {
        display: flex;
        justify-content: flex-end;
        margin-bottom: var(--spacing-2);
    }

    .note-time {
        font-size: var(--font-size-xs);
        color: var(--color-text-muted);
        font-family: var(--font-mono);
    }

    .note-content {
        color: var(--color-text-primary);
        font-size: var(--font-size-base);
        line-height: var(--line-height-relaxed);
        white-space: pre-wrap;
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

        .timeline::before {
            left: 6px;
        }

        .timeline-day {
            padding-left: var(--spacing-8);
        }

        .date-marker {
            width: 14px;
            height: 14px;
        }
    }
</style>
