// modalProblem.js
import * as auth from './authorizationFunctions.js';

let hashtagsTomSelect;
let generalTopicTomSelect;
const TOPIC_MIN_QUERY_LEN = 2;

// Функции нормализации (аналогичные бэкенду)
function normalizeTopicName(name) {
    if (!name) return "";
    name = name.trim();
    if (name) {
        name = name[0].toUpperCase() + name.slice(1).toLowerCase();
    }
    return name;
}

function normalizeHashtagName(name) {
    if (!name) return "";
    if (name.startsWith('#')) {
        name = name.slice(1);
    }
    name = name.trim().toLowerCase();
    name = name.replace(/ё/g, 'е');
    return name;
}

function normalizeCategoryName(name) {
    if (!name) return "";
    name = name.trim().toLowerCase();
    name = name.replace(/ё/g, 'е');
    return name;
}

// Функция проверки существования элемента по нормализованному имени
function checkExists(items, normalizedName, normalizeFunc) {
    return items.some(item => {
        const normalized = normalizeFunc(item.Name || item.name || item.text);
        return normalized === normalizedName;
    });
}

document.addEventListener('DOMContentLoaded', async function () {
    const problemModalOverlay = document.getElementById('problem-modal-overlay');
    const problemModal = document.getElementById('problem-modal');
    const addProblemBtn = document.getElementById('addProblem');
    const closeProblemModalBtn = document.getElementById('closeProblemModal');
    const form = document.getElementById('problemForm');
    const categorySelect = document.getElementById('categorySelect');
    const saveBtn = form?.querySelector('.save-btn');
    const clearBtn = form?.querySelector('#clearProblemBtn');

    if (!problemModalOverlay || !problemModal || !addProblemBtn || !form || !categorySelect) {
        console.error('Не найдены необходимые элементы DOM для модального окна проблемы');
        return;
    }

    // Добавим скрытые поля для ID
    const topicIDHidden = document.createElement('input');
    topicIDHidden.type = 'hidden';
    topicIDHidden.name = 'topicID';
    topicIDHidden.id = 'topicID';
    form.appendChild(topicIDHidden);

    const hashtagsIDsHidden = document.createElement('input');
    hashtagsIDsHidden.type = 'hidden';
    hashtagsIDsHidden.name = 'hashtagsIDs';
    hashtagsIDsHidden.id = 'hashtagsIDs';
    form.appendChild(hashtagsIDsHidden);

    // Функция загрузки категорий
    async function loadCategories() {
        try {
            const token = localStorage.getItem('accessToken');
            const response = await fetch('/api/categories', {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) throw new Error('Ошибка загрузки категорий');
            
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

    // Функции для открытия/закрытия модального окна
    function openProblemModal() {
        problemModalOverlay.classList.add('active');
        document.body.style.overflow = 'hidden';
        loadCategories();
    }

    function closeProblemModal() {
        problemModalOverlay.classList.remove('active');
        document.body.style.overflow = '';
        form.reset();
        if (generalTopicTomSelect) generalTopicTomSelect.clear();
        if (hashtagsTomSelect) hashtagsTomSelect.clear();
        topicIDHidden.value = '';
        hashtagsIDsHidden.value = '';
    }

    // Обработчики событий
    addProblemBtn.addEventListener('click', async () => {
        try {
            await auth.checkAuth(true);
            openProblemModal();
        } catch (error) {
            console.error('Ошибка авторизации:', error);
        }
    });

    if (closeProblemModalBtn) {
        closeProblemModalBtn.addEventListener('click', closeProblemModal);
    }

    problemModalOverlay.addEventListener('click', (e) => {
        if (e.target === problemModalOverlay) {
            closeProblemModal();
        }
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && problemModalOverlay.classList.contains('active')) {
            closeProblemModal();
        }
    });

    // Инициализация Tom Select для тем
    const generalTopicSelect = document.getElementById('generalTopicSelect');
    if (generalTopicSelect) {
        generalTopicTomSelect = new TomSelect('#generalTopicSelect', {
            // Меняем дефолтный wrapperClass="ts-wrapper" на свой
            wrapperClass: 'vs-wrapper',
            multiple: false,
            placeholder: 'Выберите общую тему или введите новую',
            searchField: ['text'],
            valueField: 'value',
            labelField: 'text',
            maxOptions: null,
            loadThrottle: 300, // Задержка перед загрузкой (мс)
            shouldLoad: function(query) {
                // Загружаем только если введено 2+ символа
                return query && query.length >= TOPIC_MIN_QUERY_LEN;
            },
            create: function(input, callback) {
                // Позволяем создавать новые темы прямо из поля ввода
                const value = input.trim();
                if (!value) {
                    callback(null);
                    return;
                }
                
                // Проверяем, нет ли уже такой темы в загруженных опциях
                const normalized = normalizeTopicName(value);
                const allOptions = generalTopicTomSelect.options;
                const existingOptions = Object.values(allOptions).map(opt => ({ Name: opt.text }));
                
                if (checkExists(existingOptions, normalized, normalizeTopicName)) {
                    callback(null); // Не показываем опцию создания, если уже существует
                    return;
                }
                
                // Создаем временную опцию для отображения
                callback({
                    value: '__new__' + value,
                    text: value + ' (создать новую)'
                });
            },
            createOnBlur: true,
            load: function (query, callback) {
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
                        
                        // Проверяем, нет ли уже такой темы (с учетом нормализации)
                        const normalizedQuery = normalizeTopicName(query);
                        const exists = checkExists(data, normalizedQuery, (name) => normalizeTopicName(name));
                        
                        // Если ничего не найдено и такой темы не существует, показываем опцию создания
                        if (options.length === 0 && query.length >= TOPIC_MIN_QUERY_LEN && !exists) {
                            options.push({
                                value: '__new__' + query,
                                text: query + ' (создать новую)'
                            });
                        } else if (options.length > 0 && !exists) {
                            // Если найдены похожие, но не точное совпадение, проверяем еще раз
                            const exactMatch = data.some(item => {
                                const normalized = normalizeTopicName(item.Name);
                                return normalized === normalizedQuery;
                            });
                            if (!exactMatch && query.length >= TOPIC_MIN_QUERY_LEN) {
                                options.push({
                                    value: '__new__' + query,
                                    text: query + ' (создать новую)'
                                });
                            }
                        }
                        callback(options);
                    })
                    .catch(err => {
                        console.error('Ошибка загрузки тем:', err);
                        callback();
                    });
            },
            onChange: async function (value) {
                if (!value) {
                    topicIDHidden.value = '';
                    return;
                }
                
                // Если это новая тема (начинается с __new__)
                if (value.startsWith('__new__')) {
                    const topicName = value.replace('__new__', '');
                    
                    // Проверяем еще раз перед созданием
                    const normalized = normalizeTopicName(topicName);
                    const allOptions = generalTopicTomSelect.options;
                    const existingOptions = Object.values(allOptions)
                        .filter(opt => !opt.value.startsWith('__new__'))
                        .map(opt => ({ Name: opt.text }));
                    
                    if (checkExists(existingOptions, normalized, normalizeTopicName)) {
                        alert('Тема с таким именем уже существует');
                        generalTopicTomSelect.clear();
                        return;
                    }
                    
                    try {
                        const token = localStorage.getItem('accessToken');
                        const response = await fetch('/api/topics', {
                            method: 'POST',
                            headers: { 
                                'Content-Type': 'application/json',
                                'Authorization': `Bearer ${token}`
                            },
                            body: JSON.stringify({ name: topicName })
                        });
                        
                        if (response.ok) {
                            const newTopic = await response.json();
                            // Удаляем временную опцию и добавляем реальную
                            generalTopicTomSelect.removeOption(value);
                            generalTopicTomSelect.addOption({ 
                                value: newTopic.ID.toString(), 
                                text: newTopic.Name 
                            });
                            generalTopicTomSelect.setValue(newTopic.ID.toString());
                            topicIDHidden.value = newTopic.ID.toString();
                            // Закрываем выпадающий список после установки значения
                            setTimeout(() => {
                                if (generalTopicTomSelect.isOpen) {
                                    generalTopicTomSelect.close();
                                    generalTopicTomSelect.blur();
                                }
                                // Принудительно скрываем выпадающий список
                                const tsWrapper = generalTopicSelect.closest('.vs-wrapper');
                                if (tsWrapper) {
                                    const tsDropdown = tsWrapper.querySelector('.ts-dropdown');
                                    if (tsDropdown) {
                                        tsDropdown.style.display = 'none';
                                        tsDropdown.style.visibility = 'hidden';
                                        tsDropdown.style.opacity = '0';
                                        tsWrapper.classList.remove('focus', 'input-active');
                                    }
                                }
                            }, 0);
                        } else {
                            const error = await response.json();
                            const errorMsg = error.error || 'Неизвестная ошибка';
                            if (errorMsg.includes('уже существует')) {
                                alert('Тема с таким именем уже существует');
                            } else {
                                alert('Ошибка создания темы: ' + errorMsg);
                            }
                            generalTopicTomSelect.clear();
                        }
                    } catch (error) {
                        alert('Сетевая ошибка при создании темы: ' + error.message);
                        generalTopicTomSelect.clear();
                    }
                } else {
                    topicIDHidden.value = value;
                    // Закрываем выпадающий список после выбора существующей темы
                    setTimeout(() => {
                        if (generalTopicTomSelect.isOpen) {
                            generalTopicTomSelect.close();
                            generalTopicTomSelect.blur();
                        }
                    }, 0);
                }
            },
            onItemAdd: function(value, item) {
                // Закрываем выпадающий список после выбора
                const self = this;
                setTimeout(() => {
                    self.close();
                    self.blur();
                    // Принудительно скрываем выпадающий список
                    const tsWrapper = generalTopicSelect.closest('.vs-wrapper');
                    if (tsWrapper) {
                        const tsDropdown = tsWrapper.querySelector('.ts-dropdown');
                        if (tsDropdown) {
                            tsDropdown.style.display = 'none';
                            tsDropdown.style.visibility = 'hidden';
                            tsDropdown.style.opacity = '0';
                            tsWrapper.classList.remove('focus', 'input-active');
                        }
                    }
                }, 0);
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
                    const isNew = item.value && item.value.startsWith('__new__');
                    const icon = isNew ? '<span style="color: #4CAF50;">+ </span>' : '';
                    return `<div>${icon}${escape(item.text)}</div>`;
                },
                item: function (item, escape) {
                    return `<div>${escape(item.text)}</div>`;
                },
                no_results: function(data, escape) {
                    return `<div class="no-results">Ничего не найдено. Введите минимум ${TOPIC_MIN_QUERY_LEN} символа(ов) для поиска или нажмите Enter для создания новой темы.</div>`;
                }
            }
        });
        
        // Функция для принудительного закрытия выпадающего списка
        const forceCloseDropdown = function() {
            const tsWrapper = generalTopicSelect.closest('.vs-wrapper');
            if (tsWrapper) {
                const tsDropdown = tsWrapper.querySelector('.ts-dropdown');
                if (tsDropdown) {
                    // Принудительно скрываем через стили
                    tsDropdown.style.display = 'none';
                    tsDropdown.style.visibility = 'hidden';
                    tsDropdown.style.opacity = '0';
                    // Убираем классы, которые могут показывать список
                    tsWrapper.classList.remove('focus', 'input-active');
                }
            }
            if (generalTopicTomSelect) {
                generalTopicTomSelect.close();
                generalTopicTomSelect.blur();
            }
        };
        
        // Используем событие item_select для закрытия списка при выборе опции
        generalTopicTomSelect.on('item_select', function() {
            setTimeout(forceCloseDropdown, 0);
        });
        
        // Используем событие item_add для закрытия списка
        generalTopicTomSelect.on('item_add', function() {
            setTimeout(forceCloseDropdown, 0);
        });
        
        // Добавляем обработчик клика на опции для закрытия списка (capture phase)
        const closeDropdownOnClick = function(event) {
            const option = event.target.closest('[data-selectable]');
            if (option && option.getAttribute('data-selectable') !== 'false') {
                // Закрываем список сразу после клика
                setTimeout(forceCloseDropdown, 10);
            }
        };
        
        // Добавляем обработчик после инициализации
        setTimeout(() => {
            const tsWrapper = generalTopicSelect.closest('.vs-wrapper');
            if (tsWrapper) {
                const tsDropdown = tsWrapper.querySelector('.ts-dropdown');
                if (tsDropdown) {
                    // Используем click с capture для надежного закрытия
                    tsDropdown.addEventListener('click', closeDropdownOnClick, true);
                    // Также добавляем mousedown для более быстрого закрытия
                    tsDropdown.addEventListener('mousedown', closeDropdownOnClick, true);
                }
                
                // Добавляем обработчик ввода для автоматического открытия списка
                const input = tsWrapper.querySelector('input[type="text"]');
                if (input) {
                    input.addEventListener('input', function(e) {
                        const query = (e.target.value || '').trim();
                        if (query.length >= TOPIC_MIN_QUERY_LEN) {
                            // Принудительно вызываем загрузку и открываем список
                            if (generalTopicTomSelect) {
                                generalTopicTomSelect.load(query);
                                generalTopicTomSelect.open();
                            }
                        } else {
                            if (generalTopicTomSelect) {
                                generalTopicTomSelect.close();
                            }
                        }
                    });
                }
            }
        }, 100);
        
        // Добавляем обработчик клика вне выпадающего списка для его закрытия
        document.addEventListener('click', function(event) {
            const tsWrapper = generalTopicSelect.closest('.vs-wrapper');
            if (tsWrapper && !tsWrapper.contains(event.target)) {
                if (generalTopicTomSelect && generalTopicTomSelect.isOpen) {
                    generalTopicTomSelect.close();
                }
            }
        });
    }

    // Инициализация Tom Select для хэштегов
    const hashtagsElement = document.getElementById('hashtags');
    if (hashtagsElement) {
        hashtagsTomSelect = new TomSelect('#hashtags', {
            // Меняем дефолтный wrapperClass="ts-wrapper" на свой
            wrapperClass: 'vs-wrapper',
            plugins: ['remove_button'],
            multiple: true,
            placeholder: 'Выберите хэштеги или введите новый',
            searchField: ['text'],
            valueField: 'value',
            labelField: 'text',
            create: function(input, callback) {
                // Позволяем создавать новые хэштеги прямо из поля ввода
                let value = input.trim();
                if (!value) {
                    callback(null);
                    return;
                }
                
                // Добавляем # если его нет
                if (!value.startsWith('#')) {
                    value = '#' + value;
                }
                
                // Проверяем, нет ли уже такого хэштега в загруженных опциях
                const normalized = normalizeHashtagName(value);
                const allOptions = hashtagsTomSelect.options;
                const existingOptions = Object.values(allOptions).map(opt => ({ Name: opt.text }));
                
                if (checkExists(existingOptions, normalized, normalizeHashtagName)) {
                    callback(null); // Не показываем опцию создания, если уже существует
                    return;
                }
                
                // Создаем временную опцию для отображения
                callback({
                    value: '__new__' + value,
                    text: value + ' (создать новый)'
                });
            },
            createOnBlur: true,
            load: function (query, callback) {
                if (query.length < 2) return callback();
                
                const token = localStorage.getItem('accessToken');
                fetch(`/api/hashtags?q=${encodeURIComponent(query)}`, {
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    }
                })
                    .then(res => {
                        if (!res.ok) throw new Error('Ошибка загрузки хэштегов');
                        return res.json();
                    })
                    .then(data => {
                        const options = data.map(item => ({
                            value: item.ID.toString(),
                            text: item.Name
                        }));
                        
                        // Подготавливаем имя хэштега для проверки
                        let hashtagName = query.trim();
                        if (!hashtagName.startsWith('#')) {
                            hashtagName = '#' + hashtagName;
                        }
                        
                        // Проверяем, нет ли уже такого хэштега (с учетом нормализации)
                        const normalizedQuery = normalizeHashtagName(hashtagName);
                        const exists = checkExists(data, normalizedQuery, (name) => normalizeHashtagName(name));
                        
                        // Если ничего не найдено и такого хэштега не существует, показываем опцию создания
                        if (options.length === 0 && query.length >= 2 && !exists) {
                            options.push({
                                value: '__new__' + hashtagName,
                                text: hashtagName + ' (создать новый)'
                            });
                        } else if (options.length > 0 && !exists) {
                            // Если найдены похожие, но не точное совпадение, проверяем еще раз
                            const exactMatch = data.some(item => {
                                const normalized = normalizeHashtagName(item.Name);
                                return normalized === normalizedQuery;
                            });
                            if (!exactMatch && query.length >= 2) {
                                options.push({
                                    value: '__new__' + hashtagName,
                                    text: hashtagName + ' (создать новый)'
                                });
                            }
                        }
                        callback(options);
                    })
                    .catch(err => {
                        console.error('Ошибка загрузки хэштегов:', err);
                        callback();
                    });
            },
            onChange: async function (values) {
                if (!values || values.length === 0) {
                    hashtagsIDsHidden.value = '';
                    return;
                }
                
                const processedValues = [];
                const newHashtags = [];
                
                // Обрабатываем каждое значение
                for (const value of values) {
                    if (value.startsWith('__new__')) {
                        newHashtags.push(value);
                    } else {
                        processedValues.push(value);
                    }
                }
                
                // Создаем новые хэштеги
                if (newHashtags.length > 0) {
                    try {
                        const token = localStorage.getItem('accessToken');
                        
                        // Проверяем каждый новый хэштег перед созданием
                        const allOptions = hashtagsTomSelect.options;
                        const existingOptions = Object.values(allOptions)
                            .filter(opt => !opt.value.startsWith('__new__'))
                            .map(opt => ({ Name: opt.text }));
                        
                        for (const tempValue of newHashtags) {
                            const hashtagName = tempValue.replace('__new__', '');
                            const normalized = normalizeHashtagName(hashtagName);
                            
                            if (checkExists(existingOptions, normalized, normalizeHashtagName)) {
                                alert(`Хэштег "${hashtagName}" уже существует`);
                                hashtagsTomSelect.removeItem(tempValue);
                                continue;
                            }
                        }
                        
                        // Фильтруем уже проверенные хэштеги
                        const validNewHashtags = newHashtags.filter(tempValue => {
                            const hashtagName = tempValue.replace('__new__', '');
                            const normalized = normalizeHashtagName(hashtagName);
                            return !checkExists(existingOptions, normalized, normalizeHashtagName);
                        });
                        
                        if (validNewHashtags.length === 0) {
                            return;
                        }
                        
                        const createPromises = validNewHashtags.map(async (tempValue) => {
                            const hashtagName = tempValue.replace('__new__', '');
                            const response = await fetch('/api/hashtags', {
                                method: 'POST',
                                headers: { 
                                    'Content-Type': 'application/json',
                                    'Authorization': `Bearer ${token}`
                                },
                                body: JSON.stringify({ name: hashtagName })
                            });
                            
                            if (response.ok) {
                                const newHashtag = await response.json();
                                // Удаляем временную опцию и добавляем реальную
                                hashtagsTomSelect.removeOption(tempValue);
                                hashtagsTomSelect.addOption({ 
                                    value: newHashtag.ID.toString(), 
                                    text: newHashtag.Name 
                                });
                                return newHashtag.ID.toString();
                            } else {
                                const error = await response.json();
                                const errorMsg = error.error || 'Неизвестная ошибка';
                                if (errorMsg.includes('уже существует')) {
                                    throw new Error('Хэштег с таким именем уже существует');
                                }
                                throw new Error(errorMsg);
                            }
                        });
                        
                        const newIds = await Promise.all(createPromises);
                        processedValues.push(...newIds);
                        
                        // Обновляем выбранные значения
                        hashtagsTomSelect.setValue(processedValues);
                    } catch (error) {
                        alert('Ошибка создания хэштега: ' + error.message);
                        // Удаляем проблемные значения
                        newHashtags.forEach(tempValue => {
                            hashtagsTomSelect.removeItem(tempValue);
                        });
                    }
                }
                
                hashtagsIDsHidden.value = processedValues.join(',');
            },
            render: {
                option: function (item, escape) {
                    const isNew = item.value && item.value.startsWith('__new__');
                    const icon = isNew ? '<span style="color: #4CAF50;">+ </span>' : '';
                    return `<div>${icon}${escape(item.text)}</div>`;
                },
                item: function (item, escape) {
                    return `<div>${escape(item.text)}</div>`;
                },
                no_results: function(data, escape) {
                    return '<div class="no-results">Ничего не найдено. Нажмите Enter для создания нового хэштега.</div>';
                }
            }
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

    // Обработчики для кнопок добавления
    const addTopicBtn = document.getElementById('addTopicBtn');
    const addCategoryBtn = document.getElementById('addCategoryBtn');
    const addHashtagBtn = document.getElementById('addHashtagBtn');

    if (addTopicBtn) addTopicBtn.addEventListener('click', () => showModal(topicModal));
    if (addCategoryBtn) addCategoryBtn.addEventListener('click', () => showModal(categoryModal));
    if (addHashtagBtn) addHashtagBtn.addEventListener('click', () => showModal(hashtagModal));

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
            
            // Проверяем, нет ли уже такой темы
            const normalized = normalizeTopicName(name);
            if (generalTopicTomSelect) {
                const allOptions = generalTopicTomSelect.options;
                const existingOptions = Object.values(allOptions)
                    .filter(opt => !opt.value.startsWith('__new__'))
                    .map(opt => ({ Name: opt.text }));
                
                if (checkExists(existingOptions, normalized, normalizeTopicName)) {
                    topicError.textContent = 'Тема с таким именем уже существует';
                    return;
                }
            }
            
            try {
                const token = localStorage.getItem('accessToken');
                const response = await fetch('/api/topics', {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify({ name: name })
                });
                
                if (response.ok) {
                    const newTopic = await response.json();
                    if (generalTopicTomSelect) {
                        generalTopicTomSelect.addOption({ 
                            value: newTopic.ID.toString(), 
                            text: newTopic.Name 
                        });
                        generalTopicTomSelect.setValue(newTopic.ID.toString());
                    }
                    hideModal();
                } else {
                    const error = await response.json();
                    const errorMsg = error.error || 'Неизвестная ошибка';
                    if (errorMsg.includes('уже существует')) {
                        topicError.textContent = 'Тема с таким именем уже существует';
                    } else {
                        topicError.textContent = 'Ошибка: ' + errorMsg;
                    }
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
            
            // Проверяем, нет ли уже такой категории
            const normalized = normalizeCategoryName(name);
            const existingCategories = Array.from(categorySelect.options)
                .filter(opt => opt.value)
                .map(opt => ({ Name: opt.textContent }));
            
            if (checkExists(existingCategories, normalized, normalizeCategoryName)) {
                categoryError.textContent = 'Категория с таким именем уже существует';
                return;
            }
            
            try {
                const token = localStorage.getItem('accessToken');
                const response = await fetch('/api/categories', {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify({ name: name })
                });
                
                if (response.ok) {
                    const newCategory = await response.json();
                    const option = document.createElement('option');
                    option.value = newCategory.ID;
                    option.textContent = newCategory.Name;
                    categorySelect.appendChild(option);
                    categorySelect.value = newCategory.ID;
                    hideModal();
                } else {
                    const error = await response.json();
                    const errorMsg = error.error || 'Неизвестная ошибка';
                    if (errorMsg.includes('уже существует')) {
                        categoryError.textContent = 'Категория с таким именем уже существует';
                    } else {
                        categoryError.textContent = 'Ошибка: ' + errorMsg;
                    }
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
            
            let name = hashtagNameInput.value.trim();
            if (!name) {
                hashtagError.textContent = 'Пожалуйста, введите имя хэштега.';
                return;
            }
            
            // Добавляем # если его нет
            if (!name.startsWith('#')) {
                name = '#' + name;
            }
            
            // Проверяем, нет ли уже такого хэштега
            const normalized = normalizeHashtagName(name);
            if (hashtagsTomSelect) {
                const allOptions = hashtagsTomSelect.options;
                const existingOptions = Object.values(allOptions)
                    .filter(opt => !opt.value.startsWith('__new__'))
                    .map(opt => ({ Name: opt.text }));
                
                if (checkExists(existingOptions, normalized, normalizeHashtagName)) {
                    hashtagError.textContent = 'Хэштег с таким именем уже существует';
                    return;
                }
            }
            
            try {
                const token = localStorage.getItem('accessToken');
                const response = await fetch('/api/hashtags', {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify({ name: name })
                });
                
                if (response.ok) {
                    const newHashtag = await response.json();
                    if (hashtagsTomSelect) {
                        hashtagsTomSelect.addOption({ 
                            value: newHashtag.ID.toString(), 
                            text: newHashtag.Name 
                        });
                        hashtagsTomSelect.addItem(newHashtag.ID.toString());
                    }
                    hideModal();
                } else {
                    const error = await response.json();
                    const errorMsg = error.error || 'Неизвестная ошибка';
                    if (errorMsg.includes('уже существует')) {
                        hashtagError.textContent = 'Хэштег с таким именем уже существует';
                    } else {
                        hashtagError.textContent = 'Ошибка: ' + errorMsg;
                    }
                }
            } catch (error) {
                hashtagError.textContent = 'Сетевая ошибка: ' + error.message;
            }
        });
    }

    // Обработчик для кнопки "Сохранить"
    if (saveBtn) {
        form.addEventListener('submit', async function (event) {
            event.preventDefault();

            // Валидация
            const problemTitle = document.getElementById('problemTitle').value.trim();
            const problemDescription = document.getElementById('problemDescription').value.trim();
            const categoryValue = categorySelect.value;
            
            if (!problemTitle) {
                alert('Пожалуйста, введите название проблемы');
                return;
            }
            
            if (!problemDescription) {
                alert('Пожалуйста, введите описание проблемы');
                return;
            }
            
            if (!categoryValue) {
                alert('Пожалуйста, выберите категорию');
                return;
            }

            // Собираем данные из формы
            const formData = new FormData();
            formData.append('name', problemTitle);
            formData.append('describe', problemDescription);
            formData.append('category_id', categoryValue);
            
            // Тема (если выбрана)
            const topicID = document.getElementById('topicID').value;
            if (topicID) {
                formData.append('topic_id', topicID);
            }
            
            // Хэштеги (если выбраны)
            const hashtagsIDs = document.getElementById('hashtagsIDs').value;
            if (hashtagsIDs) {
                formData.append('hashtags', hashtagsIDs);
            }
            
            // Изображение
            const problemImage = document.getElementById('problemImage').files[0];
            if (problemImage) {
                formData.append('image', problemImage);
            }

            try {
                const token = localStorage.getItem('accessToken');
                const response = await fetch('/api/problems', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`
                    },
                    body: formData
                });

                if (response.status === 401) {
                    const refreshed = await auth.refreshToken();
                    if (refreshed) {
                        // Повторяем отправку
                        form.dispatchEvent(new Event('submit', { cancelable: true }));
                        return;
                    }
                    throw new Error('Требуется авторизация');
                }
                
                if (response.ok) {
                    const result = await response.json();
                    alert('Проблема успешно сохранена! ID: ' + result.id);
                    closeProblemModal();
                    
                    // Перезагружаем страницу для обновления списка
                    window.location.reload();
                } else {
                    const error = await response.json();
                    alert('Ошибка: ' + (error.error || 'Неизвестная ошибка'));
                }
            } catch (error) {
                alert('Сетевая ошибка: ' + error.message);
            }
        });
    }

    // Обработчик для кнопки "Очистить"
    if (clearBtn) {
        clearBtn.addEventListener('click', function () {
            form.reset();
            document.getElementById('topicID').value = '';
            document.getElementById('hashtagsIDs').value = '';
            
            if (generalTopicTomSelect) generalTopicTomSelect.clear();
            if (hashtagsTomSelect) hashtagsTomSelect.clear();
        });
    }
});

