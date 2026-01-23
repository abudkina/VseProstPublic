// profile.js
import * as auth from './authorizationFunctions.js';
import { updateCartIconState } from './cartFunctions.js';

const API_BASE = window.location.origin + '/api';

let currentUser = null;
let refreshTimer = null;
let tokenExpiry = null;

// Обновляем состояние корзины при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    updateCartIconState();
});

// Проверяем авторизацию при загрузке
(async () => {
    try {
        const userId = await auth.checkAuth(true);
        if (userId) {
            await loadProfile();
            // Обновляем корзину после загрузки профиля
            updateCartIconState();
        }
    } catch (error) {
        console.error('Ошибка при инициализации профиля:', error);
        // checkAuth уже перенаправит на страницу авторизации, если нужно
        // Обновляем корзину даже при ошибке (покажет 0)
        updateCartIconState();
    }
})();

// Загрузка профиля
async function loadProfile() {
    try {
        const response = await fetch(`${API_BASE}/user/profile`, {
            method: 'GET',
            credentials: 'include', // Включаем cookies для отправки токена
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            if (response.status === 401) {
                // Попытка обновить токен
                try {
                    await auth.refreshToken();
                    return loadProfile(); // Повторяем запрос после обновления
                } catch (refreshError) {
                    console.warn('Не удалось обновить токен:', refreshError);
                    return;
                }
            }
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || 'Ошибка загрузки профиля');
        }

        const userData = await response.json();
        currentUser = userData;
        
        // Убеждаемся, что у пользователя есть id (проверяем оба варианта)
        if (!currentUser.id) {
            currentUser.id = currentUser.ID || currentUser.userID || currentUser.user_id;
        }
        if (!currentUser.id && currentUser.ID) {
            currentUser.id = currentUser.ID;
        }
        
        displayProfile(userData);
        displayStats(userData.stats || {});
    } catch (error) {
        console.error('Ошибка загрузки профиля:', error);
        showToast('Ошибка загрузки профиля', 'error');
    }
}

// Отображение профиля
function displayProfile(userData) {
    // Аватар
    const avatarImg = document.getElementById('avatar-img');
    if (userData.image) {
        avatarImg.src = `/${userData.image}`;
    } else {
        avatarImg.src = '/assets/icons/user-list_18357678.png';
    }

    // Имя пользователя
    document.getElementById('username-display').textContent = userData.username || 'Пользователь';
    document.getElementById('edit-username').value = userData.username || '';

    // Email
    document.getElementById('email-display').textContent = userData.email || 'Не указан';
    document.getElementById('edit-email').value = userData.email || '';

    // Дата регистрации
    if (userData.created_date) {
        const date = new Date(userData.created_date);
        const formattedDate = date.toLocaleDateString('ru-RU', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
        document.getElementById('join-date').textContent = `Дата регистрации: ${formattedDate}`;
    }
}

// Отображение статистики
function displayStats(stats) {
    const problemsCountEl = document.getElementById('problems-count');
    const solutionsCountEl = document.getElementById('solutions-count');
    const favProblemsCountEl = document.getElementById('fav-problems-count');
    const favSolutionsCountEl = document.getElementById('fav-solutions-count');
    
    if (problemsCountEl) {
        problemsCountEl.textContent = stats.problems_created || 0;
    }
    if (solutionsCountEl) {
        solutionsCountEl.textContent = stats.solutions_created || 0;
    }
    if (favProblemsCountEl) {
        favProblemsCountEl.textContent = stats.favourite_problems || 0;
    }
    if (favSolutionsCountEl) {
        favSolutionsCountEl.textContent = stats.favourite_solutions || 0;
    }
}

// Загрузка аватара
document.getElementById('avatar-input')?.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Проверка размера файла (макс 5MB)
    if (file.size > 5 * 1024 * 1024) {
        showToast('Файл слишком большой. Максимальный размер: 5MB', 'error');
        return;
    }

    // Проверка типа файла
    if (!file.type.startsWith('image/')) {
        showToast('Выберите изображение', 'error');
        return;
    }

    const formData = new FormData();
    formData.append('avatar', file);

    try {
        const response = await fetch(`${API_BASE}/user/profile/avatar`, {
            method: 'POST',
            credentials: 'include', // Используем cookies для авторизации
            body: formData
        });

        if (!response.ok) {
            if (response.status === 401) {
                try {
                    await auth.refreshToken();
                    return document.getElementById('avatar-input').dispatchEvent(new Event('change'));
                } catch (refreshError) {
                    console.warn('Не удалось обновить токен:', refreshError);
                }
            }
            const error = await response.json().catch(() => ({}));
            throw new Error(error.error || 'Ошибка загрузки аватара');
        }

        const data = await response.json();
        document.getElementById('avatar-img').src = `/${data.image}`;
        showToast('Аватар успешно загружен', 'success');
    } catch (error) {
        console.error('Ошибка загрузки аватара:', error);
        showToast(error.message || 'Ошибка загрузки аватара', 'error');
    } finally {
        e.target.value = '';
    }
});

// Редактирование профиля
document.getElementById('edit-profile-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();

    const formData = {
        username: document.getElementById('edit-username').value.trim(),
        email: document.getElementById('edit-email').value.trim()
    };

    if (!formData.username || !formData.email) {
        showToast('Заполните все поля', 'error');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/user/profile`, {
            method: 'PUT',
            credentials: 'include', // Включаем cookies для отправки токена
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        if (!response.ok) {
            if (response.status === 401) {
                try {
                    await auth.refreshToken();
                    return document.getElementById('edit-profile-form').dispatchEvent(new Event('submit'));
                } catch (refreshError) {
                    console.warn('Не удалось обновить токен:', refreshError);
                }
            }
            const error = await response.json().catch(() => ({}));
            throw new Error(error.error || 'Ошибка обновления профиля');
        }

        showToast('Профиль успешно обновлен', 'success');
        await loadProfile();
    } catch (error) {
        console.error('Ошибка обновления профиля:', error);
        showToast(error.message || 'Ошибка обновления профиля', 'error');
    }
});

// Смена пароля
document.getElementById('change-password-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();

    const oldPassword = document.getElementById('old-password').value;
    const newPassword = document.getElementById('new-password').value;
    const confirmPassword = document.getElementById('confirm-password').value;

    if (!oldPassword || !newPassword || !confirmPassword) {
        showToast('Заполните все поля', 'error');
        return;
    }

    if (newPassword.length < 6) {
        showToast('Пароль должен содержать минимум 6 символов', 'error');
        return;
    }

    if (newPassword !== confirmPassword) {
        showToast('Пароли не совпадают', 'error');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/user/profile/password`, {
            method: 'PUT',
            credentials: 'include', // Включаем cookies для отправки токена
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                old_password: oldPassword,
                new_password: newPassword
            })
        });

        if (!response.ok) {
            if (response.status === 401) {
                try {
                    await auth.refreshToken();
                    return document.getElementById('change-password-form').dispatchEvent(new Event('submit'));
                } catch (refreshError) {
                    console.warn('Не удалось обновить токен:', refreshError);
                }
            }
            const error = await response.json().catch(() => ({}));
            throw new Error(error.error || 'Ошибка смены пароля');
        }

        showToast('Пароль успешно изменен', 'success');
        document.getElementById('change-password-form').reset();
    } catch (error) {
        console.error('Ошибка смены пароля:', error);
        showToast(error.message || 'Ошибка смены пароля', 'error');
    }
});

// Переключение вкладок
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const tabName = btn.dataset.tab;

        // Убираем активный класс со всех кнопок и контента
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

        // Добавляем активный класс к выбранной кнопке и контенту
        btn.classList.add('active');
        document.getElementById(`tab-${tabName}`).classList.add('active');

        // Загружаем данные для вкладок
        if (tabName === 'problems') {
            loadUserProblems();
        } else if (tabName === 'solutions') {
            loadUserSolutions();
        }
    });
});

// Загрузка проблем пользователя
async function loadUserProblems() {
    const listContainer = document.getElementById('problems-list');
    const loadingEl = document.getElementById('problems-loading');
    const emptyEl = document.getElementById('problems-empty');

    listContainer.innerHTML = '';
    loadingEl.style.display = 'block';
    emptyEl.style.display = 'none';

    try {
        // Получаем user_id из токена или загружаем профиль
        let userId = null;
        if (currentUser && currentUser.id) {
            userId = currentUser.id;
        } else if (currentUser && currentUser.ID) {
            userId = currentUser.ID;
        } else {
            await loadProfile();
            userId = currentUser?.id || currentUser?.ID;
        }

        if (!userId) {
            throw new Error('Не удалось получить ID пользователя');
        }

        const response = await fetch(`${API_BASE}/problems/user/${userId}`, {
            method: 'GET',
            credentials: 'include', // Включаем cookies для отправки токена
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            if (response.status === 401) {
                const refreshed = await auth.refreshToken();
                if (refreshed) {
                    return loadUserProblems();
                }
            }
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || 'Ошибка загрузки проблем');
        }

        const data = await response.json();
        loadingEl.style.display = 'none';

        if (data.problems && Array.isArray(data.problems) && data.problems.length > 0) {
            data.problems.forEach(problem => {
                const card = createProblemCard(problem);
                listContainer.appendChild(card);
            });
        } else {
            emptyEl.style.display = 'block';
        }
    } catch (error) {
        console.error('Ошибка загрузки проблем:', error);
        loadingEl.style.display = 'none';
        emptyEl.style.display = 'block';
        showToast(error.message || 'Ошибка загрузки проблем', 'error');
    }
}

// Загрузка решений пользователя
async function loadUserSolutions() {
    const listContainer = document.getElementById('solutions-list');
    const loadingEl = document.getElementById('solutions-loading');
    const emptyEl = document.getElementById('solutions-empty');

    listContainer.innerHTML = '';
    loadingEl.style.display = 'block';
    emptyEl.style.display = 'none';

    try {
        // Получаем user_id из токена или загружаем профиль
        let userId = null;
        if (currentUser && currentUser.id) {
            userId = currentUser.id;
        } else if (currentUser && currentUser.ID) {
            userId = currentUser.ID;
        } else {
            await loadProfile();
            userId = currentUser?.id || currentUser?.ID;
        }

        if (!userId) {
            throw new Error('Не удалось получить ID пользователя');
        }

        const response = await fetch(`${API_BASE}/solutions/user/${userId}`, {
            method: 'GET',
            credentials: 'include', // Включаем cookies для отправки токена
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            if (response.status === 401) {
                const refreshed = await auth.refreshToken();
                if (refreshed) {
                    return loadUserSolutions();
                }
            }
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || 'Ошибка загрузки решений');
        }

        const data = await response.json();
        loadingEl.style.display = 'none';

        if (data.solutions && Array.isArray(data.solutions) && data.solutions.length > 0) {
            data.solutions.forEach(solution => {
                const card = createSolutionCard(solution);
                listContainer.appendChild(card);
            });
        } else {
            emptyEl.style.display = 'block';
        }
    } catch (error) {
        console.error('Ошибка загрузки решений:', error);
        loadingEl.style.display = 'none';
        emptyEl.style.display = 'block';
        showToast(error.message || 'Ошибка загрузки решений', 'error');
    }
}

// Создание карточки проблемы
function createProblemCard(problem) {
    const card = document.createElement('a');
    card.href = `/html/problem.html?id=${problem.ID || problem.id}`;
    card.className = 'item-card';

    const name = problem.Name || problem.name || 'Без названия';
    const describe = problem.Describe || problem.describe || '';
    const createdDate = problem.CreatedDate || problem.created_date || '';

    card.innerHTML = `
        <h3>${escapeHtml(name)}</h3>
        <p>${escapeHtml(describe.substring(0, 150))}${describe.length > 150 ? '...' : ''}</p>
        <div class="item-meta">
            <span>${formatDate(createdDate)}</span>
        </div>
    `;

    return card;
}

// Создание карточки решения
function createSolutionCard(solution) {
    const card = document.createElement('a');
    card.href = `/html/solution.html?id=${solution.ID || solution.id}`;
    card.className = 'item-card';

    const name = solution.Name || solution.name || 'Без названия';
    const describe = solution.Describe || solution.describe || '';
    const createdDate = solution.CreatedDate || solution.created_date || '';

    card.innerHTML = `
        <h3>${escapeHtml(name)}</h3>
        <p>${escapeHtml(describe.substring(0, 150))}${describe.length > 150 ? '...' : ''}</p>
        <div class="item-meta">
            <span>${formatDate(createdDate)}</span>
        </div>
    `;

    return card;
}

// Утилиты
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateString) {
    if (!dateString) return 'Дата не указана';
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString('ru-RU', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    } catch (e) {
        return dateString;
    }
}

function showToast(message, type = 'info') {
    const toast = document.getElementById('message-toast');
    toast.textContent = message;
    toast.className = `toast ${type} show`;

    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// Функция выхода
function logout() {
    fetch(`${API_BASE}/logout`, {
        method: 'POST',
        credentials: 'include', // Включаем cookies для отправки токена
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (!response.ok) throw new Error('Logout failed');
        return response.json();
    })
    .then(data => {
        console.log(data.message);
        // Очистка
        localStorage.removeItem('isLoggedIn');
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        sessionStorage.clear();
        
        // Остановка таймера обновления токена
        if (refreshTimer) {
            clearTimeout(refreshTimer);
            refreshTimer = null;
        }
        
        // Редирект на страницу авторизации
        window.location.href = '/html/authorization.html';
    })
    .catch(error => {
        console.error('Ошибка логаута:', error);
        // В случае ошибки тоже очищаем
        localStorage.removeItem('isLoggedIn');
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        sessionStorage.clear();
        window.location.href = '/html/authorization.html';
    });
}

// Экспорт функции logout для использования в других файлах
export { logout };
