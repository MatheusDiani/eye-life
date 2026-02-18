const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

// ==================== Types ====================

export interface Habit {
    id: number;
    name: string;
    description: string | null;
    is_repeatable: boolean;
    has_timer: boolean;
    estimated_duration_seconds: number | null;  // Estimated daily time in seconds
    schedule_days: number[] | null;  // 0=Monday, 6=Sunday
    start_date: string | null;  // Date when habit starts (YYYY-MM-DD)
    is_active: boolean;
    is_archived: boolean;
    created_at: string;
    completed_today: boolean;
    time_spent_today: number;
    carryover_seconds: number;  // Time carried from previous day (excess)
    deficit_seconds: number;    // Time remaining from previous day (not completed)
    streak: number;
    is_scheduled_today: boolean;
}

export interface HabitCreate {
    name: string;
    description?: string;
    is_repeatable?: boolean;
    has_timer?: boolean;
    estimated_duration_seconds?: number;
    schedule_days?: number[];
    start_date?: string;  // YYYY-MM-DD format
}

export interface HabitUpdate {
    name?: string;
    description?: string;
    is_repeatable?: boolean;
    has_timer?: boolean;
    estimated_duration_seconds?: number | null;
    schedule_days?: number[];
    start_date?: string | null;
    is_archived?: boolean;
}

export interface HabitStats {
    habit_id: number;
    habit_name: string;
    period_days: number;
    completed_days: number;
    completion_rate: number;
    total_time_seconds: number;
    current_streak: number;
    logs: Array<{
        date: string;
        completed: boolean;
        time_spent_seconds: number;
    }>;
}

export interface HabitDayLog {
    habit_id: number;
    habit_name: string;
    has_timer: boolean;
    estimated_duration_seconds: number | null;
    is_scheduled: boolean;
    completed: boolean;
    time_spent_seconds: number;
    carryover_seconds: number;
    deficit_seconds: number;
}

export interface Note {
    id: number;
    content: string;
    date: string;
    created_at: string;
    updated_at: string;
}

export interface NoteCreate {
    content: string;
    date: string;
}

export interface NotesByDate {
    date: string;
    notes: Note[];
}

export interface TimerStatus {
    is_running: boolean;
    current_session: TimerSession | null;
    total_time_today: number;
}

export interface TimerSession {
    id: number;
    habit_id: number;
    date: string;
    start_time: string;
    end_time: string | null;
    duration_seconds: number;
    is_running: boolean;
}

export interface DashboardStats {
    total_habits: number;
    completed_today: number;
    completion_percentage: number;
    total_time_today: number;
    current_streak: number;
    notes_today: number;
}

export interface DailyProgress {
    date: string;
    completed: number;
    total: number;
    percentage: number;
}

// ==================== API Functions ====================

function getAuthHeaders(): Record<string, string> {
    const token = typeof window !== 'undefined' ? localStorage.getItem('eye_life_token') : null;
    return token ? { 'Authorization': `Bearer ${token}` } : {};
}

async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...getAuthHeaders(),
            ...options?.headers,
        },
    });

    if (response.status === 401) {
        // Token expired or invalid, redirect to login
        if (typeof window !== 'undefined') {
            localStorage.removeItem('eye_life_token');
            window.location.href = '/login';
        }
        throw new Error('Sessão expirada. Faça login novamente.');
    }

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(error.detail || 'Request failed');
    }

    return response.json();
}

// ==================== Habits ====================

export const habitsAPI = {
    getAll: (includeArchived = false) =>
        fetchAPI<Habit[]>(`/habits${includeArchived ? '?include_archived=true' : ''}`),

    get: (id: number) => fetchAPI<Habit>(`/habits/${id}`),

    create: (habit: HabitCreate) =>
        fetchAPI<Habit>('/habits', {
            method: 'POST',
            body: JSON.stringify(habit),
        }),

    update: (id: number, habit: HabitUpdate) =>
        fetchAPI<Habit>(`/habits/${id}`, {
            method: 'PUT',
            body: JSON.stringify(habit),
        }),

    delete: (id: number) =>
        fetchAPI<{ message: string }>(`/habits/${id}`, {
            method: 'DELETE',
        }),

    archive: (id: number) =>
        fetchAPI<{ message: string }>(`/habits/${id}/archive`, {
            method: 'POST',
        }),

    unarchive: (id: number) =>
        fetchAPI<{ message: string }>(`/habits/${id}/unarchive`, {
            method: 'POST',
        }),

    log: (id: number, completed: boolean, timeSpentSeconds = 0) =>
        fetchAPI<any>(`/habits/${id}/log`, {
            method: 'POST',
            body: JSON.stringify({ completed, time_spent_seconds: timeSpentSeconds }),
        }),

    getStats: (id: number, days = 30) =>
        fetchAPI<HabitStats>(`/habits/${id}/stats?days=${days}`),

    getLogs: (id: number, days = 30) =>
        fetchAPI<any[]>(`/habits/${id}/logs?days=${days}`),

    getByDate: (date: string) =>
        fetchAPI<HabitDayLog[]>(`/habits/by-date/${date}`),

    updateByDate: (date: string, habitId: number, completed: boolean, timeSpentSeconds = 0) =>
        fetchAPI<any>(`/habits/by-date/${date}/${habitId}?completed=${completed}&time_spent_seconds=${timeSpentSeconds}`, {
            method: 'PUT',
        }),
};

// ==================== Notes ====================

export const notesAPI = {
    getAll: (date?: string) =>
        fetchAPI<Note[]>(`/notes${date ? `?note_date=${date}` : ''}`),

    getToday: () => fetchAPI<Note[]>('/notes/today'),

    getByDate: (startDate?: string, endDate?: string) => {
        const params = new URLSearchParams();
        if (startDate) params.append('start_date', startDate);
        if (endDate) params.append('end_date', endDate);
        const query = params.toString();
        return fetchAPI<NotesByDate[]>(`/notes/by-date${query ? `?${query}` : ''}`);
    },

    get: (id: number) => fetchAPI<Note>(`/notes/${id}`),

    create: (note: NoteCreate) =>
        fetchAPI<Note>('/notes', {
            method: 'POST',
            body: JSON.stringify(note),
        }),

    update: (id: number, note: Partial<NoteCreate>) =>
        fetchAPI<Note>(`/notes/${id}`, {
            method: 'PUT',
            body: JSON.stringify(note),
        }),

    delete: (id: number) =>
        fetchAPI<{ message: string }>(`/notes/${id}`, {
            method: 'DELETE',
        }),
};

// ==================== Timers ====================

export const timersAPI = {
    start: (habitId: number) =>
        fetchAPI<TimerSession>('/timers/start', {
            method: 'POST',
            body: JSON.stringify({ habit_id: habitId }),
        }),

    stop: (habitId: number) =>
        fetchAPI<TimerSession>('/timers/stop', {
            method: 'POST',
            body: JSON.stringify({ habit_id: habitId }),
        }),

    getStatus: (habitId: number) =>
        fetchAPI<TimerStatus>(`/timers/${habitId}/status`),

    getTodayTime: (habitId: number) =>
        fetchAPI<{ habit_id: number; total_seconds: number }>(`/timers/${habitId}/today`),

    reset: (habitId: number) =>
        fetchAPI<{ message: string; habit_id: number }>(`/timers/${habitId}/reset`, {
            method: 'POST',
        }),
};

// ==================== Dashboard ====================

export const dashboardAPI = {
    getStats: () => fetchAPI<DashboardStats>('/dashboard/stats'),

    getProgress: (days = 7) =>
        fetchAPI<DailyProgress[]>(`/dashboard/progress?days=${days}`),
};

// ==================== Settings ====================

export interface Settings {
    carryover_enabled: boolean;
}

export const settingsAPI = {
    get: () => fetchAPI<Settings>('/settings'),

    update: (settings: Partial<Settings>) =>
        fetchAPI<Settings>('/settings', {
            method: 'PUT',
            body: JSON.stringify(settings),
        }),

    resetAll: () =>
        fetchAPI<{ message: string }>('/settings/reset-all', {
            method: 'DELETE',
        }),
};
