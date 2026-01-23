// admin.js
import * as auth from './authorizationFunctions.js';

// Общая функция для получения количества по endpoint'у
async function fetchCount(endpoint) {
    try {
        // Используем cookies для авторизации (токен хранится там)
        const response = await fetch(`/api/${endpoint}`, {
            method: 'GET',
            credentials: 'include', // Важно для отправки cookies
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        // Перехватчик fetch должен автоматически обработать 401,
        // но на всякий случай оставляем проверку
        if (response.status === 401) {
            // Попробуем обновить токен
            try {
                const refreshed = await auth.refreshToken();
                if (refreshed) {
                    // Повторяем запрос после обновления токена
                    return await fetchCount(endpoint);
                }
            } catch (refreshError) {
                console.error('Ошибка обновления токена:', refreshError);
            }
            throw new Error('Требуется авторизация');
        }
        
        if (!response.ok) throw new Error('Network response was not ok');
        const data = await response.json();
        return data.count || 0;
    } catch (error) {
        console.error('Fetch error:', error);
        return 0;
    }
}

document.addEventListener('DOMContentLoaded', async function () {
    // Проверяем аутентификацию перед загрузкой
    try {
        await auth.checkAuth(true);
    } catch (error) {
        return;
    }

    // Исправленные endpoint'ы
    const items = [
        { endpoint: 'categories/count', elementId: 'new-categories-count', label: 'Категории' },
        { endpoint: 'topics/count-new', elementId: 'new_topics-count', label: 'Темы' },
        { endpoint: 'hashtags/count', elementId: 'new_hashtags-count', label: 'Хэштеги' },
        { endpoint: 'problems/count-new', elementId: 'new_problems-count', label: 'Проблемы' },
        { endpoint: 'solutions/count-new', elementId: 'new_solutions-count', label: 'Решения' },
        { endpoint: 'comment-solutions/count', elementId: 'new_solution_comments-count', label: 'Комментарии решений' },
        { endpoint: 'temporary-problem-solutions/count', elementId: 'link_problem_solutions', label: 'Проблемы - Решения' },
        { endpoint: 'temporary-link-solutions/count', elementId: 'link_solution_problems', label: 'Решения - Проблемы' },
        { endpoint: 'temporary-link-problems/count', elementId: 'link_problem_problems', label: 'Проблемы - Проблемы' },
        { endpoint: 'users/count-new', elementId: 'users-count', label: 'Пользователи' }
    ];

    // Получаем все количества параллельно
    const counts = await Promise.all(items.map(item => fetchCount(item.endpoint)));

    // Обновляем DOM в цикле
    items.forEach((item, index) => {
        const count = counts[index];
        const textElement = document.getElementById(item.elementId);
        if (textElement) {
            const block = textElement.closest('.block');
            if (block) {
                block.firstChild.textContent = `${item.label} (${count}) `;
                block.classList.toggle('green', count > 0);
                block.classList.toggle('red', count === 0);
            }
        }
    });
    
    // Добавляем обработчики кликов для переходов на соответствующие страницы
    setupNavigationHandlers();
});

// Настройка обработчиков навигации
function setupNavigationHandlers() {
    // Блок "Новые проблемы" -> страница админки проблем
    const newProblemsLink = document.getElementById('new_problems');
    if (newProblemsLink) {
        newProblemsLink.addEventListener('click', (e) => {
            e.preventDefault();
            window.location.href = '/html/admin_problems.html';
        });
        // Делаем весь блок кликабельным
        const block = newProblemsLink.nextElementSibling;
        if (block) {
            block.style.cursor = 'pointer';
            block.addEventListener('click', () => {
                window.location.href = '/html/admin_problems.html';
            });
        }
    }
    
    // Остальные блоки
    const newSolutionsLink = document.getElementById('new_solutions');
    if (newSolutionsLink) {
        newSolutionsLink.addEventListener('click', (e) => {
            e.preventDefault();
            window.location.href = '/html/admin_solutions.html';
        });
        const block = newSolutionsLink.nextElementSibling;
        if (block) {
            block.style.cursor = 'pointer';
            block.addEventListener('click', () => {
                window.location.href = '/html/admin_solutions.html';
            });
        }
    }
    
    const newHashtagsLink = document.getElementById('new_hashtags');
    if (newHashtagsLink) {
        newHashtagsLink.addEventListener('click', (e) => {
            e.preventDefault();
            window.location.href = '/html/admin_hashtags.html';
        });
        const block = newHashtagsLink.nextElementSibling;
        if (block) {
            block.style.cursor = 'pointer';
            block.addEventListener('click', () => {
                window.location.href = '/html/admin_hashtags.html';
            });
        }
    }
    
    const newSolutionCommentsLink = document.getElementById('new_solution_comments');
    if (newSolutionCommentsLink) {
        newSolutionCommentsLink.addEventListener('click', (e) => {
            e.preventDefault();
            window.location.href = '/html/admin_comments.html';
        });
        const block = newSolutionCommentsLink.nextElementSibling;
        if (block) {
            block.style.cursor = 'pointer';
            block.addEventListener('click', () => {
                window.location.href = '/html/admin_comments.html';
            });
        }
    }
    
    const newCategoriesLink = document.getElementById('new_categories');
    if (newCategoriesLink) {
        newCategoriesLink.addEventListener('click', (e) => {
            e.preventDefault();
            window.location.href = '/html/admin_categories.html';
        });
        const block = newCategoriesLink.nextElementSibling;
        if (block) {
            block.style.cursor = 'pointer';
            block.addEventListener('click', () => {
                window.location.href = '/html/admin_categories.html';
            });
        }
    }
    
    const newTopicsLink = document.getElementById('new_topics');
    if (newTopicsLink) {
        newTopicsLink.addEventListener('click', (e) => {
            e.preventDefault();
            window.location.href = '/html/admin_topics.html';
        });
        const block = newTopicsLink.nextElementSibling;
        if (block) {
            block.style.cursor = 'pointer';
            block.addEventListener('click', () => {
                window.location.href = '/html/admin_topics.html';
            });
        }
    }
    
    const usersLink = document.getElementById('users');
    if (usersLink) {
        usersLink.addEventListener('click', (e) => {
            e.preventDefault();
            window.location.href = '/html/admin_users.html';
        });
        const block = usersLink.nextElementSibling;
        if (block) {
            block.style.cursor = 'pointer';
            block.addEventListener('click', () => {
                window.location.href = '/html/admin_users.html';
            });
        }
    }
}