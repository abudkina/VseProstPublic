// add_problem.js
import * as auth from './authorizationFunctions.js';

let generalTopicTomSelect;
const MAX_HASHTAGS = 5;
const selectedHashtags = []; // { id, name }
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
    // Проверяем аутентификацию
    try {
        await auth.checkAuth(true);
    } catch (error) {
        return;
    }

    const form = document.getElementById('problemForm');
    const categorySelect = document.getElementById('categorySelect');
    const saveBtn = document.querySelector('.save-btn');
    const clearBtn = document.querySelector('.clear-btn');

    if (!form || !categorySelect || !saveBtn || !clearBtn) {
        console.error('Не найдены необходимые элементы DOM');
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
            const response = await fetch(API_CONFIG.buildURL(API_CONFIG.ENDPOINTS.CATEGORIES), {
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

    // Загружаем категории
    await loadCategories();

    // Инициализация Tom Select для тем
    const generalTopicSelect = document.getElementById('generalTopicSelect');
    if (generalTopicSelect) {
        generalTopicTomSelect = new TomSelect('#generalTopicSelect', {
            wrapperClass: 'vs-wrapper',
            controlClass: 'ts-control vs-control',
            multiple: false,
            placeholder: 'Выберите общую тему',
            searchField: ['text'],
            valueField: 'value',
            labelField: 'text',
            maxItems: 1,
            maxOptions: null,
            loadThrottle: 300,
            create: false,
            dropdownParent: 'body',
            shouldLoad: function(query) {
                return query !== undefined && (query.length === 0 || query.length >= TOPIC_MIN_QUERY_LEN);
            },
            load: function (query, callback) {
                const q = (query || '').trim();
                const token = localStorage.getItem('accessToken');
                const url = q.length >= TOPIC_MIN_QUERY_LEN
                    ? API_CONFIG.buildURLWithParams(API_CONFIG.ENDPOINTS.TOPICS, { search: q })
                    : API_CONFIG.buildURL(API_CONFIG.ENDPOINTS.TOPICS);
                fetch(url, {
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
            onChange: function (value) {
                if (!value) {
                    topicIDHidden.value = '';
                    return;
                }
                topicIDHidden.value = value;
                setTimeout(() => {
                    if (generalTopicTomSelect.isOpen) generalTopicTomSelect.close();
                    generalTopicTomSelect.blur();
                }, 0);
            },
            onItemAdd: function() {
                const self = this;
                setTimeout(() => { self.close(); self.blur(); }, 0);
            },
            onFocus: function() {
                const q = (this.control_input?.value || '').trim();
                if (q.length >= TOPIC_MIN_QUERY_LEN) {
                    this.open();
                } else {
                    this.load('', () => { this.open(); });
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
                no_results: function(data, escape) {
                    return `<div class="no-results">Ничего не найдено. Введите минимум ${TOPIC_MIN_QUERY_LEN} символа(ов) для поиска.</div>`;
                }
            }
        });
        
        const forceCloseDropdown = function() {
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

    // Поле выбора хэштегов (search-select)
    const wrapHashtags = document.getElementById('wrap-hashtags');
    const hashtagsInput = document.getElementById('filter-hashtags-input');
    const hashtagsTags = document.getElementById('filter-hashtags-tags');
    const hashtagsDropdown = document.getElementById('filter-hashtags-dropdown');
    function syncHashtagsToHidden() {
        hashtagsIDsHidden.value = selectedHashtags.map(h => h.id).join(',');
    }
    function renderHashtagsTags() {
        const frag = document.createDocumentFragment();
        selectedHashtags.forEach(h => {
            const span = document.createElement('span');
            span.className = 'search-select-tag';
            span.textContent = h.name + ' ';
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'tag-remove';
            btn.setAttribute('data-id', h.id);
            btn.setAttribute('aria-label', 'Удалить');
            btn.textContent = '×';
            btn.addEventListener('click', () => {
                const i = selectedHashtags.findIndex(x => String(x.id) === String(h.id));
                if (i !== -1) selectedHashtags.splice(i, 1);
                renderHashtagsTags();
                syncHashtagsToHidden();
            });
            span.appendChild(btn);
            frag.appendChild(span);
        });
        hashtagsTags.innerHTML = '';
        hashtagsTags.appendChild(frag);
    }
    function addHashtag(id, name) {
        if (selectedHashtags.length >= MAX_HASHTAGS) return;
        const sid = String(id);
        if (selectedHashtags.some(h => String(h.id) === sid)) return;
        selectedHashtags.push({ id: sid, name: name || '#' + id });
        renderHashtagsTags();
        syncHashtagsToHidden();
    }
    function clearHashtagsWidget() {
        selectedHashtags.length = 0;
        renderHashtagsTags();
        syncHashtagsToHidden();
        if (hashtagsInput) hashtagsInput.value = '';
        if (hashtagsDropdown) hashtagsDropdown.classList.remove('active');
    }
    if (wrapHashtags && hashtagsInput && hashtagsTags && hashtagsDropdown) {
        let searchTimeout;
        hashtagsInput.addEventListener('input', () => {
            const q = hashtagsInput.value.trim();
            clearTimeout(searchTimeout);
            if (q.length < 2) {
                hashtagsDropdown.classList.remove('active');
                return;
            }
            searchTimeout = setTimeout(async () => {
                try {
                    const token = localStorage.getItem('accessToken');
                    const res = await fetch(API_CONFIG.buildURLWithParams('/hashtags/search', { q }), {
                        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
                        credentials: 'include'
                    });
                    if (!res.ok) throw new Error('Ошибка загрузки хэштегов');
                    const data = await res.json();
                    const list = Array.isArray(data) ? data : (data.hashtags || []);
                    hashtagsDropdown.innerHTML = '';
                    list.forEach(item => {
                        const id = item.ID != null ? item.ID : item.id;
                        const name = item.Name != null ? item.Name : item.name;
                        if (selectedHashtags.some(h => String(h.id) === String(id))) return;
                        const div = document.createElement('div');
                        div.className = 'dropdown-item';
                        div.textContent = name;
                        div.addEventListener('click', () => {
                            addHashtag(id, name);
                            hashtagsInput.value = '';
                            hashtagsDropdown.classList.remove('active');
                        });
                        hashtagsDropdown.appendChild(div);
                    });
                    hashtagsDropdown.classList.add('active');
                } catch (err) {
                    console.error('Ошибка загрузки хэштегов:', err);
                    hashtagsDropdown.classList.remove('active');
                }
            }, 300);
        });
        hashtagsInput.addEventListener('focus', () => {
            if (hashtagsInput.value.trim().length >= 2 && hashtagsDropdown.children.length) hashtagsDropdown.classList.add('active');
        });
        document.addEventListener('click', (e) => {
            if (wrapHashtags && !wrapHashtags.contains(e.target)) hashtagsDropdown.classList.remove('active');
        });
    }

    // Функции для модальных окон
    const modalOverlay = document.getElementById('modal-overlay');
    const topicModal = document.getElementById('topic-modal');
    const categoryModal = document.getElementById('category-modal');
    const hashtagModal = document.getElementById('hashtag-modal');

    function showModal(modal) {
        if (modalOverlay && modal) {
            modalOverlay.style.display = 'flex';
            modal.style.display = 'block';
            const input = modal.querySelector('input');
            if (input) setTimeout(() => input.focus(), 0);
        }
    }

    function hideModal() {
        if (modalOverlay) modalOverlay.style.display = 'none';
        if (topicModal) topicModal.style.display = 'none';
        if (categoryModal) categoryModal.style.display = 'none';
        if (hashtagModal) hashtagModal.style.display = 'none';
        
        document.querySelectorAll('.error-message').forEach(el => el.textContent = '');
        document.querySelectorAll('.modal input').forEach(inp => inp.value = '');
    }

    if (modalOverlay) {
        modalOverlay.addEventListener('click', (e) => {
            if (e.target === modalOverlay) hideModal();
        });
    }

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') hideModal();
    });

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
            
            const normalized = normalizeHashtagName(name);
            if (selectedHashtags.some(h => normalizeHashtagName(h.name) === normalized)) {
                hashtagError.textContent = 'Хэштег с таким именем уже добавлен';
                return;
            }

            const token = localStorage.getItem('accessToken');
            try {
                const checkRes = await fetch(API_CONFIG.buildURLWithParams('/hashtags/search', { q: name }), {
                    headers: { 'Authorization': `Bearer ${token}` },
                    credentials: 'include'
                });
                if (checkRes.ok) {
                    const checkData = await checkRes.json();
                    const list = Array.isArray(checkData) ? checkData : (checkData.hashtags || []);
                    const exists = list.some(h => {
                        const n = (h.Name != null ? h.Name : h.name) || '';
                        return normalizeHashtagName(n) === normalized;
                    });
                    if (exists) {
                        hashtagError.textContent = 'Хэштег с таким именем уже существует';
                        return;
                    }
                }
            } catch (_) { /* продолжаем создание при ошибке проверки */ }

            try {
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
                    addHashtag(newHashtag.ID, newHashtag.Name);
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

    // Отправка формы (вызывается из submit и при повторе после 401)
    async function submitProblem() {
        const problemTitle = document.getElementById('problemTitle').value.trim();
        const problemDescription = document.getElementById('problemDescription').value.trim();
        const categoryValue = categorySelect.value;

        if (!problemTitle) {
            alert('Пожалуйста, введите название проблемы');
            return;
        }
        if (!categoryValue) {
            alert('Пожалуйста, выберите категорию');
            return;
        }

        const formData = new FormData();
        formData.append('name', problemTitle);
        formData.append('describe', problemDescription);
        formData.append('category_id', categoryValue);

        const topicID = document.getElementById('topicID').value;
        if (topicID) formData.append('topic_id', topicID);

        const hashtagsIDs = document.getElementById('hashtagsIDs').value;
        if (hashtagsIDs) formData.append('hashtags', hashtagsIDs);

        const problemImageEl = document.getElementById('problemImage');
        const problemImageErrorEl = document.getElementById('problemImageError');
        if (problemImageErrorEl) problemImageErrorEl.textContent = '';
        const problemImage = problemImageEl?.files[0];
        if (problemImage) formData.append('image', problemImage);

        const token = localStorage.getItem('accessToken');
        const response = await fetch(API_CONFIG.buildURL(API_CONFIG.ENDPOINTS.PROBLEMS), {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` },
            body: formData
        });

        if (response.status === 401) {
            const refreshed = await auth.refreshToken();
            if (refreshed) {
                await submitProblem();
                return;
            }
            throw new Error('Требуется авторизация');
        }

        if (response.ok) {
            const result = await response.json();
            const problemId = result.id || result.problem?.ID;
            if (problemId) {
                window.location.href = '/problem/' + problemId;
                return;
            }
            form.reset();
            if (generalTopicTomSelect) generalTopicTomSelect.clear();
            clearHashtagsWidget();
            document.getElementById('topicID').value = '';
            document.getElementById('hashtagsIDs').value = '';
        } else {
            let msg = 'Неизвестная ошибка';
            try {
                const data = await response.json();
                msg = data.error || msg;
                if (problemImageErrorEl) {
                    problemImageErrorEl.textContent = msg;
                    problemImageErrorEl.style.display = '';
                }
            } catch (_) {
                msg = await response.text() || response.statusText || msg;
            }
            alert('Ошибка: ' + msg);
        }
    }

    form.addEventListener('submit', async function (event) {
        event.preventDefault();
        if (saveBtn.disabled) return;
        saveBtn.disabled = true;
        try {
            await submitProblem();
        } catch (error) {
            alert('Ошибка: ' + (error.message || 'Не удалось отправить запрос'));
        } finally {
            saveBtn.disabled = false;
        }
    });

    const problemImageInput = document.getElementById('problemImage');
    if (problemImageInput) {
        problemImageInput.addEventListener('change', function () {
            const errEl = document.getElementById('problemImageError');
            if (errEl) errEl.textContent = '';
        });
    }
    clearBtn.addEventListener('click', function () {
        form.reset();
        document.getElementById('topicID').value = '';
        document.getElementById('hashtagsIDs').value = '';
        const errEl = document.getElementById('problemImageError');
        if (errEl) errEl.textContent = '';
        if (generalTopicTomSelect) generalTopicTomSelect.clear();
        clearHashtagsWidget();
    });
});