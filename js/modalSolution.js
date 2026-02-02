// modalSolution.js
import * as auth from './authorizationFunctions.js';

let selectedProblemsList = [];

document.addEventListener('DOMContentLoaded', function() {
    const solutionModalOverlay = document.getElementById('solution-modal-overlay');
    const solutionModal = document.getElementById('solution-modal');
    const addSolutionBtn = document.getElementById('addSolution');
    const closeSolutionModalBtn = document.getElementById('closeSolutionModal');
    const form = document.getElementById('solutionForm');
    const clearBtn = document.getElementById('clearSolutionBtn');
    const problemSearch = document.getElementById('problemSearch');
    const problemDropdown = document.getElementById('problemDropdown');
    const selectedProblems = document.getElementById('selectedProblems');

    if (!solutionModalOverlay || !solutionModal || !addSolutionBtn || !form) {
        console.error('Не найдены необходимые элементы DOM для модального окна решения');
        return;
    }

    // Функция для обновления отображения выбранных проблем
    function updateSelectedProblems() {
        if (!selectedProblems) return;
        
        selectedProblems.innerHTML = '';
        selectedProblemsList.forEach(problem => {
            const div = document.createElement('div');
            div.className = 'selected-problem';
            div.innerHTML = `${problem.title} <span class="remove" data-id="${problem.id}">×</span>`;
            selectedProblems.appendChild(div);
        });
    }

    // Функции для открытия/закрытия модального окна
    function openSolutionModal() {
        solutionModalOverlay.classList.add('active');
        document.body.style.overflow = 'hidden';
        updateSelectedProblems();
    }

    function closeSolutionModal() {
        solutionModalOverlay.classList.remove('active');
        document.body.style.overflow = '';
        form.reset();
        selectedProblemsList = [];
        updateSelectedProblems();
        if (problemDropdown) problemDropdown.style.display = 'none';
    }

    // Обработчики событий
    addSolutionBtn.addEventListener('click', async () => {
        try {
            await auth.checkAuth(true);
            openSolutionModal();
        } catch (error) {
            console.error('Ошибка авторизации:', error);
        }
    });

    if (closeSolutionModalBtn) {
        closeSolutionModalBtn.addEventListener('click', closeSolutionModal);
    }

    solutionModalOverlay.addEventListener('click', (e) => {
        if (e.target === solutionModalOverlay) {
            closeSolutionModal();
        }
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && solutionModalOverlay.classList.contains('active')) {
            closeSolutionModal();
        }
    });

    // Инициализация
    updateSelectedProblems();

    // Поиск проблем
    if (problemSearch && problemDropdown) {
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
    }

    // Удаление выбранной проблемы
    if (selectedProblems) {
        selectedProblems.addEventListener('click', (e) => {
            if (e.target.classList.contains('remove')) {
                const id = parseInt(e.target.dataset.id);
                selectedProblemsList = selectedProblemsList.filter(p => p.id !== id);
                updateSelectedProblems();
            }
        });
    }

    // Скрыть dropdown при клике вне
    document.addEventListener('click', (e) => {
        if (problemSearch && problemDropdown && 
            !problemSearch.contains(e.target) && 
            !problemDropdown.contains(e.target)) {
            problemDropdown.style.display = 'none';
        }
    });

    // Очистка формы
    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            form.reset();
            selectedProblemsList = [];
            updateSelectedProblems();
            if (problemDropdown) problemDropdown.style.display = 'none';
        });
    }

    // Функции для модальных окон (тема, категория, хэштег)
    const modalOverlay = document.getElementById('modal-overlay');
    const topicModal = document.getElementById('topic-modal');
    const categoryModal = document.getElementById('category-modal');
    const hashtagModal = document.getElementById('hashtag-modal');

    function showModal(modal) {
        if (modalOverlay && modal) {
            modalOverlay.classList.add('active');
            modal.classList.add('active');
            const input = modal.querySelector('input');
            if (input) input.focus();
        }
    }

    function hideModal() {
        if (modalOverlay) modalOverlay.classList.remove('active');
        if (topicModal) topicModal.classList.remove('active');
        if (categoryModal) categoryModal.classList.remove('active');
        if (hashtagModal) hashtagModal.classList.remove('active');
        
        document.querySelectorAll('.error-message').forEach(el => el.textContent = '');
        document.querySelectorAll('.modal input').forEach(inp => inp.value = '');
    }

    if (modalOverlay) {
        modalOverlay.addEventListener('click', (e) => {
            if (e.target === modalOverlay) hideModal();
        });
    }

    // Обработчики для кнопок в модалах
    const topicCancelBtn = document.getElementById('topic-cancel-btn');
    const categoryCancelBtn = document.getElementById('category-cancel-btn');
    const hashtagCancelBtn = document.getElementById('hashtag-cancel-btn');

    if (topicCancelBtn) topicCancelBtn.addEventListener('click', hideModal);
    if (categoryCancelBtn) categoryCancelBtn.addEventListener('click', hideModal);
    if (hashtagCancelBtn) hashtagCancelBtn.addEventListener('click', hideModal);

    // Добавление темы
    const topicAddBtn = document.getElementById('topic-add-btn');
    if (topicAddBtn) {
        topicAddBtn.addEventListener('click', async () => {
            const topicNameInput = document.getElementById('topic-name-input');
            const topicError = document.getElementById('topic-error');
            
            if (!topicNameInput || !topicError) return;
            
            const name = topicNameInput.value.trim();
            if (!name) {
                topicError.textContent = 'Пожалуйста, введите имя темы.';
                return;
            }
            
            try {
                const token = localStorage.getItem('accessToken');
                const response = await fetch(API_CONFIG.buildURL(API_CONFIG.ENDPOINTS.TOPICS), {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify({ name: name })
                });
                
                if (response.ok) {
                    const newTopic = await response.json();
                    hideModal();
                    alert('Тема успешно добавлена!');
                } else {
                    const error = await response.json();
                    topicError.textContent = 'Ошибка: ' + (error.error || 'Неизвестная ошибка');
                }
            } catch (error) {
                topicError.textContent = 'Сетевая ошибка: ' + error.message;
            }
        });
    }

    // Добавление категории
    const categoryAddBtn = document.getElementById('category-add-btn');
    if (categoryAddBtn) {
        categoryAddBtn.addEventListener('click', async () => {
            const categoryNameInput = document.getElementById('category-name-input');
            const categoryError = document.getElementById('category-error');
            
            if (!categoryNameInput || !categoryError) return;
            
            const name = categoryNameInput.value.trim();
            if (!name) {
                categoryError.textContent = 'Пожалуйста, введите имя категории.';
                return;
            }
            
            try {
                const token = localStorage.getItem('accessToken');
                const response = await fetch(API_CONFIG.buildURL(API_CONFIG.ENDPOINTS.CATEGORIES), {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify({ name: name })
                });
                
                if (response.ok) {
                    const newCategory = await response.json();
                    hideModal();
                    alert('Категория успешно добавлена!');
                } else {
                    const error = await response.json();
                    categoryError.textContent = 'Ошибка: ' + (error.error || 'Неизвестная ошибка');
                }
            } catch (error) {
                categoryError.textContent = 'Сетевая ошибка: ' + error.message;
            }
        });
    }

    // Добавление хэштега
    const hashtagAddBtn = document.getElementById('hashtag-add-btn');
    if (hashtagAddBtn) {
        hashtagAddBtn.addEventListener('click', async () => {
            const hashtagNameInput = document.getElementById('hashtag-name-input');
            const hashtagError = document.getElementById('hashtag-error');
            
            if (!hashtagNameInput || !hashtagError) return;
            
            const name = hashtagNameInput.value.trim();
            if (!name) {
                hashtagError.textContent = 'Пожалуйста, введите имя хэштега.';
                return;
            }
            
            try {
                const token = localStorage.getItem('accessToken');
                const response = await fetch(API_CONFIG.buildURL(API_CONFIG.ENDPOINTS.HASHTAGS), {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify({ name: name })
                });
                
                if (response.ok) {
                    const newHashtag = await response.json();
                    hideModal();
                    alert('Хэштег успешно добавлен!');
                } else {
                    const error = await response.json();
                    hashtagError.textContent = 'Ошибка: ' + (error.error || 'Неизвестная ошибка');
                }
            } catch (error) {
                hashtagError.textContent = 'Сетевая ошибка: ' + error.message;
            }
        });
    }

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
        if (mainImage) formData.append('image', mainImage);
        if (additionalImage) formData.append('additionalImage', additionalImage);

        try {
            const token = localStorage.getItem('accessToken');
            const response = await fetch(API_CONFIG.buildURL(API_CONFIG.ENDPOINTS.SOLUTIONS), {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
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
                closeSolutionModal();
                
                // Перезагружаем страницу для обновления списка
                window.location.reload();
            } else {
                const error = await response.json();
                alert('Ошибка: ' + (error.error || 'Неизвестная ошибка'));
            }
        } catch (error) {
            alert('Ошибка сети: ' + error.message);
        }
    });
});

