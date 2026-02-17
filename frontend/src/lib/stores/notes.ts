import { writable } from 'svelte/store';
import { notesAPI, type Note, type NotesByDate } from '$lib/api/client';

function createNotesStore() {
    const { subscribe, set, update } = writable<Note[]>([]);
    const loading = writable(false);
    const error = writable<string | null>(null);

    return {
        subscribe,
        loading,
        error,

        async fetchToday() {
            loading.set(true);
            error.set(null);
            try {
                const notes = await notesAPI.getToday();
                set(notes);
            } catch (e) {
                error.set(e instanceof Error ? e.message : 'Failed to fetch notes');
            } finally {
                loading.set(false);
            }
        },

        async fetchByDate(date: string) {
            loading.set(true);
            error.set(null);
            try {
                const notes = await notesAPI.getAll(date);
                set(notes);
            } catch (e) {
                error.set(e instanceof Error ? e.message : 'Failed to fetch notes');
            } finally {
                loading.set(false);
            }
        },

        async create(note: { content: string; date: string }) {
            loading.set(true);
            error.set(null);
            try {
                const newNote = await notesAPI.create(note);
                update(notes => [newNote, ...notes]);
                return newNote;
            } catch (e) {
                error.set(e instanceof Error ? e.message : 'Failed to create note');
                throw e;
            } finally {
                loading.set(false);
            }
        },

        async updateNote(id: number, data: { content?: string }) {
            try {
                const updatedNote = await notesAPI.update(id, data);
                update(notes =>
                    notes.map(n => (n.id === id ? updatedNote : n))
                );
                return updatedNote;
            } catch (e) {
                error.set(e instanceof Error ? e.message : 'Failed to update note');
                throw e;
            }
        },

        async delete(id: number) {
            try {
                await notesAPI.delete(id);
                update(notes => notes.filter(n => n.id !== id));
            } catch (e) {
                error.set(e instanceof Error ? e.message : 'Failed to delete note');
            }
        }
    };
}

function createNotesHistoryStore() {
    const { subscribe, set } = writable<NotesByDate[]>([]);
    const loading = writable(false);
    const error = writable<string | null>(null);

    return {
        subscribe,
        loading,
        error,

        async fetch(startDate?: string, endDate?: string) {
            loading.set(true);
            error.set(null);
            try {
                const notesByDate = await notesAPI.getByDate(startDate, endDate);
                set(notesByDate);
            } catch (e) {
                error.set(e instanceof Error ? e.message : 'Failed to fetch notes history');
            } finally {
                loading.set(false);
            }
        }
    };
}

export const notes = createNotesStore();
export const notesHistory = createNotesHistoryStore();
