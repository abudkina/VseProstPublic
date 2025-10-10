import * as auth from './authorizationFunctions.js';

// Общая функция для получения количества по endpoint'у
async function fetchCount(endpoint) {
    try {
        const response = await fetch(`http://127.0.0.1:8080/api/${endpoint}`, {
            method: 'GET',
            credentials: 'include'
        });
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
    const authenticated = await auth.checkAuth(true); // true — редирект при ошибке
    if (!authenticated) return; // checkAuth уже обработает редирект

    // Массив с данными для каждого типа (endpoint, elementId, label)
    const items = [
        { endpoint: 'countCategory', elementId: 'new-categories-count', label: 'Категории' },
        { endpoint: 'countTopic', elementId: 'new_topics-count', label: 'Темы' },
        { endpoint: 'countHashtag', elementId: 'new_hashtags-count', label: 'Хэштеги' },
        { endpoint: 'countProblem', elementId: 'new_problems-count', label: 'Проблемы' },
        { endpoint: 'countSolution', elementId: 'new_solutions-count', label: 'Решения' },
        { endpoint: 'countCommentSolution', elementId: 'new_solution_comments-count', label: 'Комментарии решений' },
        { endpoint: 'countTemporaryProblemSolution', elementId: 'link_problem_solutions', label: 'Проблемы - Решения' },
        { endpoint: 'countTemporaryLinkSolution', elementId: 'link_solution_problems', label: 'Решения - Проблемы' },
        { endpoint: 'countTemporaryLinkProblem', elementId: 'link_problem_problems', label: 'Проблемы - Проблемы' },
        { endpoint: 'countUser', elementId: 'users-count', label: 'Пользователи' }
    ];

    // Получаем все количества параллельно (Promise.all для скорости)
    const counts = await Promise.all(items.map(item => fetchCount(item.endpoint)));

    // Обновляем DOM в цикле
    items.forEach((item, index) => {
        const count = counts[index];
        const textElement = document.getElementById(item.elementId);
        if (textElement) {
            const block = textElement.closest('.block');
            if (block) {
                block.firstChild.textContent = `${item.label} (${count}) `;
                // Обновляем классы: green если count > 0, иначе red
                block.classList.toggle('green', count > 0);
                block.classList.toggle('red', count === 0);
            }
        }
    });
});
