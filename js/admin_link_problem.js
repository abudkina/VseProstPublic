import * as auth from './authorizationFunctions.js';

const LIST_URL = '/temporary-link-problems';
const PREFIX = '/temporary-link-problems';

async function fetchList() {
    const res = await fetch(API_CONFIG.buildURL(LIST_URL), {
        method: 'GET',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' }
    });
    if (res.status === 401) {
        const ok = await auth.refreshToken();
        if (ok) return fetchList();
        throw new Error('Требуется авторизация');
    }
    if (!res.ok) throw new Error('Ошибка загрузки');
    const data = await res.json();
    return data.items || [];
}

async function approve(id) {
    const res = await fetch(API_CONFIG.buildURL(`${PREFIX}/${id}/approve`), {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' }
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || 'Ошибка');
    }
}

async function remove(id) {
    const res = await fetch(API_CONFIG.buildURL(`${PREFIX}/${id}`), {
        method: 'DELETE',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' }
    });
    if (!res.ok) throw new Error('Ошибка удаления');
}

function render(items) {
    const tbody = document.getElementById('tbody');
    const emptyMsg = document.getElementById('emptyMsg');
    tbody.innerHTML = '';
    if (!items.length) {
        emptyMsg.style.display = 'block';
        return;
    }
    emptyMsg.style.display = 'none';
    items.forEach(item => {
        const tr = document.createElement('tr');
        tr.dataset.id = item.id;
        tr.innerHTML = `
            <td>${escapeHtml(item.problem_name || '')}</td>
            <td>${escapeHtml(item.link_problem_name || '')}</td>
            <td class="admin-links-actions">
                <button type="button" class="btn-approve" data-id="${item.id}">Сохранить</button>
                <button type="button" class="btn-delete" data-id="${item.id}">Удалить</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function escapeHtml(s) {
    const div = document.createElement('div');
    div.textContent = s;
    return div.innerHTML;
}

async function load() {
    try {
        const items = await fetchList();
        render(items);
    } catch (e) {
        if (e.message && e.message.includes('авторизация')) {
            window.location.href = window.pageUrl('authorization.html');
            return;
        }
        document.getElementById('tbody').innerHTML = '<tr><td colspan="3">Ошибка загрузки</td></tr>';
    }
}

document.addEventListener('DOMContentLoaded', async () => {
    try {
        await auth.checkAuth(true);
    } catch {
        window.location.href = window.pageUrl('authorization.html');
        return;
    }
    await load();

    document.getElementById('tbody').addEventListener('click', async (e) => {
        const id = e.target.dataset?.id;
        if (!id) return;
        const row = e.target.closest('tr');
        if (e.target.classList.contains('btn-approve')) {
            e.target.disabled = true;
            try {
                await approve(id);
                if (row) row.remove();
                const tbody = document.getElementById('tbody');
                if (tbody.children.length === 0) document.getElementById('emptyMsg').style.display = 'block';
            } catch (err) {
                alert(err.message || 'Ошибка');
                e.target.disabled = false;
            }
        } else if (e.target.classList.contains('btn-delete')) {
            e.target.disabled = true;
            try {
                await remove(id);
                if (row) row.remove();
                if (document.getElementById('tbody').children.length === 0) document.getElementById('emptyMsg').style.display = 'block';
            } catch (err) {
                alert(err.message || 'Ошибка');
                e.target.disabled = false;
            }
        }
    });

    document.getElementById('favoritesLink')?.addEventListener('click', (ev) => {
        ev.preventDefault();
        if (!localStorage.getItem('isLoggedIn')) {
            sessionStorage.setItem('redirectAfterLogin', window.pageUrl('favourites.html'));
            window.location.href = window.pageUrl('authorization.html');
            return;
        }
        auth.checkAuth(true).then(() => { window.location.href = window.pageUrl('favourites.html'); }).catch(() => {});
    });
    document.getElementById('profileBtn')?.addEventListener('click', () => {
        auth.checkAuth(false).then(() => { window.location.href = window.pageUrl('profile.html'); }).catch(() => {
            sessionStorage.setItem('redirectAfterLogin', window.location.href);
            window.location.href = window.pageUrl('authorization.html');
        });
    });
});
