
// Импорт всего из другого файла
import * as auth from './authorizationFunctions.js';

// Проверяем аутентификацию перед загрузкой
(async () => {
    const authenticated = await auth.checkAuth(true); // true — редирект при ошибке
    if (!authenticated) return; // checkAuth уже обработает редирект
})();

// Элементы формы и кнопки
const form = document.getElementById('solutionForm');
const clearBtn = document.getElementById('clearBtn');

// Элементы для multiselect проблем
const problemSearch = document.getElementById('problemSearch');
const problemDropdown = document.getElementById('problemDropdown');
const selectedProblems = document.getElementById('selectedProblems');

// Массив для хранения выбранных проблем: [{id: number, title: string}, ...]
let selectedProblemsList = [];

// Функция для обновления отображения выбранных проблем
function updateSelectedProblems() {
    selectedProblems.innerHTML = '';
    selectedProblemsList.forEach(problem => {
        const div = document.createElement('div');
        div.className = 'selected-problem';
        div.innerHTML = `${problem.title} <span class="remove" data-id="${problem.id}">×</span>`;
        selectedProblems.appendChild(div);
    });
}

// Обработчик ввода в поле поиска
problemSearch.addEventListener('input', async (e) => {
    const query = e.target.value.trim();
    if (query.length > 2) {
        try {
            // Используем параметр 'search' вместо 'q', и добавляем limit для оптимизации (например, 10 результатов)
            const response = await fetch(`http://127.0.0.1:8080/api/problems?search=${encodeURIComponent(query)}&limit=10`);
            if (response.ok) {
                const problems = await response.json();
                problemDropdown.innerHTML = '';
                problems.forEach(problem => {
                    // Берем только id и name (как title)
                    const div = document.createElement('div');
                    div.className = 'dropdown-item';
                    div.textContent = problem.Name;  // Название проблемы
                    div.addEventListener('click', () => {
                        // Добавить, если не выбрана
                        if (!selectedProblemsList.some(p => p.ID === problem.ID)) {
                            selectedProblemsList.push({ id: problem.ID, title: problem.Name });
                            updateSelectedProblems();
                        }
                        problemSearch.value = '';
                        problemDropdown.style.display = 'none';
                    });
                    problemDropdown.appendChild(div);
                });
                problemDropdown.style.display = 'block';
            }
        } catch (error) {
            console.error('Ошибка поиска:', error);
        }
    } else {
        problemDropdown.style.display = 'none';
    }
});

// Обработчик удаления выбранной проблемы
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
});

// Обработчик отправки формы
form.addEventListener('submit', async (e) => {
    e.preventDefault();

    // Собрать данные в FormData
    const formData = new FormData();
    formData.append('solution', document.getElementById('solution').value);
    formData.append('details', document.getElementById('details').value);
    
    // Передача массива ID выбранных проблем (JSON-строка)
    const selectedIds = selectedProblemsList.map(p => p.id);
    formData.append('relatedProblems', JSON.stringify(selectedIds));
    
    formData.append('canBuy', document.getElementById('canBuy').checked ? 'on' : 'off');
    formData.append('canEvaluate', document.getElementById('canEvaluate').checked ? 'on' : 'off');

    // Добавить файлы
    const mainImage = document.getElementById('mainImage').files[0];
    const additionalImage = document.getElementById('additionalImage').files[0];
    if (mainImage) formData.append('mainImage', mainImage);
    if (additionalImage) formData.append('additionalImage', additionalImage);

    try {
        // Отправить на сервер
        const response = await fetch('http://127.0.0.1:8080/api/createSolution', {
            method: 'POST',
            body: formData,
            credentials: 'include'  // Отправляем куки автоматически — сервер извлечёт userID
        });

        if (response.ok) {
            const result = await response.json();
            alert('Решение добавлено успешно! ID: ' + result.id);
            form.reset(); // Очистить форму после успеха
            selectedProblemsList = [];
            updateSelectedProblems();
        } else {
            const error = await response.json();
            alert('Ошибка: ' + error.error);
        }
    } catch (error) {
        alert('Ошибка сети: ' + error.message);
    }
});
