import * as auth from './authorizationFunctions.js';

var hashtagsTomSelect; // Экземпляр Tom Select для хэштегов
var generalTopicTomSelect; // Экземпляр Tom Select для тем

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('problemForm');
    const categorySelect = document.getElementById('categorySelect');

    // Добавим скрытые поля для ID
    const topicIDHidden = document.createElement('input');
    topicIDHidden.type = 'hidden';
    topicIDHidden.name = 'topicID';
    form.appendChild(topicIDHidden);

    const hashtagsIDsHidden = document.createElement('input');
    hashtagsIDsHidden.type = 'hidden';
    hashtagsIDsHidden.name = 'hashtagsIDs';
    form.appendChild(hashtagsIDsHidden);

    // Функция загрузки категорий
    async function loadCategories() {
        try {
            const response = await fetch('http://127.0.0.1:8080/api/categories');
            const categories = await response.json();

            categorySelect.innerHTML = '<option value="">Выберите категорию</option>';

            categories.forEach(cat => {
                const option = document.createElement('option');
                option.value = cat.ID;
                option.textContent = cat.Name;
                categorySelect.appendChild(option);
            });
        } catch (error) {
            console.error('Ошибка загрузки категорий:', error);
        }
    }

    // загружаем категории при загрузке страницы
    loadCategories();

    // Инициализация Tom Select для тем (с поиском)
    generalTopicTomSelect = new TomSelect('#generalTopicSelect', {
        multiple: false,
        placeholder: 'Выберите общую тему (введите для поиска)',
        searchField: ['text'], // Поле для поиска
        valueField: 'value', // Значение опции (ID)
        labelField: 'text', // Текст опции (имя)
        maxOptions: null, // Без ограничения опций
        load: function (query, callback) {
            if (query.length < 3) return callback(); // Минимум 3 символа для поиска
            fetch(`http://127.0.0.1:8080/api/topics?search=${encodeURIComponent(query)}`)
                .then(res => res.json())
                .then(data => {
                    const options = data.map(item => ({
                        value: item.ID.toString(), // ID как строка
                        text: item.Name
                    }));
                    callback(options);
                })
                .catch(err => {
                    console.error('Ошибка загрузки тем:', err);
                    callback();
                });
        },
        onChange: function (value) {
            // Обновляем скрытое поле при выборе
            topicIDHidden.value = value;
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

    // Инициализация Tom Select для хэштегов
    hashtagsTomSelect = new TomSelect('#hashtags', {
        plugins: ['remove_button'], // Кнопки удаления выбранных элементов
        multiple: true, // Множественный выбор
        placeholder: 'Выберите хэштеги',
        searchField: ['text'], // Поле для поиска
        valueField: 'value', // Значение опции (ID)
        labelField: 'text', // Текст опции (имя)
        load: function (query, callback) {
            if (query.length < 3) return callback(); // Минимум 3 символа
            fetch(`http://127.0.0.1:8080/api/hashtags?q=${encodeURIComponent(query)}`)
                .then(res => res.json())
                .then(data => {
                    const options = data.map(item => ({
                        value: item.ID.toString(), // ID как строка для Tom Select
                        text: item.Name
                    }));
                    callback(options);
                })
                .catch(err => {
                    console.error('Ошибка загрузки хэштегов:', err);
                    callback();
                });
        },
        onChange: function (values) {
            // Обновляем скрытое поле: строка ID через запятую
            hashtagsIDsHidden.value = values.join(',');
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

    // Функции для модальных окон
    const modalOverlay = document.getElementById('modal-overlay');
    const topicModal = document.getElementById('topic-modal');
    const categoryModal = document.getElementById('category-modal');
    const hashtagModal = document.getElementById('hashtag-modal');

    function showModal(modal) {
        modalOverlay.style.display = 'flex';
        modal.style.display = 'block';
        modal.querySelector('input').focus();
    }

    function hideModal() {
        modalOverlay.style.display = 'none';
        topicModal.style.display = 'none';
        categoryModal.style.display = 'none';
        hashtagModal.style.display = 'none';
        // Очистить ошибки и поля
        document.querySelectorAll('.error-message').forEach(el => el.textContent = '');
        document.querySelectorAll('.modal input').forEach(inp => inp.value = '');
    }

    modalOverlay.
    addEventListener('click', (e) => {
        if (e.target === modalOverlay) hideModal();
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') hideModal();
    });

    // Обработчики для кнопок добавления
    document.getElementById('addTopicBtn').addEventListener('click', () => showModal(topicModal));
    document.getElementById('addCategoryBtn').addEventListener('click', () => showModal(categoryModal));
    document.getElementById('addHashtagBtn').addEventListener('click', () => showModal(hashtagModal));

    // Обработчики для кнопок в модалах
    document.getElementById('topic-cancel-btn').addEventListener('click', hideModal);
    document.getElementById('category-cancel-btn').addEventListener('click', hideModal);
    document.getElementById('hashtag-cancel-btn').addEventListener('click', hideModal);

    document.getElementById('topic-add-btn').addEventListener('click', async () => {
        const name = document.getElementById('topic-name-input').value.trim();
        if (!name) {
            document.getElementById('topic-error').textContent = 'Пожалуйста, введите имя темы.';
            return;
        }
        try {
            const response = await fetch('http://127.0.0.1:8080/api/addTopic', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name }),
                credentials: 'include'
            });
            if (response.ok) {
                const newTopic = await response.json();
                generalTopicTomSelect.addOption({ value: newTopic.ID.toString(), text: newTopic.Name });
                hideModal();
            } else {
                const error = await response.json();
                document.getElementById('topic-error').textContent = 'Ошибка: ' + error.error;
            }
        } catch (error) {
            document.getElementById('topic-error').textContent = 'Сетевая ошибка: ' + error.message;
        }
    });

    document.getElementById('category-add-btn').addEventListener('click', async () => {
        const name = document.getElementById('category-name-input').value.trim();
        if (!name) {
            document.getElementById('category-error').textContent = 'Пожалуйста, введите имя категории.';
            return;
        }
        try {
            const response = await fetch('http://127.0.0.1:8080/api/addCategory', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name }),
                credentials: 'include'
            });
            if (response.ok) {
                const newCategory = await response.json();
                const option = document.createElement('option');
                option.value = newCategory.ID;
                option.textContent = newCategory.Name;
                categorySelect.appendChild(option);
                hideModal();
            } else {
                const error = await response.json();
                document.getElementById('category-error').textContent = 'Ошибка: ' + error.error;
            }
        } catch (error) {
            document.getElementById('category-error').textContent = 'Сетевая ошибка: ' + error.message;
        }
    });

    document.getElementById('hashtag-add-btn').addEventListener('click', async () => {
        const name = document.getElementById('hashtag-name-input').value.trim();
        if (!name) {
            document.getElementById('hashtag-error').textContent = 'Пожалуйста, введите имя хэштега.';
            return;
        }
        try {
            const response = await fetch('http://127.0.0.1:8080/api/addHashtag', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name }),
                credentials: 'include'
            });
            if (response.ok) {
                const newHashtag = await response.json();
                hashtagsTomSelect.addOption({ value: newHashtag.ID.toString(), text: newHashtag.Name });
                hideModal();
            } else {
                const error = await response.json();
                document.getElementById('hashtag-error').textContent = 'Ошибка: ' + error.error;
            }
        } catch (error) {
            document.getElementById('hashtag-error').textContent = 'Сетевая ошибка: ' + error.message;
        }
    });
});

document.addEventListener('DOMContentLoaded', async function () {
    const form = document.getElementById('problemForm');
    const saveBtn = document.querySelector('.save-btn');
    const clearBtn = document.querySelector('.clear-btn');

    // Проверяем аутентификацию перед загрузкой
    const authenticated = await auth.checkAuth(true); // true — редирект при ошибке
    if (!authenticated) return; // checkAuth уже обработает редирект

    // Обработчик для кнопки "Сохранить"
    saveBtn.addEventListener('click', async function (event) {
        event.preventDefault();  // Предотвращаем стандартную отправку формы

        // Собираем данные из формы
        const formData = new FormData(form);
        formData.set('name', document.getElementById('problemTitle').value);
        formData.set('describe', document.getElementById('problemDescription').value);
        formData.set('category', document.getElementById('categorySelect').value);

        try {
            const response = await fetch('http://127.0.0.1:8080/api/createProblem', {
                method: 'POST',
                body: formData,  // Отправляем как FormData для файла
                credentials: 'include'  // Отправляем куки автоматически — сервер извлечёт userID
            });

            if (response.ok) {
                const result = await response.json();
                alert('Проблема сохранена! ID: ' + result.id);
                form.reset();  // Очищаем форму после сохранения
            } else {
                const error = await response.json();
                alert('Ошибка: ' + error.error);
            }
        } catch (error) {
            alert('Сетевая ошибка: ' + error.message);
        }
    });

    // Обработчик для кнопки "Очистить"
    clearBtn.addEventListener('click', function () {
        form.reset();
        document.querySelector('input[name="topicID"]').value = '';
        // Сброс Tom Select
        generalTopicTomSelect.clear();
        hashtagsTomSelect.clear();
    });
});