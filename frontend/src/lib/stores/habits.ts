import { writable, derived, get } from 'svelte/store';
import { habitsAPI, type Habit, type HabitUpdate } from '$lib/api/client';

function createHabitsStore() {
    const { subscribe, set, update } = writable<Habit[]>([]);
    const loading = writable(false);
    const error = writable<string | null>(null);

    return {
        subscribe,
        loading,
        error,

        async fetch(includeArchived = false) {
            loading.set(true);
            error.set(null);
            try {
                const habits = await habitsAPI.getAll(includeArchived);
                set(habits);
            } catch (e) {
                error.set(e instanceof Error ? e.message : 'Failed to fetch habits');
            } finally {
                loading.set(false);
            }
        },

        async create(habit: { name: string; description?: string; is_repeatable?: boolean; has_timer?: boolean; estimated_duration_seconds?: number; schedule_days?: number[]; start_date?: string }) {
            loading.set(true);
            error.set(null);
            try {
                const newHabit = await habitsAPI.create(habit);
                // Re-fetch all habits to get complete data with computed fields
                const freshHabits = await habitsAPI.getAll(false);
                set(freshHabits);
                return newHabit;
            } catch (e) {
                error.set(e instanceof Error ? e.message : 'Failed to create habit');
                throw e;
            } finally {
                loading.set(false);
            }
        },

        async updateHabit(id: number, data: HabitUpdate) {
            try {
                const updatedHabit = await habitsAPI.update(id, data);
                update(habits =>
                    habits.map(h => (h.id === id ? { ...h, ...updatedHabit } : h))
                );
                return updatedHabit;
            } catch (e) {
                error.set(e instanceof Error ? e.message : 'Failed to update habit');
                throw e;
            }
        },

        async toggleComplete(id: number, completed: boolean) {
            try {
                await habitsAPI.log(id, completed);
                // Optimistic update for completed_today
                update(habits =>
                    habits.map(h =>
                        h.id === id ? { ...h, completed_today: completed } : h
                    )
                );
                // Fetch fresh data to get updated streak values
                const freshHabits = await habitsAPI.getAll(false);
                // Merge with local time_spent_today values to preserve timer data
                update(currentHabits => {
                    const timeMap = new Map(currentHabits.map(h => [h.id, h.time_spent_today]));
                    return freshHabits.map(h => ({
                        ...h,
                        // Keep local time if it's greater (timer might have updated locally)
                        time_spent_today: Math.max(h.time_spent_today, timeMap.get(h.id) || 0)
                    }));
                });
            } catch (e) {
                error.set(e instanceof Error ? e.message : 'Failed to update habit');
            }
        },

        async archive(id: number) {
            try {
                await habitsAPI.archive(id);
                update(habits =>
                    habits.map(h =>
                        h.id === id ? { ...h, is_archived: true } : h
                    )
                );
            } catch (e) {
                error.set(e instanceof Error ? e.message : 'Failed to archive habit');
                throw e;
            }
        },

        async unarchive(id: number) {
            try {
                await habitsAPI.unarchive(id);
                update(habits =>
                    habits.map(h =>
                        h.id === id ? { ...h, is_archived: false } : h
                    )
                );
            } catch (e) {
                error.set(e instanceof Error ? e.message : 'Failed to unarchive habit');
                throw e;
            }
        },

        async delete(id: number) {
            try {
                await habitsAPI.delete(id);
                update(habits => habits.filter(h => h.id !== id));
            } catch (e) {
                error.set(e instanceof Error ? e.message : 'Failed to delete habit');
            }
        },

        async updateTimeSpent(id: number, seconds: number) {
            try {
                const today = new Date().toISOString().split('T')[0];
                // Get current completion status before updating
                const currentHabits = get({ subscribe });
                const habit = currentHabits.find(h => h.id === id);
                const isCompleted = habit?.completed_today || false;

                // Update locally first
                update(habits =>
                    habits.map(h =>
                        h.id === id ? { ...h, time_spent_today: seconds } : h
                    )
                );
                // Persist to backend
                await habitsAPI.updateByDate(today, id, isCompleted, seconds);
            } catch (e) {
                error.set(e instanceof Error ? e.message : 'Failed to update time');
            }
        },

        addTimeSpent(id: number, seconds: number) {
            update(habits =>
                habits.map(h =>
                    h.id === id ? { ...h, time_spent_today: (h.time_spent_today || 0) + seconds } : h
                )
            );
        }
    };
}

export const habits = createHabitsStore();

export const activeHabits = derived(habits, $habits =>
    $habits.filter(h => !h.is_archived)
);

export const archivedHabits = derived(habits, $habits =>
    $habits.filter(h => h.is_archived)
);

export const todayHabits = derived(habits, $habits =>
    $habits.filter(h => !h.is_archived && h.is_scheduled_today)
);

export const completedToday = derived(todayHabits, $habits =>
    $habits.filter(h => h.completed_today).length
);

export const totalHabitsToday = derived(todayHabits, $habits => $habits.length);

export const completionPercentage = derived(
    [completedToday, totalHabitsToday],
    ([$completed, $total]) => ($total > 0 ? Math.round(($completed / $total) * 100) : 0)
);
