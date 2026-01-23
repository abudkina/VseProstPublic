// admin_problems.js
import * as auth from './authorizationFunctions.js';
import {
    loadCategories,
    initHashtagsTomSelect,
    loadProblemsCards,
    renderProblemCards,
    initFilterHandlers,
    initTagClickHandler
} from './problemListCommon.js';

let choicesInstance; // Для основного фильтра
let editChoicesInstance; // Для хэштегов в модале
let editTopicTomSelect; // Для темы в модале
const TOPIC_MIN_QUERY_LEN = 2;

let currentFilters = {
  search: '',
  hashtags: [],
  category: null,
  isNew: false, // Новый фильтр
  limit: 50,
  offset: 0
};

// Функция для перезагрузки карточек
function reloadCards() {
    loadProblemsCards(currentFilters, (data) => {
        renderProblemCards(data, { isAdmin: true });
    });
}

// При загрузке — опционально проверить авторизацию
window.addEventListener('load', async function() {
    if (localStorage.getItem('isLoggedIn')) {
        auth.checkAuth(false).catch(() => {
            localStorage.removeItem('isLoggedIn');
        });
    }
    
    // Используем общие функции
    await loadCategories('category', false);
    choicesInstance = initHashtagsTomSelect('hashtags', (instance) => {
        currentFilters.hashtags = instance.getValue().map(Number);
        currentFilters.offset = 0;
        reloadCards();
    });
    
    // Инициализация обработчиков фильтров
    if (choicesInstance) {
        initFilterHandlers(currentFilters, choicesInstance, reloadCards);
        initTagClickHandler(choicesInstance, currentFilters, reloadCards);
    }
    
    reloadCards();
    initModal();
    
    // Инициализация компонентов модала
    await Promise.all([
        loadCategoriesForModal(),
        loadTopicsForModal()
    ]);
    initEditTomSelect();
});

// Обработчик "Избранное" (без изменений)
document.getElementById('favoritesLink').addEventListener('click', function(e) {
    e.preventDefault();
    if (!localStorage.getItem('isLoggedIn')) {
        sessionStorage.setItem('redirectAfterLogin', '/html/favourites.html');
        window.location.href = '/html/authorization.html';
        return;
    }
    auth.checkAuth(true).then(userID => {
        window.location.href = '/html/favourites.html';
    }).catch(() => {});
});

// Обработчик профиля (без изменений)
document.getElementById('profileBtn').addEventListener('click', () => {
    auth.checkAuth(false).then(userID => {
        window.location.href = '/html/profile.html';
    }).catch(() => {
        sessionStorage.setItem('redirectAfterLogin', window.location.href);
        window.location.href = '/html/authorization.html';
    });
});

// Клик на карточку: открыть модал редактирования
document.addEventListener('click', (event) => {
    // Клик на иконку избранного - не открываем модал
    if (event.target.closest('.favorite-icon')) {
        return;
    }
    
    // Клик на карточку - открываем модал редактирования
    const card = event.target.closest('.card');
    if (card) {
        const problemId = card.getAttribute('data-problem-id');
        if (problemId) {
            event.preventDefault();
            event.stopPropagation();
            loadProblemById(problemId).then(problem => {
                fillEditForm(problem);
                const modal = document.getElementById('editModal');
                const content = modal.querySelector('.modal-content');
                
                // Создаем или получаем style элемент для принудительных стилей
                let forceStyle = document.getElementById('force-editModal-style');
                if (!forceStyle) {
                    forceStyle = document.createElement('style');
                    forceStyle.id = 'force-editModal-style';
                    document.head.appendChild(forceStyle);
                }
                
                // Функция для полноэкранного модального окна
                const centerModal = () => {
                    // Устанавливаем стили через CSS в style элементе для полноэкранного режима
                    forceStyle.textContent = `
                        #editModal {
                            display: block !important;
                            position: fixed !important;
                            left: 0 !important;
                            right: 0 !important;
                            top: 0 !important;
                            bottom: 0 !important;
                            width: 100% !important;
                            height: 100% !important;
                            margin: 0 !important;
                            padding: 0 !important;
                            background: linear-gradient(135deg, rgba(0, 0, 0, 0.6) 0%, rgba(0, 0, 0, 0.8) 100%) !important;
                            backdrop-filter: blur(4px) !important;
                            -webkit-backdrop-filter: blur(4px) !important;
                            z-index: 10000 !important;
                            overflow: auto !important;
                            box-sizing: border-box !important;
                        }
                        #editModal .modal-content {
                            position: relative !important;
                            left: auto !important;
                            right: auto !important;
                            top: auto !important;
                            transform: none !important;
                            width: 100% !important;
                            max-width: 100% !important;
                            height: 100% !important;
                            max-height: 100% !important;
                            margin: 0 !important;
                            padding: 20px !important;
                            background: linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%) !important;
                            border-radius: 0 !important;
                            box-shadow: none !important;
                            overflow-y: auto !important;
                            display: flex !important;
                            flex-direction: column !important;
                        }
                    `;
                };
                
                centerModal();
                modal.classList.add('active');
                
                // Применяем центрирование с задержками
                setTimeout(centerModal, 10);
                setTimeout(centerModal, 50);
                setTimeout(centerModal, 100);
                setTimeout(centerModal, 200);
                
                // Обновляем при изменении размера окна
                window.addEventListener('resize', centerModal);
                window.addEventListener('scroll', centerModal);
            }).catch(err => {
                alert('Ошибка загрузки проблемы: ' + err.message);
            });
        }
    }
});

// Инициализация модала
function initModal() {
    const modal = document.getElementById('editModal');
    const closeBtn = modal.querySelector('.close');
    const clearBtn = document.getElementById('clearBtn');
    const deleteBtn = document.getElementById('deleteBtn');

    // Явно скрываем модальное окно при инициализации
    if (modal) {
        modal.style.display = 'none';
        modal.classList.remove('active');
    }

    closeBtn.addEventListener('click', () => { 
        modal.style.display = 'none';
        modal.classList.remove('active');
    });
    window.addEventListener('click', (e) => { 
        if (e.target === modal) {
            modal.style.display = 'none';
            modal.classList.remove('active');
        }
    });

    clearBtn.addEventListener('click', () => {
        document.getElementById('editForm').reset();
        if (editChoicesInstance) editChoicesInstance.clear();
        if (editTopicTomSelect) editTopicTomSelect.clear();
        document.getElementById('relatedInfo').innerHTML = '';
        document.getElementById('currentImagePreview').innerHTML = '';
    });

    deleteBtn.addEventListener('click', () => {
        const problemId = document.getElementById('problemId').value;
        if (confirm('Удалить проблему?')) {
            deleteProblem(problemId).then(() => {
                modal.style.display = 'none';
                reloadCards(); // Перезагрузить список
            }).catch(err => alert('Ошибка удаления: ' + err.message));
        }
    });

    // Submit формы: сохранить/обновить
    document.getElementById('editForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const problemId = document.getElementById('problemId').value;
        if (!problemId) {
            alert('ID проблемы не найден');
            return;
        }
        
        const formData = new FormData();
        formData.append('name', document.getElementById('editName').value.trim());
        formData.append('describe', document.getElementById('editDescribe').value.trim());
        formData.append('category', document.getElementById('editCategory').value);
        
        // Тема
        const topicValue = editTopicTomSelect ? editTopicTomSelect.getValue() : '';
        if (topicValue) {
            formData.append('topic', topicValue);
        }
        
        // Хэштеги
        if (editChoicesInstance) {
            const hashtagValues = editChoicesInstance.getValue();
            if (hashtagValues && hashtagValues.length > 0) {
                formData.append('hashtagsIDs', hashtagValues.join(','));
            } else {
                formData.append('hashtagsIDs', '');
            }
        }
        
        // Изображение
        const imageFile = document.getElementById('editImage').files[0];
        if (imageFile) {
            formData.append('image', imageFile);
        }
        
        // Флаги
        formData.append('isNew', document.getElementById('editIsNew').checked ? 'true' : 'false');
        formData.append('fromAuthor', document.getElementById('editFromAuthor').checked ? 'true' : 'false');
        
        try {
            await updateProblem(problemId, formData);
            alert('Проблема успешно обновлена');
            document.getElementById('editModal').style.display = 'none';
            reloadCards(); // Перезагрузить список
        } catch (err) {
            alert('Ошибка сохранения: ' + err.message);
        }
    });
}

async function loadProblemById(problemId) {
    try {
        const token = localStorage.getItem('accessToken');
        const response = await fetch(`/api/problems/${problemId}`, {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const problem = await response.json();
        
        if (!problem) {
            throw new Error('Проблема не найдена');
        }
        
        console.log('Loaded problem:', problem); // Для отладки
        return problem; // Возвращаем объект, а не вызываем fillEditForm
    } catch (err) {
        console.error('Error loading problem:', err);
        throw err; // Пробрасываем ошибку, чтобы .catch в обработчике сработал
    }
}

// Заполнение формы данными проблемы
function fillEditForm(problem) {
    document.getElementById('problemId').value = problem.ID;
    document.getElementById('editName').value = problem.Name || '';
    document.getElementById('editDescribe').value = problem.Describe || '';
    document.getElementById('editCategory').value = problem.Category || '';
    
    // Устанавливаем тему
    if (editTopicTomSelect) {
        if (problem.Topic) {
            editTopicTomSelect.setValue(problem.Topic.toString());
        } else {
            editTopicTomSelect.clear();
        }
    }
    
    // Устанавливаем хэштеги
    if (problem.Hashtags && problem.Hashtags.length > 0 && editChoicesInstance) {
        const hashtagIds = problem.Hashtags.map(h => h.ID.toString());
        editChoicesInstance.setValue(hashtagIds);
    } else if (editChoicesInstance) {
        editChoicesInstance.clear();
    }
    
    document.getElementById('editIsNew').checked = problem.IsNew || false;
    document.getElementById('editFromAuthor').checked = problem.FromAuthor || false;

    // Показать связанные данные (не редактируемые)
    let relatedHtml = '';
    if (problem.Solutions && problem.Solutions.length > 0) {
        relatedHtml += `<p><strong>Решения:</strong> ${problem.Solutions.length}</p>`;
    }
    if (problem.LinkedProblems && problem.LinkedProblems.length > 0) {
        relatedHtml += `<p><strong>Связанные проблемы:</strong> ${problem.LinkedProblems.length}</p>`;
    }
    if (problem.FavouriteUsers && problem.FavouriteUsers.length > 0) {
        relatedHtml += `<p><strong>В избранном у:</strong> ${problem.FavouriteUsers.length} пользователей</p>`;
    }
    document.getElementById('relatedInfo').innerHTML = relatedHtml;

    // Показать текущее изображение
    const previewDiv = document.getElementById('currentImagePreview');
    previewDiv.innerHTML = '';
    if (problem.Image) {
        const imgPreview = document.createElement('img');
        imgPreview.src = problem.Image.startsWith('http') ? problem.Image : `${problem.Image}`;
        imgPreview.style.maxWidth = '200px';
        imgPreview.style.maxHeight = '200px';
        imgPreview.style.borderRadius = '4px';
        imgPreview.style.marginTop = '10px';
        const label = document.createElement('p');
        label.textContent = 'Текущее изображение:';
        label.style.margin = '0 0 5px 0';
        previewDiv.appendChild(label);
        previewDiv.appendChild(imgPreview);
    }
}

// Обновление проблемы (multipart для файла)
async function updateProblem(id, formData) {
    const token = localStorage.getItem('accessToken');
    const response = await fetch(`/api/problems/${id}`, {
        method: 'PUT',
        headers: {
            'Authorization': `Bearer ${token}`
        },
        body: formData
    });
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'Неизвестная ошибка' }));
        throw new Error(errorData.error || 'Ошибка HTTP: ' + response.status);
    }
    return await response.json();
}

// Удаление проблемы
async function deleteProblem(id) {
    const token = localStorage.getItem('accessToken');
    const response = await fetch(`/api/problems/${id}`, {
        method: 'DELETE',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        }
    });
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'Неизвестная ошибка' }));
        throw new Error(errorData.error || 'Ошибка HTTP: ' + response.status);
    }
    return await response.json();
}

// Загрузка категорий для модала (дублирует основную, но отдельно)
async function loadCategoriesForModal() {
    try {
        const token = localStorage.getItem('accessToken');
        const response = await fetch('/api/categories', {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        const categories = await response.json();
        const categorySelect = document.getElementById('editCategory');
        categorySelect.innerHTML = '<option value="">Выберите категорию</option>';
        categories.forEach(cat => {
            const option = document.createElement('option');
            option.value = cat.ID;
            option.textContent = cat.Name;
            categorySelect.appendChild(option);
        });
    } catch (error) {
        console.error('Ошибка загрузки категорий для модала:', error);
    }
}

// Загрузка тем для модала (предполагаем эндпоинт /api/topics; адаптируйте если нужно)
async function loadTopicsForModal() {
    try {
        const token = localStorage.getItem('accessToken');
        const response = await fetch('/api/topics', {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        const topics = await response.json();
        
        // Инициализируем TomSelect для темы
        if (editTopicTomSelect) {
            editTopicTomSelect.destroy();
        }
        
        editTopicTomSelect = new TomSelect('#editTopic', {
            // Меняем дефолтный wrapperClass="ts-wrapper" на свой
            wrapperClass: 'vs-wrapper',
            multiple: false,
            placeholder: 'Выберите общую тему (введите для поиска)',
            searchField: ['text'],
            valueField: 'value',
            labelField: 'text',
            maxOptions: null,
            loadThrottle: 300, // Задержка перед загрузкой (мс)
            shouldLoad: function(query) {
                // Загружаем только если введено 2+ символа
                return query && query.length >= TOPIC_MIN_QUERY_LEN;
            },
            load: function (query, callback) {
                // Выпадающий список (и загрузку) показываем только после 2+ символов
                if (!query || query.length < TOPIC_MIN_QUERY_LEN) {
                    callback();
                    return;
                }
                
                const token = localStorage.getItem('accessToken');
                console.log('Поиск темы:', query); // Отладка
                fetch(`/api/topics?search=${encodeURIComponent(query)}`, {
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    }
                })
                    .then(res => {
                        if (!res.ok) throw new Error('Ошибка загрузки тем');
                        return res.json();
                    })
                    .then(data => {
                        console.log('Найдено тем:', data.length); // Отладка
                        const options = data.map(item => ({
                            value: item.ID.toString(),
                            text: item.Name
                        }));
                        callback(options);
                    })
                    .catch(err => {
                        console.error('Ошибка загрузки тем:', err);
                        callback();
                    });
            },
            onFocus: function() {
                // Выпадающий список показываем только после ввода 2+ символов
                const q = (this.control_input?.value || '').trim();
                if (q.length >= TOPIC_MIN_QUERY_LEN) {
                    this.open();
                } else {
                    this.close();
                }
            },
            onType: function(str) {
                // Открываем список при вводе 2+ символов
                const query = (str || '').trim();
                if (query.length >= TOPIC_MIN_QUERY_LEN) {
                    this.open();
                } else {
                    this.close();
                }
            },
            render: {
                option: function (item, escape) {
                    return `<div>${escape(item.text)}</div>`;
                },
                item: function (item, escape) {
                    return `<div>${escape(item.text)}</div>`;
                },
                no_results: function() {
                    return `<div class="no-results">Введите минимум ${TOPIC_MIN_QUERY_LEN} символа(ов) для поиска темы.</div>`;
                }
            }
        });
        
        // Добавляем обработчик ввода для автоматического открытия списка
        setTimeout(() => {
            const editTopicSelect = document.getElementById('editTopic');
            if (editTopicSelect && editTopicTomSelect) {
                const tsWrapper = editTopicSelect.closest('.vs-wrapper');
                if (tsWrapper) {
                    const input = tsWrapper.querySelector('input[type="text"]');
                    if (input) {
                        input.addEventListener('input', function(e) {
                            const query = (e.target.value || '').trim();
                            if (query.length >= TOPIC_MIN_QUERY_LEN) {
                                // Принудительно вызываем загрузку и открываем список
                                if (editTopicTomSelect) {
                                    editTopicTomSelect.load(query);
                                    editTopicTomSelect.open();
                                }
                            } else {
                                if (editTopicTomSelect) {
                                    editTopicTomSelect.close();
                                }
                            }
                        });
                    }
                }
            }
        }, 100);
    } catch (error) {
        console.error('Ошибка загрузки тем:', error); // Если эндпоинта нет, игнорируем
    }
}

// Инициализация TomSelect для модала (аналогично основному)
function initEditTomSelect() {
    if (editChoicesInstance) editChoicesInstance.destroy();
    const token = localStorage.getItem('accessToken');
    editChoicesInstance = new TomSelect('#editHashtags', {
        // Меняем дефолтный wrapperClass="ts-wrapper" на свой
        wrapperClass: 'vs-wrapper',
        plugins: ['remove_button'],
        multiple: true,
        placeholder: 'Выберите хэштеги',
        searchField: ['text'],
        valueField: 'value',
        labelField: 'text',
        load: function (query, callback) {
            if (query.length < 2) return callback();
            
            // Используем endpoint для поиска хэштегов
            fetch(`/api/hashtags/search?q=${encodeURIComponent(query)}`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                credentials: 'include'
            })
                .then(res => {
                    if (!res.ok) throw new Error('Ошибка загрузки хэштегов');
                    return res.json();
                })
                .then(data => {
                    // Обрабатываем разные форматы ответа
                    let hashtags = [];
                    if (Array.isArray(data)) {
                        hashtags = data;
                    } else if (data.hashtags && Array.isArray(data.hashtags)) {
                        hashtags = data.hashtags;
                    } else if (data && typeof data === 'object') {
                        // Если data - это объект с полями, преобразуем в массив
                        hashtags = Object.values(data).filter(item => item && typeof item === 'object');
                    }
                    
                    const options = hashtags.map(item => ({
                        value: (item.ID || item.id || item.Id || 0).toString(),
                        text: (item.Name || item.name || item.text || '').replace(/^#/, '') // Убираем # если есть
                    })).filter(opt => opt.value && opt.text); // Фильтруем пустые значения
                    
                    callback(options);
                })
                .catch(err => {
                    console.error('Ошибка загрузки хэштегов:', err);
                    callback();
                });
        },
        onChange: function (values) {
            // Обновление при изменении
        },
        render: {
            option: function (item, escape) {
                return `<div>${escape(item.text)}</div>`;
            },
            item: function (item, escape) {
                return `<div>${escape(item.text)}</div>`;
            }
        }
    });
}

// Кнопка "Новые"
document.getElementById('newBtn').addEventListener('click', () => {
    currentFilters.isNew = !currentFilters.isNew;
    document.getElementById('newBtn').classList.toggle('active', currentFilters.isNew);
    currentFilters.offset = 0;
    reloadCards();
});

// Обработчик "Добавить проблему" - теперь открывает модальное окно
// Логика перенесена в modalProblem.js

// Инициализация TomSelect для модала уже происходит в window.addEventListener('load')
