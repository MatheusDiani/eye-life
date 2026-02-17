<script lang="ts">
    import { goto } from "$app/navigation";
    import { onMount } from "svelte";

    let username = $state("");
    let password = $state("");
    let error = $state("");
    let loading = $state(false);

    const API_BASE =
        import.meta.env.VITE_API_URL || "http://localhost:8000/api";

    onMount(() => {
        // If already logged in, redirect to home
        const token = localStorage.getItem("eye_life_token");
        if (token) {
            goto("/");
        }
    });

    async function handleLogin() {
        if (!username.trim() || !password.trim()) {
            error = "Preencha todos os campos";
            return;
        }

        loading = true;
        error = "";

        try {
            const response = await fetch(`${API_BASE}/auth/login`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ username, password }),
            });

            if (!response.ok) {
                const data = await response
                    .json()
                    .catch(() => ({ detail: "Erro desconhecido" }));
                throw new Error(data.detail || "Falha no login");
            }

            const data = await response.json();
            localStorage.setItem("eye_life_token", data.access_token);
            goto("/");
        } catch (e: any) {
            error = e.message || "Erro ao fazer login";
        } finally {
            loading = false;
        }
    }

    function handleKeydown(event: KeyboardEvent) {
        if (event.key === "Enter") {
            handleLogin();
        }
    }
</script>

<svelte:head>
    <title>Login | Eye Life</title>
</svelte:head>

<div class="login-page">
    <div class="login-card">
        <div class="login-header">
            <h1>👁️ Eye Life</h1>
            <p class="text-muted">Faça login para continuar</p>
        </div>

        {#if error}
            <div class="alert alert-error">{error}</div>
        {/if}

        <div class="form-group">
            <label for="username">Usuário</label>
            <input
                id="username"
                type="text"
                class="input"
                bind:value={username}
                onkeydown={handleKeydown}
                placeholder="Seu usuário"
                disabled={loading}
            />
        </div>

        <div class="form-group">
            <label for="password">Senha</label>
            <input
                id="password"
                type="password"
                class="input"
                bind:value={password}
                onkeydown={handleKeydown}
                placeholder="Sua senha"
                disabled={loading}
            />
        </div>

        <button
            class="btn btn-primary btn-full"
            onclick={handleLogin}
            disabled={loading}
        >
            {loading ? "Entrando..." : "Entrar"}
        </button>
    </div>
</div>

<style>
    .login-page {
        min-height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: var(--spacing-4);
        background: var(--color-bg);
    }

    .login-card {
        width: 100%;
        max-width: 400px;
        background: var(--color-surface);
        border: 1px solid var(--color-border);
        border-radius: var(--radius-xl);
        padding: var(--spacing-8);
        box-shadow: var(--shadow-lg);
    }

    .login-header {
        text-align: center;
        margin-bottom: var(--spacing-6);
    }

    .login-header h1 {
        font-size: var(--font-size-3xl);
        margin-bottom: var(--spacing-2);
    }

    .form-group {
        margin-bottom: var(--spacing-4);
    }

    .form-group label {
        display: block;
        margin-bottom: var(--spacing-1);
        font-size: var(--font-size-sm);
        color: var(--color-text-secondary);
    }

    .input {
        width: 100%;
        padding: var(--spacing-3);
        background: var(--color-surface-elevated);
        border: 1px solid var(--color-border);
        border-radius: var(--radius-md);
        color: var(--color-text-primary);
        font-size: var(--font-size-base);
        transition: border-color var(--transition-fast);
    }

    .input:focus {
        outline: none;
        border-color: var(--color-accent);
    }

    .input:disabled {
        opacity: 0.6;
    }

    .btn-full {
        width: 100%;
        padding: var(--spacing-3);
        font-size: var(--font-size-base);
        margin-top: var(--spacing-2);
    }

    .alert-error {
        background: var(--color-danger-muted);
        color: var(--color-danger);
        padding: var(--spacing-3);
        border-radius: var(--radius-md);
        margin-bottom: var(--spacing-4);
        font-size: var(--font-size-sm);
        border: 1px solid var(--color-danger);
    }

    .text-muted {
        color: var(--color-text-muted);
    }
</style>
