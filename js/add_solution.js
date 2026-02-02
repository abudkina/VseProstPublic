// add_solution.js
import * as auth from './authorizationFunctions.js';

let selectedProblemsList = [];

// Проверяем аутентификацию
(async () => {
    try {
        await auth.checkAuth(true);
    } catch (error) {
        return;
    }
})();

// Функция для обновления отображения выбранных проблем
function updateSelectedProblems() {
    const selectedProblems = document.getElementById('selectedProblems');
    if (!selectedProblems) return;
    
    selectedProblems.innerHTML = '';
    selectedProblemsList.forEach(problem => {
        const div = document.createElement('div');
        div.className = 'selected-problem';
        div.innerHTML = `${problem.title} <span class="remove" data-id="${problem.id}">×</span>`;
        selectedProblems.appendChild(div);
    });
}

// Инициализация при загрузке DOM
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('solutionForm');
    const clearBtn = document.getElementById('clearBtn');
    const problemSearch = document.getElementById('problemSearch');
    const problemDropdown = document.getElementById('problemDropdown');
    const selectedProblems = document.getElementById('selectedProblems');

    if (!form || !clearBtn || !problemSearch || !problemDropdown || !selectedProblems) {
        console.error('Не найдены необходимые элементы DOM');
        return;
    }

    // Обновление выбранных проблем
    updateSelectedProblems();

    // Поиск проблем
    problemSearch.addEventListener('input', async (e) => {
        const query = e.target.value.trim();
        if (query.length > 2) {
            try {
                const token = localStorage.getItem('accessToken');
                const response = await fetch(API_CONFIG.buildURLWithParams(API_CONFIG.ENDPOINTS.PROBLEMS, {search: query, limit: 10}), {
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    }
                });
                
                if (response.ok) {
                    const problems = await response.json();
                    problemDropdown.innerHTML = '';
                    
                    problems.forEach(problem => {
                        // Проверяем, не выбрана ли уже эта проблема
                        if (selectedProblemsList.some(p => p.id === problem.ID)) {
                            return;
                        }
                        
                        const div = document.createElement('div');
                        div.className = 'dropdown-item';
                        div.textContent = problem.Name || 'Без названия';
                        div.setAttribute('data-id', problem.ID);
                        
                        div.addEventListener('click', () => {
                            selectedProblemsList.push({ 
                                id: problem.ID, 
                                title: problem.Name || 'Без названия' 
                            });
                            updateSelectedProblems();
                            problemSearch.value = '';
                            problemDropdown.style.display = 'none';
                        });
                        
                        problemDropdown.appendChild(div);
                    });
                    
                    if (problems.length > 0) {
                        problemDropdown.style.display = 'block';
                    } else {
                        problemDropdown.style.display = 'none';
                    }
                }
            } catch (error) {
                console.error('Ошибка поиска проблем:', error);
                problemDropdown.style.display = 'none';
            }
        } else {
            problemDropdown.style.display = 'none';
        }
    });

    // Удаление выбранной проблемы
    selectedProblems.addEventListener('click', (e) => {
        if (e.target.classList.contains('remove')) {
            const id = parseInt(e.target.dataset.id);
            selectedProblemsList = selectedProblemsList.filter(p => p.id !== id);
            updateSelectedProblems();
        }
    });

    // Скрыть dropdown при клике вне
    document.addEventListener('click', (e) => {
        if (!problemSearch.contains(e.target) && !problemDropdown.contains(e.target)) {
            problemDropdown.style.display = 'none';
        }
    });

    // Очистка формы
    clearBtn.addEventListener('click', () => {
        form.reset();
        selectedProblemsList = [];
        updateSelectedProblems();
        problemDropdown.style.display = 'none';
    });

    // Обработчик отправки формы
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        // Валидация
        const solutionName = document.getElementById('solution').value.trim();
        const solutionDetails = document.getElementById('details').value.trim();
        
        if (!solutionName) {
            alert('Пожалуйста, введите название решения');
            return;
        }
        
        if (!solutionDetails) {
            alert('Пожалуйста, введите описание решения');
            return;
        }
        
        if (selectedProblemsList.length === 0) {
            alert('Пожалуйста, выберите хотя бы одну связанную проблему');
            return;
        }

        // Собрать данные в FormData
        const formData = new FormData();
        formData.append('solution', solutionName);
        formData.append('details', solutionDetails);
        
        // Передача ID выбранных проблем через запятую
        const selectedIds = selectedProblemsList.map(p => p.id).join(',');
        formData.append('relatedProblems', selectedIds);
        
        formData.append('canBuy', document.getElementById('canBuy').checked ? 'on' : 'off');
        formData.append('canEvaluate', document.getElementById('canEvaluate').checked ? 'on' : 'off');

        // Добавить файлы
        const mainImage = document.getElementById('mainImage').files[0];
        const additionalImage = document.getElementById('additionalImage').files[0];
        if (mainImage) formData.append('image', mainImage); // Исправлено имя поля
        if (additionalImage) formData.append('additionalImage', additionalImage);

        try {
            const token = localStorage.getItem('accessToken');
            // Исправленный endpoint для создания решения
            const response = await fetch(API_CONFIG.buildURL(API_CONFIG.ENDPOINTS.SOLUTIONS), {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                    // Не устанавливаем Content-Type для FormData - браузер сделает это сам
                },
                body: formData
            });

            if (response.status === 401) {
                const refreshed = await auth.refreshToken();
                if (refreshed) {
                    // Повторяем отправку формы
                    form.dispatchEvent(new Event('submit', { cancelable: true }));
                    return;
                }
                throw new Error('Требуется авторизация');
            }
            
            if (response.ok) {
                const result = await response.json();
                alert('Решение успешно добавлено!');
                form.reset();
                selectedProblemsList = [];
                updateSelectedProblems();
            } else {
                const error = await response.json();
                alert('Ошибка: ' + (error.error || 'Неизвестная ошибка'));
            }
        } catch (error) {
            alert('Ошибка сети: ' + error.message);
        }
    });
});