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
        load: function(query, callback) {
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
        onChange: function(value) {
            // Обновляем скрытое поле при выборе
            topicIDHidden.value = value;
        },
        render: {
            option: function(item, escape) {
                return `<div>${escape(item.text)}</div>`;
            },
            item: function(item, escape) {
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

    // Обработчик для кнопки "Добавить хэштег"
    document.getElementById('addHashtagBtn').addEventListener('click', async () => {
        const newHashtagName = prompt('Введите имя нового хэштега:');
        if (!newHashtagName || newHashtagName.trim().length < 1) return;

        try {
            const response = await fetch('http://127.0.0.1:8080/api/addHashtag', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: newHashtagName.trim() })
            });
            if (response.ok) {
                const newHashtag = await response.json();
                // Добавляем новую опцию в Tom Select и обновляем
                hashtagsTomSelect.addOption({ value: newHashtag.ID.toString(), text: newHashtag.Name });
                alert('Хэштег добавлен!');
            } else {
                const error = await response.json();
                alert('Ошибка: ' + error.error);
            }
        } catch (error) {
            alert('Сетевая ошибка: ' + error.message);
        }
    });

    document.getElementById('addTopicBtn').addEventListener('click', () => {
        alert('Добавить тему - функционал пока не реализован.');
    });

    document.getElementById('addCategoryBtn').addEventListener('click', () => {
        alert('Добавить категорию - функционал пока не реализован.');
    });

    document.getElementById('addHashtagBtn').addEventListener('click', () => {
        alert('Добавить хэштег - функционал пока не реализован.');
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
