// problemListCommon.js - общая логика для работы со списком проблем
// Используется в index.js и admin_problems.js

import { initTagsScroll } from './tagsScroll.js';

// Re-export initTagsScroll for use in other modules
export { initTagsScroll };

function setFavoriteIconState(iconElement, isFavorite) {
    if (!iconElement) return;
    const isFavoriteFlag = isFavorite === true || isFavorite === 1 || isFavorite === '1';
    iconElement.classList.add('fa-heart');
    iconElement.classList.toggle('favorited', isFavoriteFlag);
    iconElement.classList.toggle('liked', isFavoriteFlag);
    iconElement.classList.toggle('fas', isFavoriteFlag);
    iconElement.classList.toggle('far', !isFavoriteFlag);
    const favoritesWrapper = iconElement.closest('.card-favorites');
    if (favoritesWrapper) {
        favoritesWrapper.classList.toggle('favorited', isFavoriteFlag);
    }
}

/**
 * Загрузка категорий и заполнение select
 */
export async function loadCategories(selectId = 'category', requireAuth = false) {
    try {
        const headers = { 'Content-Type': 'application/json' };
        if (requireAuth) {
            const token = localStorage.getItem('accessToken');
            if (token) headers['Authorization'] = `Bearer ${token}`;
        }
        
        const response = await fetch(`${API_CONFIG.API_URL}/categories`, { headers });
        const categories = await response.json();
        
        const categorySelect = document.getElementById(selectId);
        if (!categorySelect) return;
        
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

/**
 * Инициализация TomSelect для хэштегов
 */
export function initHashtagsTomSelect(selectId = 'hashtags', onItemAdd = null) {
    const hashtagsElement = document.getElementById(selectId);
    if (!hashtagsElement) {
        console.warn(`Элемент с id "${selectId}" не найден`);
        return null;
    }
    
    // Проверяем, не инициализирован ли уже TomSelect на этом элементе
    try {
        // Проверяем прямое свойство tomselect
        if (hashtagsElement.tomselect) {
            if (typeof hashtagsElement.tomselect.destroy === 'function') {
                hashtagsElement.tomselect.destroy();
            }
            // Очищаем свойство вручную на случай, если destroy не сработал полностью
            delete hashtagsElement.tomselect;
        }
    } catch (e) {
        // Игнорируем ошибки при уничтожении, но пытаемся очистить свойство
        console.warn('Предупреждение при проверке TomSelect:', e);
        try {
            if (hashtagsElement.tomselect) {
                delete hashtagsElement.tomselect;
            }
        } catch (e2) {
            // Игнорируем
        }
    }
    
    // Убеждаемся, что элемент все еще в DOM
    const element = document.getElementById(selectId);
    if (!element) {
        console.warn(`Элемент с id "${selectId}" был удален из DOM`);
        return null;
    }
    
    // Финальная проверка перед созданием
    if (element.tomselect) {
        console.warn('TomSelect все еще привязан к элементу, принудительная очистка...');
        try {
            if (typeof element.tomselect.destroy === 'function') {
                element.tomselect.destroy();
            }
        } catch (e) {
            // Игнорируем
        }
        delete element.tomselect;
    }
    
    try {
        // Передаем элемент напрямую (более надежно, чем селектор)
        const instance = new TomSelect(element, {
            // Уходим от дефолтного wrapperClass="ts-wrapper" (часто конфликтует с чужими стилями)
            wrapperClass: 'vs-wrapper',
            controlClass: 'ts-control vs-control',
            valueField: 'ID',
            labelField: 'Name',
            searchField: 'Name',
            maxItems: 5,
            create: false,
            loadThrottle: 300,
            placeholder: 'Выберите хэштеги',
            dropdownParent: 'body', // Рендерим выпадающий список в body, чтобы он был поверх всего
            shouldLoad: function(query) {
                // Показываем выпадающий список только при вводе минимум 2 символов
                return query && query.length >= 2;
            },
            onType: function(query) {
                // При вводе текста очищаем опции, если запрос меньше 2 символов
                if (!query || query.length < 2) {
                    this.clearOptions();
                    this.close();
                }
            },
            load(query, callback) {
                if (!query.length || query.length < 2) {
                    callback();
                    return;
                }
                
                fetch(`${API_CONFIG.API_URL}/hashtags?q=${encodeURIComponent(query)}`, {
                    credentials: 'include' // Важно для отправки cookies с токеном
                })
                    .then(res => {
                        if (!res.ok) throw new Error('Ошибка загрузки хэштегов');
                        return res.json();
                    })
                    .then(json => {
                        // Обрабатываем разные форматы ответа
                        const hashtags = Array.isArray(json) ? json : (json.hashtags || []);
                        callback(hashtags);
                    })
                    .catch(error => {
                        console.error('Ошибка загрузки хэштегов:', error);
                        callback();
                    });
            },
            onItemAdd() {
                // Очищаем поле ввода
                this.control_input.value = '';
                // Очищаем все опции, чтобы не показывать все хэштеги
                this.clearOptions();
                // Закрываем выпадающий список
                this.close();
                if (onItemAdd) onItemAdd(this);
            },
            onItemRemove() {
                // Очищаем опции при удалении элемента, чтобы не показывать старые хэштеги
                this.clearOptions();
                this.close();
                this.control_input.value = '';
                
                // При удалении элемента проверяем, остались ли элементы
                // Если элементов нет, убеждаемся, что плейсхолдер виден
                if (this.items.length === 0) {
                    // Удаляем класс has-items, чтобы показать плейсхолдер
                    this.wrapper.classList.remove('has-items');
                    // Убеждаемся, что input виден и плейсхолдер отображается
                    if (this.control_input) {
                        this.control_input.placeholder = this.settings.placeholder || 'Выберите хэштеги';
                    }
                }
            },
            onFocus() {
                // При фокусе не показываем выпадающий список автоматически
                // Пользователь должен ввести минимум 2 символа для поиска
                this.control_input.value = '';
                this.clearOptions();
            },
            onBlur() {
                // При потере фокуса закрываем выпадающий список
                this.close();
            },
        });
        
        return instance;
    } catch (error) {
        console.error('Ошибка инициализации TomSelect:', error);
        return null;
    }
}

/**
 * Загрузка карточек проблем с фильтрами
 */
export async function loadProblemsCards(filters, onSuccess = null, onError = null) {
    const container = document.querySelector('.cards-container');
    if (!container) return;
    
    container.innerHTML = 'Загрузка...';
    
    const params = new URLSearchParams();
    if (filters.search) params.append('search', filters.search);
    if (filters.hashtags && filters.hashtags.length) {
        params.append('hashtags', filters.hashtags.join(','));
    }
    if (filters.category != null && Number.isInteger(filters.category)) {
        params.append('category', filters.category);
    }
    if (filters.topic != null && Number.isInteger(filters.topic)) {
        params.append('topic', filters.topic);
    }
    if (filters.isNew) {
        params.append('isnew', 'true');
    }
    if (filters.limit) params.append('limit', filters.limit);
    if (filters.offset) params.append('offset', filters.offset);
    if (filters.sort && filters.sort !== 'default') params.append('sort', filters.sort);

    try {
        const response = await fetch(`${API_CONFIG.API_URL}/problems?${params.toString()}`, {
            credentials: 'include',
            cache: 'no-store'
        });
        
        // Перехватчик fetch должен автоматически обработать 401,
        // но проверяем статус на всякий случай
        if (response.status === 401) {
            // Пытаемся обновить токен через перехватчик
            // Если это не помогло, выводим ошибку
            throw new Error('Требуется авторизация');
        }
        
        if (!response.ok) {
            throw new Error(`Ошибка HTTP: ${response.status}`);
        }
        const contentType = response.headers.get('Content-Type') || '';
        let data;
        const text = await response.text();
        if (contentType.includes('application/json') && text) {
            try {
                data = JSON.parse(text);
            } catch (_) {
                throw new Error('Некорректный ответ сервера');
            }
        } else {
            throw new Error(response.ok ? 'Некорректный ответ сервера' : `Ошибка HTTP: ${response.status}`);
        }
        const list = (data && data.problems !== undefined) ? data.problems : (Array.isArray(data) ? data : []);
        // ИИ и оплата отключены: suggestAi не показываем
        const meta = data && typeof data === 'object' ? { suggestAi: false, aiPlanPriceRub: data.ai_plan_price_rub } : {};
        if (onSuccess) {
            onSuccess(list, meta);
        } else {
            renderProblemCards(list, meta);
        }
    } catch (error) {
        console.error('Ошибка загрузки проблем:', error);
        if (container) {
            container.innerHTML = `<p style="color:red; text-align:center">Ошибка загрузки данных: ${error.message}</p>`;
        }
        if (onError) onError(error);
    }
}

/**
 * Рендеринг карточек проблем (базовая версия)
 */
export function renderProblemCards(data, options = {}) {
    const container = document.querySelector('.cards-container');
    if (!container) return;
    const list = Array.isArray(data) ? data : [];
    container.innerHTML = '';

    if (list.length === 0 && options.suggestAi) {
        const suggestDiv = document.createElement('div');
        suggestDiv.className = 'suggest-ai-block';
        suggestDiv.innerHTML = `
            <p class="suggest-ai-text">По вашему запросу ничего не найдено. Создайте проблему с решениями с помощью ИИ — тариф 999 руб/мес.</p>
            <div class="suggest-ai-actions">
                <button type="button" class="suggest-ai-btn suggest-ai-btn-pay">Подключить за 999 руб</button>
                <button type="button" class="suggest-ai-btn suggest-ai-btn-create" disabled>Создать с ИИ</button>
            </div>
            <p class="suggest-ai-hint">После оплаты тарифа кнопка «Создать с ИИ» станет активной.</p>
        `;
        container.appendChild(suggestDiv);
        const payBtn = suggestDiv.querySelector('.suggest-ai-btn-pay');
        const createBtn = suggestDiv.querySelector('.suggest-ai-btn-create');
        if (payBtn) {
            payBtn.addEventListener('click', () => {
                if (typeof window.openPaymentModal === 'function') {
                    window.openPaymentModal(999);
                } else {
                    window.location.href = '/profile?tab=balance';
                }
            });
        }
            createBtn?.addEventListener('click', () => {
            const query = (document.getElementById('search') || document.querySelector('input[type="search"]'))?.value?.trim() || '';
            if (!query) return;
            suggestDiv.querySelector('.suggest-ai-actions')?.classList.add('loading');
            fetch(`${window.API_CONFIG?.API_URL || ''}/ai/create-problem-from-query`, {
                method: 'POST',
                credentials: 'include',
                headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + (localStorage.getItem('accessToken') || '') },
                body: JSON.stringify({ query })
            })
                .then(r => r.json())
                .then(res => {
                    if (res.status === 'success' && res.problem) {
                        window.location.href = '/problem/' + res.problem.ID;
                    } else {
                        alert(res.message || 'Ошибка создания');
                    }
                })
                .catch(() => alert('Ошибка сети'))
                .finally(() => suggestDiv.querySelector('.suggest-ai-actions')?.classList.remove('loading'));
        });
        function checkAiPlan() {
            const token = localStorage.getItem('accessToken');
            if (!token) return;
            fetch(`${window.API_CONFIG?.API_URL || ''}/payment/check_balance`, { credentials: 'include', headers: { 'Authorization': 'Bearer ' + token } })
                .then(r => r.json())
                .then(res => {
                    if (res.can_ai_plan && createBtn) {
                        createBtn.disabled = false;
                        const hint = suggestDiv.querySelector('.suggest-ai-hint');
                        if (hint) hint.textContent = 'Тариф ИИ подключён. Введите запрос в поиск и нажмите «Создать с ИИ».';
                    }
                })
                .catch(() => {});
        }
        checkAiPlan();
        return;
    }

    if (list.length === 0) {
        container.innerHTML = '<p style="text-align:center">Нет проблем для отображения</p>';
        return;
    }
    data = list;
    
    const template = document.getElementById('card-template');
    if (!template) {
        console.error('Шаблон карточки не найден!');
        return;
    }
    
    data.forEach(problem => {
        const clone = template.content.cloneNode(true);
        const card = clone.querySelector('.card');
        
        // Устанавливаем ID для админки
        if (options.isAdmin) {
            card.setAttribute('data-problem-id', problem.ID);
            card.style.cursor = 'pointer';
        }
        
        // Изображение: полный URL (Yandex Storage и т.д.) — как есть, иначе относительный путь приводим к рабочему
        const img = clone.querySelector('.card-image');
        if (img) {
            let imageSrc = (problem.Image || problem.image || '').replace(/\\/g, '/').trim();
            if (imageSrc && (imageSrc.startsWith('http://') || imageSrc.startsWith('https://'))) {
                img.src = imageSrc;
            } else if (!imageSrc) {
                img.src = '/assets/images/Screenshot_4-ww78noDj9-transformed.png';
            } else {
                if (imageSrc.startsWith('../images/')) imageSrc = '/images/' + imageSrc.slice(13);
                else if (imageSrc.startsWith('../assets/')) imageSrc = '/assets/' + imageSrc.slice(14);
                else if (imageSrc.startsWith('uploads/')) imageSrc = '/' + imageSrc;
                else if (!imageSrc.startsWith('/')) imageSrc = '/' + imageSrc.replace(/^\//, '');
                img.src = imageSrc;
            }
            img.alt = problem.Name || 'Проблема';
            img.loading = 'lazy';
            img.onerror = () => { img.src = '/assets/images/Screenshot_4-ww78noDj9-transformed.png'; };
        }
        
        // Название
        const titleText = clone.querySelector('.card-title-text');
        if (titleText) {
            titleText.textContent = problem.Name || 'Без названия';
            if (!options.isAdmin && titleText.tagName === 'A') {
                titleText.href = `/problem/${problem.ID}`;
            }
        }
        
        // Ссылка на детальную страницу (для обычной страницы)
        if (!options.isAdmin) {
            const cardTitleLink = clone.querySelector('.card-title-link');
            if (cardTitleLink) {
                cardTitleLink.href = `/problem/${problem.ID}`;
            }
        }
        
        // Избранное
        const favoriteCount = clone.querySelector('.favorite-count');
        if (favoriteCount) {
            favoriteCount.textContent = problem.FavouriteUsers ? problem.FavouriteUsers.length : (problem.Favourite || 0);
        }
        
        // Проверяем статус избранного и меняем иконку
        const favoriteIcon = clone.querySelector('.favorite-icon');
        if (favoriteIcon) {
            setFavoriteIconState(favoriteIcon, problem.IsFavourite);
        }
        
        // Тема проблемы
        const topicElement = clone.querySelector('.problem-topic');
        if (topicElement) {
            if (problem.TopicInfo && problem.TopicInfo.Name) {
                topicElement.innerHTML = '';
                const topicLink = document.createElement('a');
                topicLink.className = 'topic-link';
                topicLink.href = '#';
                topicLink.textContent = problem.TopicInfo.Name;
                topicLink.setAttribute('data-topic-id', problem.TopicInfo.ID);
                topicLink.style.cursor = 'pointer';
                topicElement.appendChild(topicLink);
                topicElement.style.display = 'block';
            } else {
                topicElement.style.display = 'none';
            }
        }
        
        // Хэштеги
        const tagsColumn = clone.querySelector('.tags-column');
        if (tagsColumn && problem.Hashtags) {
            tagsColumn.innerHTML = '';
            problem.Hashtags.forEach(hashtag => {
                const tagElement = document.createElement('span');
                tagElement.className = 'tag';
                tagElement.setAttribute('data-id', hashtag.ID);
                tagElement.textContent = hashtag.Name;
                tagsColumn.appendChild(tagElement);
            });
        }
        
        // Статистика
        const viewsStat = clone.querySelector('.views .stat-value');
        if (viewsStat) viewsStat.textContent = problem.Views || problem.Show || 0;
        
        const commentsStat = clone.querySelector('.comments .stat-value');
        if (commentsStat) {
            commentsStat.textContent = problem.Confirmations || (problem.Solutions?.length || 0);
        }
        
        const sharesStat = clone.querySelector('.shares .stat-value');
        if (sharesStat) sharesStat.textContent = problem.Shares || problem.Reply || 0;
        
        const linksStat = clone.querySelector('.links .stat-value');
        if (linksStat) {
            linksStat.textContent = problem.ProblemLinks ? problem.ProblemLinks.length : 0;
        }
        
        // Обработчик избранного (только для обычной страницы)
        if (!options.isAdmin) {
            const favoriteIcon = clone.querySelector('.favorite-icon');
            if (favoriteIcon) {
                favoriteIcon.addEventListener('click', (e) => {
                    e.stopPropagation();
                    toggleFavorite(problem.ID, favoriteIcon);
                });
            }
        }
        
        container.appendChild(clone);
    });
    
    // Инициализируем обработчики клика на тему (только для обычной страницы)
    if (!options.isAdmin) {
        container.querySelectorAll('.topic-link').forEach(topicLink => {
            topicLink.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                const topicId = topicLink.getAttribute('data-topic-id');
                if (topicId && options.onTopicClick) {
                    options.onTopicClick(parseInt(topicId, 10));
                }
            });
        });
    }
    
    // Инициализируем прокрутку тегов после рендеринга
    setTimeout(() => {
        initTagsScroll();
    }, 100);
}

/**
 * Переключение избранного
 */
export async function toggleFavorite(problemId, iconElement) {
    if (!iconElement || iconElement.dataset.pending === '1') {
        return;
    }
    iconElement.dataset.pending = '1';
    iconElement.style.pointerEvents = 'none';
    const wrapper = iconElement.closest('.card-favorites');
    if (wrapper) {
        wrapper.style.pointerEvents = 'none';
    }

    try {
        const token = localStorage.getItem('accessToken') || localStorage.getItem('token');
        const response = await fetch(API_CONFIG.buildURL(API_CONFIG.ENDPOINTS.PROBLEM_TOGGLE_FAVORITE(problemId)), {
            method: 'POST',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.status === 401) {
            // Пробуем обновить токен
            const refreshResponse = await fetch(API_CONFIG.buildURL(API_CONFIG.ENDPOINTS.REFRESH_TOKEN), {
                method: 'POST',
                credentials: 'include'
            });
            
            if (refreshResponse.ok) {
                // Повторяем запрос
                const retryResponse = await fetch(API_CONFIG.buildURL(API_CONFIG.ENDPOINTS.PROBLEM_TOGGLE_FAVORITE(problemId)), {
                    method: 'POST',
                    credentials: 'include',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                
                if (retryResponse.ok) {
                    const data = await retryResponse.json();
                    const countElement = iconElement.closest('.card-favorites')?.querySelector('.favorite-count');
                    if (countElement) {
                        // Обновляем счетчик (увеличиваем или уменьшаем на 1)
                        const currentCount = parseInt(countElement.textContent) || 0;
                        countElement.textContent = data.is_favourite ? currentCount + 1 : Math.max(0, currentCount - 1);
                    }
                    setFavoriteIconState(iconElement, data.is_favourite);
                }
            }
        } else if (response.ok) {
            const data = await response.json();
            const countElement = iconElement.closest('.card-favorites')?.querySelector('.favorite-count');
            if (countElement) {
                const currentCount = parseInt(countElement.textContent) || 0;
                countElement.textContent = data.is_favourite ? currentCount + 1 : Math.max(0, currentCount - 1);
            }
            // Переключаем иконку и фон избранного
            setFavoriteIconState(iconElement, data.is_favourite);
        }
    } catch (error) {
        console.error('Ошибка добавления в избранное:', error);
    } finally {
        iconElement.dataset.pending = '0';
        iconElement.style.pointerEvents = '';
        if (wrapper) {
            wrapper.style.pointerEvents = '';
        }
    }
}

/**
 * Инициализация обработчиков фильтров
 */
export function initFilterHandlers(filters, tomSelectInstance, onFilterChange) {
    const searchInput = document.getElementById('search');
    const categorySelect = document.getElementById('category');
    const hashtagsSelect = document.getElementById('hashtags');
    const sortSelect = document.getElementById('sort');
    
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            filters.search = e.target.value.trim();
            filters.offset = 0;
            if (onFilterChange) onFilterChange();
        });
    }
    
    if (categorySelect) {
        categorySelect.addEventListener('change', (e) => {
            const val = e.target.value;
            filters.category = val === '' ? null : parseInt(val, 10);
            filters.offset = 0;
            if (onFilterChange) onFilterChange();
        });
    }
    
    if (hashtagsSelect && tomSelectInstance) {
        hashtagsSelect.addEventListener('change', (e) => {
            filters.hashtags = tomSelectInstance.getValue().map(Number);
            filters.offset = 0;
            if (onFilterChange) onFilterChange();
        });
    }
    
    if (sortSelect) {
        sortSelect.addEventListener('change', (e) => {
            filters.sort = e.target.value;
            filters.offset = 0;
            if (onFilterChange) onFilterChange();
        });
    }
}

/**
 * Обработчик клика на теги (для фильтрации)
 */
export function initTagClickHandler(tomSelectInstance, filters, onFilterChange) {
    document.addEventListener('click', (event) => {
        if (event.target.classList.contains('tag')) {
            event.stopPropagation();
            event.preventDefault();
            const tagId = event.target.getAttribute('data-id');
            const tagName = event.target.textContent.trim();
            
            if (tagId && tomSelectInstance) {
                const tagIdNum = parseInt(tagId, 10);
                const currentValues = tomSelectInstance.getValue().map(v => parseInt(v, 10));
                
                // Проверяем, не добавлен ли уже этот хэштег
                if (!currentValues.includes(tagIdNum)) {
                    // Создаем объект опции для хэштега
                    const option = {
                        ID: tagIdNum,
                        Name: tagName
                    };
                    
                    // Добавляем опцию в TomSelect, если её еще нет
                    if (!tomSelectInstance.options[tagId]) {
                        tomSelectInstance.addOption(option);
                    }
                    
                    // Получаем текущие значения и добавляем новый хэштег
                    const currentValue = tomSelectInstance.getValue();
                    const newValue = [...currentValue, tagId];
                    
                    // Устанавливаем новое значение (silent = false, чтобы вызвать события)
                    tomSelectInstance.setValue(newValue, false);
                    
                    // Обновляем фильтры сразу после добавления
                    filters.hashtags = newValue.map(v => parseInt(v, 10));
                    filters.offset = 0;
                    
                    // Обновляем класс has-items для правильного отображения
                    const tsControl = document.querySelector('.vs-control');
                    if (tsControl && !tsControl.classList.contains('has-items')) {
                        tsControl.classList.add('has-items');
                    }
                    
                    // Очищаем поле ввода и опции после добавления
                    tomSelectInstance.control_input.value = '';
                    tomSelectInstance.clearOptions();
                    tomSelectInstance.close();
                    
                    // Вызываем callback для обновления карточек
                    if (onFilterChange) {
                        onFilterChange();
                    }
                }
            }
        }
    });
}

