import { writable, get } from 'svelte/store';
import { timersAPI, type TimerStatus } from '$lib/api/client';
import { habits } from './habits';

interface ActiveTimer {
    habitId: number;
    startTime: Date;
    elapsedSeconds: number;
    pausedSeconds: number; // Tempo acumulado de pausas anteriores
    isPaused: boolean;
}

function createTimerStore() {
    const { subscribe, set, update } = writable<ActiveTimer | null>(null);
    const loading = writable(false);
    const error = writable<string | null>(null);

    let tickInterval: number | null = null;

    function startTicking() {
        if (tickInterval) return;

        tickInterval = window.setInterval(() => {
            update(timer => {
                if (!timer || timer.isPaused) return timer;
                const elapsed = timer.pausedSeconds + Math.floor((Date.now() - timer.startTime.getTime()) / 1000);
                return { ...timer, elapsedSeconds: elapsed };
            });
        }, 1000);
    }

    function stopTicking() {
        if (tickInterval) {
            window.clearInterval(tickInterval);
            tickInterval = null;
        }
    }

    return {
        subscribe,
        loading,
        error,

        async checkStatus(habitId: number): Promise<TimerStatus | null> {
            try {
                const status = await timersAPI.getStatus(habitId);
                if (status.is_running && status.current_session) {
                    const startTime = new Date(status.current_session.start_time);
                    const elapsed = Math.floor((Date.now() - startTime.getTime()) / 1000);
                    set({
                        habitId,
                        startTime,
                        elapsedSeconds: elapsed,
                        pausedSeconds: 0,
                        isPaused: false
                    });
                    startTicking();
                }
                return status;
            } catch (e) {
                return null;
            }
        },

        async start(habitId: number, initialSeconds = 0) {
            loading.set(true);
            error.set(null);
            try {
                await timersAPI.start(habitId);
                set({
                    habitId,
                    startTime: new Date(),
                    elapsedSeconds: initialSeconds,
                    pausedSeconds: initialSeconds,
                    isPaused: false
                });
                startTicking();
            } catch (e) {
                error.set(e instanceof Error ? e.message : 'Failed to start timer');
                throw e;
            } finally {
                loading.set(false);
            }
        },

        async pause() {
            const currentTimer = get({ subscribe });
            if (!currentTimer || currentTimer.isPaused) return;

            // Calculate elapsed time
            const currentElapsed = currentTimer.pausedSeconds + Math.floor((Date.now() - currentTimer.startTime.getTime()) / 1000);

            // Stop the backend timer to persist the time
            try {
                await timersAPI.stop(currentTimer.habitId);
                // Update habit's time in the store
                habits.addTimeSpent(currentTimer.habitId, currentElapsed - currentTimer.pausedSeconds);
            } catch (e) {
                // Even if backend fails, update local state
                console.error('Failed to persist pause:', e);
            }

            update(timer => {
                if (!timer) return timer;
                return {
                    ...timer,
                    isPaused: true,
                    pausedSeconds: currentElapsed,
                    elapsedSeconds: currentElapsed
                };
            });
        },

        async resume() {
            const currentTimer = get({ subscribe });
            if (!currentTimer || !currentTimer.isPaused) return;

            // Start a new backend session
            try {
                await timersAPI.start(currentTimer.habitId);
            } catch (e) {
                console.error('Failed to resume timer:', e);
            }

            update(timer => {
                if (!timer) return timer;
                return {
                    ...timer,
                    isPaused: false,
                    startTime: new Date() // Reinicia o contador de tempo
                };
            });
        },

        async stop() {
            const currentTimer = get({ subscribe });
            if (!currentTimer) return;

            loading.set(true);
            error.set(null);
            try {
                const result = await timersAPI.stop(currentTimer.habitId);
                stopTicking();

                // Add session duration to habit's total time spent
                habits.addTimeSpent(currentTimer.habitId, result.duration_seconds);

                set(null);
                return result;
            } catch (e) {
                error.set(e instanceof Error ? e.message : 'Failed to stop timer');
                throw e;
            } finally {
                loading.set(false);
            }
        },

        async reset() {
            const currentTimer = get({ subscribe });
            if (!currentTimer) return;

            loading.set(true);
            error.set(null);
            try {
                // Call backend to reset saved time
                await timersAPI.reset(currentTimer.habitId);

                // Reset local timer state
                set({
                    ...currentTimer,
                    startTime: new Date(),
                    elapsedSeconds: 0,
                    pausedSeconds: 0,
                    isPaused: false
                });

                // Update habit's time spent to 0
                habits.updateTimeSpent(currentTimer.habitId, 0);
            } catch (e) {
                error.set(e instanceof Error ? e.message : 'Failed to reset timer');
            } finally {
                loading.set(false);
            }
        },

        getElapsedFormatted(): string {
            const timer = get({ subscribe });
            if (!timer) return '00:00:00';
            return formatTime(timer.elapsedSeconds);
        },

        isRunning(): boolean {
            const timer = get({ subscribe });
            return timer !== null && !timer.isPaused;
        },

        isPaused(): boolean {
            const timer = get({ subscribe });
            return timer !== null && timer.isPaused;
        },

        isRunningFor(habitId: number): boolean {
            const timer = get({ subscribe });
            return timer !== null && timer.habitId === habitId;
        }
    };
}

export function formatTime(seconds: number): string {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    return [hrs, mins, secs]
        .map(v => v.toString().padStart(2, '0'))
        .join(':');
}

export const timer = createTimerStore();
