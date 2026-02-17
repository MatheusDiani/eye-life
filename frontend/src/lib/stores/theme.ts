import { writable } from 'svelte/store';
import { browser } from '$app/environment';

export type ThemeName = 'dark' | 'light' | 'ocean' | 'forest' | 'sunset';

export interface Theme {
    name: ThemeName;
    label: string;
    emoji: string;
}

export const themes: Theme[] = [
    { name: 'dark', label: 'Escuro', emoji: '🌙' },
    { name: 'light', label: 'Claro', emoji: '☀️' },
    { name: 'ocean', label: 'Oceano', emoji: '🌊' },
    { name: 'forest', label: 'Floresta', emoji: '🌲' },
    { name: 'sunset', label: 'Pôr do Sol', emoji: '🌅' },
];

function getInitialTheme(): ThemeName {
    if (browser) {
        const saved = localStorage.getItem('theme') as ThemeName;
        if (saved && themes.some(t => t.name === saved)) {
            return saved;
        }
    }
    return 'dark';
}

function createThemeStore() {
    const { subscribe, set } = writable<ThemeName>(getInitialTheme());

    return {
        subscribe,
        setTheme(theme: ThemeName) {
            set(theme);
            if (browser) {
                localStorage.setItem('theme', theme);
                document.documentElement.setAttribute('data-theme', theme);
            }
        },
        init() {
            if (browser) {
                const theme = getInitialTheme();
                document.documentElement.setAttribute('data-theme', theme);
            }
        }
    };
}

export const theme = createThemeStore();
