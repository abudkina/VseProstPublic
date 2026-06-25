// problem.js
import * as auth from './authorizationFunctions.js';
import { initAuthHandlers } from './common.js';
import { updateCartIconState, addToCart, checkInCart } from './cartFunctions.js';
import { initTagsScroll, toggleFavorite } from './problemListCommon.js';
import { updateSEOMetaTags, addStructuredData, createProblemStructuredData } from './utils/seo.js';

// Инициализация обработчиков авторизации
initAuthHandlers();

let selectedProblemsList = [];
let currentProblem = null;
let selectedSolutionsList = [];

// Теперь используем градиентный фон вместо внешних изображений

function setFavoriteIconState(icon, isFavorite) {
    if (!icon) return;
    const isFavoriteFlag = isFavorite === true || isFavorite === 1 || isFavorite === '1';
    icon.classList.add('fa-heart');
    icon.classList.toggle('favorited', isFavoriteFlag);
    icon.classList.toggle('liked', isFavoriteFlag);
    icon.classList.toggle('fas', isFavoriteFlag);
    icon.classList.toggle('far', !isFavoriteFlag);
}

// Извлекаем ID из URL: поддержка /problem/123, /problem/123-slug и ?id=123
function getProblemIdFromURL() {
    // Сначала проверяем красивый URL: /problem/123 или /problem/123-slug
    const pathMatch = window.location.pathname.match(/\/problem\/(\d+)/);
    if (pathMatch) return pathMatch[1];

    // Фоллбэк на query параметры
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('problemId') || urlParams.get('id');
}

// Загружаем данные из JSON файлов
async function loadData() {
    const problemId = getProblemIdFromURL();
    if (!problemId) {
        throw new Error("Отсутствует параметр problemId в URL");
    }
    const response = await fetch(API_CONFIG.buildURL(API_CONFIG.ENDPOINTS.PROBLEM_BY_ID(problemId)));
    if (!response.ok) throw new Error('Ошибка HTTP: ' + response.status);
    const data = await response.json();
    return data.problem ?? data;
}

// Отображаем информацию о проблеме и её решениях
async function displaySolutions() {
    const problem = await loadData();
    currentProblem = problem; // Сохраняем текущую проблему для использования в модальном окне
    console.log("Получена задача:", problem);
    const solutionContainer = document.getElementById('solutionContainer');

    if (!problem) {
        solutionContainer.innerHTML = '<p>Проблема не найдена.</p>';
        return;
    }

    // Обновляем SEO мета-теги
    const baseUrl = window.location.origin;
    const problemUrl = `/problem/${problem.ID}`;
    const problemImage = problem.Image || 'assets/og-image.png';
    
    updateSEOMetaTags({
        title: `${problem.Name} - Всё Прост`,
        description: problem.Description || `Проблема: ${problem.Name}. Найдите решения на платформе Всё Прост (VseProst, ВсеПрост, Все Просто, ВсёПрост).`,
        image: problemImage,
        url: problemUrl,
        type: 'article'
    });

    // Добавляем структурированные данные
    addStructuredData(createProblemStructuredData(problem));

    // Очищаем контейнер
    solutionContainer.innerHTML = '';

    // --- Создаем блок с информацией о проблеме ---
    const problemInfoTemplate = document.getElementById('problem-info-template');
    const problemInfo = problemInfoTemplate.content.cloneNode(true);

    const img = problemInfo.querySelector('.problem-img');
    img.src = problem.Image || problem.image || 'assets/images/Screenshot_4-ww78noDj9-transformed.png';
    img.alt = problem.Name;
    
    // Добавляем обработчик клика для открытия модального окна
    img.addEventListener('click', () => {
        openImageViewer(img.src, img.alt);
    });

    const title = problemInfo.querySelector('.problem-title');
    title.textContent = problem.Name;

    // Заполняем статистику проблемы
    const statItems = problemInfo.querySelectorAll('.stat-item');
    statItems.forEach(statItem => {
        const statNumber = statItem.querySelector('.stat-number');
        if (statNumber) {
            const title = statItem.getAttribute('title');
            if (title === 'Лайки') {
                statNumber.textContent = problem.Favourite || 0;
                
                // Делаем иконку избранного кликабельной (только для авторизованных)
                const favoriteIcon = statItem.querySelector('.icon');
                if (favoriteIcon) {
                    setFavoriteIconState(favoriteIcon, problem.IsFavourite);

                    if (localStorage.getItem('isLoggedIn') !== 'true') return;
                    statItem.style.cursor = 'pointer';
                    statItem.addEventListener('click', async (e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        if (statItem.dataset.pending === '1') return;
                        statItem.dataset.pending = '1';
                        statItem.style.pointerEvents = 'none';
                        
                        // Вызываем toggleFavorite и обновляем счетчик
                        try {
                            const token = localStorage.getItem('accessToken') || localStorage.getItem('token');
                            const response = await fetch(API_CONFIG.buildURL(API_CONFIG.ENDPOINTS.PROBLEM_TOGGLE_FAVORITE(problem.ID)), {
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
                                    const retryResponse = await fetch(API_CONFIG.buildURL(API_CONFIG.ENDPOINTS.PROBLEM_TOGGLE_FAVORITE(problem.ID)), {
                                        method: 'POST',
                                        credentials: 'include',
                                        headers: {
                                            'Content-Type': 'application/json'
                                        }
                                    });
                                    
                                    if (retryResponse.ok) {
                                        const data = await retryResponse.json();
                                        // Обновляем счетчик
                                        const currentCount = parseInt(statNumber.textContent) || 0;
                                        statNumber.textContent = data.is_favourite ? currentCount + 1 : Math.max(0, currentCount - 1);
                                        // Обновляем иконку
                                        setFavoriteIconState(favoriteIcon, data.is_favourite);
                                    }
                                }
                            } else if (response.ok) {
                                const data = await response.json();
                                // Обновляем счетчик
                                const currentCount = parseInt(statNumber.textContent) || 0;
                                statNumber.textContent = data.is_favourite ? currentCount + 1 : Math.max(0, currentCount - 1);
                                // Обновляем иконку
                                setFavoriteIconState(favoriteIcon, data.is_favourite);
                            }
                        } catch (error) {
                            console.error('Ошибка добавления в избранное:', error);
                        } finally {
                            statItem.dataset.pending = '0';
                            statItem.style.pointerEvents = '';
                        }
                    });
                }
            } else if (title === 'Просмотры') {
                statNumber.textContent = problem.Show || 0;
            } else if (title === 'Ссылки') {
                // Количество прилинкованных проблем
                const linkedCount = problem.LinkedProblemsCount !== undefined
                    ? problem.LinkedProblemsCount
                    : (problem.LinkedProblems ? problem.LinkedProblems.length : 0);
                statNumber.textContent = linkedCount;

                // Делаем иконку кликабельной только для авторизованных
                if (localStorage.getItem('isLoggedIn') === 'true') {
                    statItem.style.cursor = 'pointer';
                    statItem.addEventListener('click', () => {
                        openLinkedProblemModal();
                    });
                }
            }
        }
    });

    // Добавляем описание проблемы, если есть
    if (problem.Describe) {
        const description = problemInfo.querySelector('.problem-description');
        if (description) {
            description.textContent = problem.Describe;
        }
    }

    // Добавляем информацию о проблеме в контейнер
    solutionContainer.appendChild(problemInfo);

    // --- Добавляем теги и кнопку добавления решения ---
    const tagsAndButtonContainer = document.createElement('div');
    tagsAndButtonContainer.className = 'tags-and-button-container';
    
    const tagsContainer = document.createElement('div');
    tagsContainer.className = 'tags';
    
    if (problem.Hashtags && problem.Hashtags.length > 0) {
        const tagTemplate = document.getElementById('tag-template');
        problem.Hashtags.forEach(tag => {
            const tagNode = tagTemplate.content.cloneNode(true);
            tagNode.querySelector('.tag').textContent = `#${tag.Name || tag.text || 'хэштег'}`;
            tagsContainer.appendChild(tagNode);
        });
    }
    
    tagsAndButtonContainer.appendChild(tagsContainer);
    
    // Добавляем кнопку добавления решения (только для авторизованных)
    const isLoggedIn = localStorage.getItem('isLoggedIn') === 'true';
    if (isLoggedIn) {
        const addSolutionBtnContainer = document.createElement('div');
        addSolutionBtnContainer.className = 'add-solution-button-container';
        const addSolutionBtn = document.createElement('button');
        addSolutionBtn.id = 'addSolutionBtn';
        addSolutionBtn.className = 'add-solution-btn';
        addSolutionBtn.innerHTML = `
            <i class="fas fa-plus-circle btn-icon" aria-hidden="true"></i>
            <span>Добавить решение</span>
        `;
        addSolutionBtnContainer.appendChild(addSolutionBtn);
        tagsAndButtonContainer.appendChild(addSolutionBtnContainer);
    }
    
    solutionContainer.appendChild(tagsAndButtonContainer);

    // --- Создаем вкладки для переключения между решениями и похожими проблемами ---
    const tabsContainer = document.createElement('div');
    tabsContainer.className = 'tabs-container';
    
    const tabsWrapper = document.createElement('div');
    tabsWrapper.className = 'tabs-wrapper';
    
    const solutionsTab = document.createElement('button');
    solutionsTab.className = 'tab-button active';
    solutionsTab.id = 'solutions-tab';
    solutionsTab.textContent = 'Решения';
    
    const similarProblemsTab = document.createElement('button');
    similarProblemsTab.className = 'tab-button';
    similarProblemsTab.id = 'similar-problems-tab';
    similarProblemsTab.textContent = 'Похожие проблемы';
    
    tabsWrapper.appendChild(solutionsTab);
    tabsWrapper.appendChild(similarProblemsTab);
    tabsContainer.appendChild(tabsWrapper);
    
    // --- Создаем контейнер для сортировки (только для решений) ---
    const sortContainer = document.createElement('div');
    sortContainer.className = 'sort-container';
    sortContainer.id = 'sort-container';
    
    const sortLabel = document.createElement('label');
    sortLabel.textContent = 'Сортировать по:';
    sortLabel.className = 'sort-label';
    
    const sortSelect = document.createElement('select');
    sortSelect.id = 'sort-select';
    sortSelect.className = 'sort-select';
    sortSelect.innerHTML = `
        <option value="created_date_desc">Дата создания (новые)</option>
        <option value="created_date_asc">Дата создания (старые)</option>
        <option value="modified_date_desc">Дата изменения (новые)</option>
        <option value="modified_date_asc">Дата изменения (старые)</option>
        <option value="price_desc">Цена (убывание)</option>
        <option value="price_asc">Цена (возрастание)</option>
        <option value="efficiency_desc">Эффективность (убывание)</option>
        <option value="efficiency_asc">Эффективность (возрастание)</option>
        <option value="complexity_desc">Сложность (убывание)</option>
        <option value="complexity_asc">Сложность (возрастание)</option>
        <option value="time_desc">Время (убывание)</option>
        <option value="time_asc">Время (возрастание)</option>
        <option value="rating_desc">Рейтинг (убывание)</option>
        <option value="rating_asc">Рейтинг (возрастание)</option>
    `;
    
    sortContainer.appendChild(sortLabel);
    sortContainer.appendChild(sortSelect);
    
    tabsContainer.appendChild(sortContainer);
    solutionContainer.appendChild(tabsContainer);

    // --- Создаем контейнер для карточек решений ---
    let cardsWrapper = document.createElement('div');
    cardsWrapper.id = 'solutions-cards-wrapper';
    cardsWrapper.className = 'cards-container';
    solutionContainer.appendChild(cardsWrapper);
    
    // --- Создаем контейнер для похожих проблем ---
    let similarProblemsWrapper = document.createElement('div');
    similarProblemsWrapper.id = 'similar-problems-wrapper';
    similarProblemsWrapper.className = 'cards-container';
    similarProblemsWrapper.style.display = 'none';
    solutionContainer.appendChild(similarProblemsWrapper);

    // Сохраняем решения для сортировки
    let currentSolutions = problem.Solutions || [];
    
    // Функция сортировки решений
    function sortSolutions(solutions, sortType) {
        const sorted = [...solutions];
        const [field, direction] = sortType.split('_');
        const isDesc = direction === 'desc';
        
        sorted.sort((a, b) => {
            let aVal, bVal;
            
            switch(field) {
                case 'created':
                    aVal = a.CreatedDate ? new Date(a.CreatedDate) : new Date(0);
                    bVal = b.CreatedDate ? new Date(b.CreatedDate) : new Date(0);
                    break;
                case 'modified':
                    aVal = a.ModifiedDate ? new Date(a.ModifiedDate) : new Date(0);
                    bVal = b.ModifiedDate ? new Date(b.ModifiedDate) : new Date(0);
                    break;
                case 'price':
                    aVal = a.Price || 0;
                    bVal = b.Price || 0;
                    break;
                case 'efficiency':
                    aVal = a.Efficiency || 0;
                    bVal = b.Efficiency || 0;
                    break;
                case 'complexity':
                    aVal = a.Complexity || 0;
                    bVal = b.Complexity || 0;
                    break;
                case 'time':
                    aVal = a.Time || 0;
                    bVal = b.Time || 0;
                    break;
                case 'rating':
                    aVal = a.Rating || 0;
                    bVal = b.Rating || 0;
                    break;
                default:
                    return 0;
            }
            
            if (aVal < bVal) return isDesc ? 1 : -1;
            if (aVal > bVal) return isDesc ? -1 : 1;
            return 0;
        });
        
        return sorted;
    }
    
    // Функция отображения решений
    function renderSolutions(solutions) {
        cardsWrapper.innerHTML = '';
        
        if (!solutions || solutions.length === 0) {
            cardsWrapper.innerHTML = '<p class="no-solutions">Решений для этой проблемы пока нет.</p>';
            return;
        }
        
        const cardTemplate = document.getElementById('solution-card-template');
        
        solutions.forEach(solution => {
            const card = cardTemplate.content.cloneNode(true);

            const link = card.querySelector('.card-title-link');
            if (link) {
                link.href = (window.PATHS ? window.PATHS.solution(solution.ID) : `/solution/${solution.ID}`);
            }

            const cardImg = card.querySelector('.card-image');
            const cardImageWrapper = card.querySelector('.card-image-wrapper');
            if (cardImg) cardImg.loading = 'lazy';

            if (cardImg) {
                // Функция для генерации SVG изображения с градиентом и названием
                function getImageFromInternet(solutionName) {
                    if (!solutionName || solutionName.trim() === '') {
                        return null;
                    }
                    
                    // Создаем хеш от названия для получения стабильного изображения
                    let hash = 0;
                    for (let i = 0; i < solutionName.length; i++) {
                        const char = solutionName.charCodeAt(i);
                        hash = ((hash << 5) - hash) + char;
                        hash = hash & hash;
                    }
                    
                    const imageId = Math.abs(hash) % 1000;
                    
                    // Цвета для градиента на основе хеша
                    const colors = [
                        ['#667eea', '#764ba2'], ['#f093fb', '#f5576c'], ['#4facfe', '#00f2fe'],
                        ['#43e97b', '#38f9d7'], ['#fa709a', '#fee140'], ['#30cfd0', '#330867'],
                        ['#a8edea', '#fed6e3'], ['#d299c2', '#fef9d7'], ['#ff9a9e', '#fecfef'],
                        ['#ffecd2', '#fcb69f'],
                    ];
                    
                    const colorPair = colors[imageId % colors.length];
                    const displayText = solutionName.trim().replace(/[<>]/g, '').substring(0, 30);
                    
                    const svg = `
                        <svg xmlns="http://www.w3.org/2000/svg" width="400" height="300" viewBox="0 0 400 300">
                            <defs>
                                <linearGradient id="grad${imageId}" x1="0%" y1="0%" x2="100%" y2="100%">
                                    <stop offset="0%" style="stop-color:${colorPair[0]};stop-opacity:1" />
                                    <stop offset="100%" style="stop-color:${colorPair[1]};stop-opacity:1" />
                                </linearGradient>
                            </defs>
                            <rect width="400" height="300" fill="url(#grad${imageId})"/>
                            <text x="50%" y="50%" text-anchor="middle" fill="white" font-family="Arial, sans-serif" 
                                  font-size="24" font-weight="bold" dy=".3em">
                                ${displayText}
                            </text>
                        </svg>
                    `;
                    
                    return 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg);
                }
                
                let imageSrc = solution.Image;
                
                // Внешний URL (Yandex Storage и т.д.) — используем как есть
                if (imageSrc && (imageSrc.startsWith('http://') || imageSrc.startsWith('https://'))) {
                    cardImg.src = imageSrc;
                    cardImg.alt = solution.Name || 'Решение';
                    cardImg.style.display = 'block';
                    if (cardImageWrapper) cardImageWrapper.style.background = 'none';
                    cardImg.onerror = function() {
                        const internetImage = getImageFromInternet(solution.Name);
                        if (internetImage) {
                            this.src = internetImage;
                        } else {
                            this.style.display = 'none';
                            if (cardImageWrapper) cardImageWrapper.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
                        }
                    };
                } else if (!imageSrc || imageSrc.trim() === '' || imageSrc === '../images/default.png') {
                    const internetImage = getImageFromInternet(solution.Name);
                    if (internetImage) {
                        cardImg.src = internetImage;
                        cardImg.style.display = 'block';
                        if (cardImageWrapper) cardImageWrapper.style.background = 'none';
                        cardImg.onerror = function() {
                            this.style.display = 'none';
                            if (cardImageWrapper) cardImageWrapper.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
                        };
                    } else {
                        cardImg.style.display = 'none';
                        if (cardImageWrapper) cardImageWrapper.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
                    }
                } else {
                    // Локальный/относительный путь
                    if (!imageSrc.startsWith('/')) {
                        if (imageSrc.startsWith('../images/')) {
                            imageSrc = imageSrc.replace('../images/', '/images/');
                        } else if (imageSrc.startsWith('../assets/')) {
                            imageSrc = imageSrc.replace('../assets/', 'assets/');
                        } else {
                            imageSrc = '/images/' + imageSrc;
                        }
                    }
                    cardImg.src = imageSrc;
                    cardImg.alt = solution.Name || 'Решение';
                    cardImg.style.display = 'block';
                    if (cardImageWrapper) cardImageWrapper.style.background = 'none';
                    cardImg.onerror = function() {
                        const internetImage = getImageFromInternet(solution.Name);
                        if (internetImage) {
                            this.src = internetImage;
                            this.style.display = 'block';
                            if (cardImageWrapper) {
                                cardImageWrapper.style.background = 'none';
                            }
                        } else {
                            this.style.display = 'none';
                            if (cardImageWrapper) {
                                cardImageWrapper.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
                            }
                        }
                    };
                }
            }

            // Заполняем данные карточки
            const favoriteCount = card.querySelector('.favorite-count');
            if (favoriteCount) favoriteCount.textContent = solution.Favourite || 0;

            const favoriteIcon = card.querySelector('.favorite-icon');
            if (favoriteIcon) {
                setFavoriteIconState(favoriteIcon, solution.IsFavourite);
                if (localStorage.getItem('isLoggedIn') === 'true') {
                    favoriteIcon.style.cursor = 'pointer';
                    favoriteIcon.addEventListener('click', async (e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        await toggleSolutionFavorite(solution.ID, favoriteIcon, favoriteCount);
                    });
                }
            }

            const ratingNumber = card.querySelector('.rating-number');
            if (ratingNumber) ratingNumber.textContent = solution.Rating || 0;

            const cardTitleText = card.querySelector('.card-title-text');
            if (cardTitleText) {
                cardTitleText.href = (window.PATHS ? window.PATHS.solution(solution.ID) : `/solution/${solution.ID}`);
                cardTitleText.textContent = solution.Name || 'Решение';
            }

            // Отображаем темы из связанных проблем
            const topicElement = card.querySelector('.problem-topic');
            if (topicElement) {
                topicElement.innerHTML = '';
                // Собираем уникальные темы из всех связанных проблем
                const topicsMap = new Map();
                // Решение связано с текущей проблемой, используем её тему
                if (problem && problem.TopicInfo && problem.TopicInfo.Name) {
                    const topicId = problem.TopicInfo.ID;
                    if (!topicsMap.has(topicId)) {
                        topicsMap.set(topicId, problem.TopicInfo);
                    }
                }
                // Также проверяем, есть ли информация о проблемах в самом решении
                if (solution.Problems && Array.isArray(solution.Problems)) {
                    solution.Problems.forEach(prob => {
                        if (prob.TopicInfo && prob.TopicInfo.Name) {
                            const topicId = prob.TopicInfo.ID;
                            if (!topicsMap.has(topicId)) {
                                topicsMap.set(topicId, prob.TopicInfo);
                            }
                        }
                    });
                }
                
                // Отображаем темы (берем первую, как в карточках проблем)
                if (topicsMap.size > 0) {
                    const firstTopic = Array.from(topicsMap.values())[0];
                    const topicLink = document.createElement('a');
                    topicLink.className = 'topic-link';
                    topicLink.href = '/';
                    topicLink.textContent = firstTopic.Name;
                    topicLink.setAttribute('data-topic-id', firstTopic.ID);
                    topicLink.style.cursor = 'pointer';
                    topicLink.addEventListener('click', (e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        window.location.href = `/?topic=${firstTopic.ID}`;
                    });
                    topicElement.appendChild(topicLink);
                    topicElement.style.display = 'block';
                } else {
                    topicElement.style.display = 'none';
                }
            }

            // Теги (хэштеги из связанных проблем)
            const tagsColumn = card.querySelector('.tags-column');
            if (tagsColumn) {
                tagsColumn.innerHTML = '';
                if (solution.Problems && Array.isArray(solution.Problems)) {
                    solution.Problems.forEach(problem => {
                        if (problem.Hashtags && Array.isArray(problem.Hashtags)) {
                            problem.Hashtags.forEach(tag => {
                                const tagElement = document.createElement('span');
                                tagElement.className = 'tag';
                                tagElement.setAttribute('data-id', tag.ID);
                                tagElement.textContent = tag.Name;
                                tagElement.style.cursor = 'pointer';
                                // Обработчик клика по тегу - переход на главную страницу с фильтром
                                tagElement.addEventListener('click', (e) => {
                                    e.stopPropagation();
                                    e.preventDefault();
                                    window.location.href = `/?hashtags=${tag.ID}`;
                                });
                                tagsColumn.appendChild(tagElement);
                            });
                        }
                    });
                }
            }

            // Статистика
            const statViewsValue = card.querySelector('.stat-item.views .stat-value');
            if (statViewsValue) statViewsValue.textContent = solution.Show || 0;

            const commentsCount = Array.isArray(solution.Comments) ? solution.Comments.length : (solution.CommentSolutions?.length || 0);
            const statCommentsValue = card.querySelector('.stat-item.comments .stat-value');
            if (statCommentsValue) statCommentsValue.textContent = commentsCount;

            // Ссылки (Reply)
            const statSharesValue = card.querySelector('.stat-item.shares .stat-value');
            if (statSharesValue) statSharesValue.textContent = solution.Reply || 0;
            
            // Линки (связанные решения)
            const linksValue = solution.LinkedSolutionsCount || solution.LinkedSolutions?.length || 0;
            const statLinksValue = card.querySelector('.stat-item.links .stat-value');
            if (statLinksValue) statLinksValue.textContent = linksValue;

            // Кнопка добавления в корзину
            const cartBtn = card.querySelector('.card-cart-btn');
            if (cartBtn) {
                const cartIcon = cartBtn.querySelector('i');
                
                cartBtn.addEventListener('click', async (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    await handleAddToCart(solution.ID, cartBtn, cartIcon);
                });
                
                // Проверяем, есть ли уже в корзине
                checkInCart(solution.ID).then(inCart => {
                    if (inCart) {
                        cartBtn.classList.add('in-cart');
                        cartBtn.title = 'Уже в корзине';
                        if (cartIcon) {
                            cartIcon.classList.add('cart-in-cart');
                        }
                    } else {
                        if (cartIcon) {
                            cartIcon.classList.remove('cart-in-cart');
                        }
                    }
                });
            }

            cardsWrapper.appendChild(card);
        });
    }
    
    // Переключение избранного для решений
    async function toggleSolutionFavorite(solutionId, iconElement, countElement) {
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
            const response = await fetch(API_CONFIG.buildURL(API_CONFIG.ENDPOINTS.SOLUTION_TOGGLE_FAVORITE(solutionId)), {
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
                    const retryResponse = await fetch(API_CONFIG.buildURL(API_CONFIG.ENDPOINTS.SOLUTION_TOGGLE_FAVORITE(solutionId)), {
                        method: 'POST',
                        credentials: 'include',
                        headers: {
                            'Content-Type': 'application/json'
                        }
                    });
                    
                    if (retryResponse.ok) {
                        const data = await retryResponse.json();
                        if (countElement) {
                            const currentCount = parseInt(countElement.textContent) || 0;
                            countElement.textContent = data.is_favourite ? currentCount + 1 : Math.max(0, currentCount - 1);
                        }
                        setFavoriteIconState(iconElement, data.is_favourite);
                    }
                }
            } else if (response.ok) {
                const data = await response.json();
                if (countElement) {
                    const currentCount = parseInt(countElement.textContent) || 0;
                    countElement.textContent = data.is_favourite ? currentCount + 1 : Math.max(0, currentCount - 1);
                }
                setFavoriteIconState(iconElement, data.is_favourite);
            }
        } catch (error) {
            console.error('Ошибка добавления решения в избранное:', error);
        } finally {
            iconElement.dataset.pending = '0';
            iconElement.style.pointerEvents = '';
            if (wrapper) {
                wrapper.style.pointerEvents = '';
            }
        }
    }
    
    // Обработчик добавления в корзину
    async function handleAddToCart(solutionId, button, icon) {
        const result = await addToCart(solutionId);
        
        if (result.success) {
            button.classList.add('in-cart');
            button.title = 'Уже в корзине';
            if (icon) {
                icon.classList.add('cart-in-cart');
            }
            alert(result.message || 'Решение добавлено в корзину');
        } else {
            alert(result.error || 'Не удалось добавить в корзину');
        }
    }
    
    // Функция отображения похожих проблем
    function renderSimilarProblems(problems) {
        similarProblemsWrapper.innerHTML = '';
        
        if (!problems || problems.length === 0) {
            similarProblemsWrapper.innerHTML = '<p class="no-solutions">Похожих проблем пока нет.</p>';
            return;
        }
        
        // Создаем карточки для похожих проблем, используя структуру, аналогичную главной странице
        problems.forEach(linkedProblem => {
            const problemCard = document.createElement('article');
            problemCard.className = 'card';
            
            // Обертка для изображения
            const imageWrapper = document.createElement('div');
            imageWrapper.className = 'card-image-wrapper';
            
            // Ссылка на изображение
            const imageLink = document.createElement('a');
            imageLink.href = `/problem/${linkedProblem.ID}`;
            imageLink.className = 'card-title-link';
            
            const img = document.createElement('img');
            let imageSrc = linkedProblem.Image || '../images/default.png';
            // Исправляем пути к изображениям
            if (imageSrc && !imageSrc.startsWith('http') && !imageSrc.startsWith('/')) {
                if (imageSrc.startsWith('../images/')) {
                    imageSrc = imageSrc.replace('../images/', '/images/');
                } else if (imageSrc.startsWith('../assets/')) {
                    imageSrc = imageSrc.replace('../assets/', 'assets/');
                } else if (!imageSrc.startsWith('/')) {
                    imageSrc = '/images/' + imageSrc;
                }
            }
            img.src = imageSrc;
            img.alt = linkedProblem.Name || 'Проблема';
            img.className = 'card-image';
            img.loading = 'lazy';
            
            imageLink.appendChild(img);
            imageWrapper.appendChild(imageLink);
            
            // Overlay для названия
            const titleOverlay = document.createElement('div');
            titleOverlay.className = 'card-title-overlay';
            imageWrapper.appendChild(titleOverlay);
            
            // Название проблемы (ссылка)
            const titleLink = document.createElement('a');
            titleLink.href = `/problem/${linkedProblem.ID}`;
            titleLink.className = 'card-title-text';
            titleLink.textContent = linkedProblem.Name || 'Без названия';
            imageWrapper.appendChild(titleLink);
            
            // Избранное
            const favoritesDiv = document.createElement('div');
            favoritesDiv.className = 'card-favorites';
            const favoriteIcon = document.createElement('i');
            favoriteIcon.className = 'favorite-icon fa-heart';
            favoriteIcon.setAttribute('aria-label', 'Избранное');
            setFavoriteIconState(favoriteIcon, linkedProblem.IsFavourite);
            if (linkedProblem.IsFavourite === true) {
                favoritesDiv.classList.add('favorited');
            } else {
                favoritesDiv.classList.remove('favorited');
            }
            const favoriteCount = document.createElement('span');
            favoriteCount.className = 'favorite-count';
            favoriteCount.textContent = linkedProblem.FavouriteUsers ? linkedProblem.FavouriteUsers.length : (linkedProblem.Favourite || 0);
            favoritesDiv.appendChild(favoriteIcon);
            favoritesDiv.appendChild(favoriteCount);
            imageWrapper.appendChild(favoritesDiv);
            
            problemCard.appendChild(imageWrapper);
            
            // Контент карточки
            const cardContent = document.createElement('div');
            cardContent.className = 'card-content';
            
            // Тема проблемы
            const topicElement = document.createElement('div');
            topicElement.className = 'problem-topic';
            if (linkedProblem.TopicInfo && linkedProblem.TopicInfo.Name) {
                const topicLink = document.createElement('a');
                topicLink.className = 'topic-link';
                topicLink.href = '#';
                topicLink.textContent = linkedProblem.TopicInfo.Name;
                topicLink.setAttribute('data-topic-id', linkedProblem.TopicInfo.ID);
                topicLink.style.cursor = 'pointer';
                topicLink.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    window.location.href = `/?topic=${linkedProblem.TopicInfo.ID}`;
                });
                topicElement.appendChild(topicLink);
                topicElement.style.display = 'block';
            } else {
                topicElement.style.display = 'none';
            }
            cardContent.appendChild(topicElement);
            
            // Теги/хэштеги (аналогично главной странице)
            const tagsColumn = document.createElement('div');
            tagsColumn.className = 'tags-column';
            if (linkedProblem.Hashtags && Array.isArray(linkedProblem.Hashtags) && linkedProblem.Hashtags.length > 0) {
                linkedProblem.Hashtags.forEach(hashtag => {
                    const tagElement = document.createElement('span');
                    tagElement.className = 'tag';
                    tagElement.setAttribute('data-id', hashtag.ID);
                    tagElement.textContent = hashtag.Name;
                    tagElement.style.cursor = 'pointer';
                    // Обработчик клика по тегу - переход на главную страницу с фильтром
                    tagElement.addEventListener('click', (e) => {
                        e.stopPropagation();
                        e.preventDefault();
                        window.location.href = `/?hashtags=${hashtag.ID}`;
                    });
                    tagsColumn.appendChild(tagElement);
                });
            }
            cardContent.appendChild(tagsColumn);
            
            // Футер со статистикой
            const cardFooter = document.createElement('div');
            cardFooter.className = 'card-footer';
            
            // Просмотры
            const viewsStat = document.createElement('div');
            viewsStat.className = 'stat-item views';
            const viewsIcon = document.createElement('div');
            viewsIcon.className = 'stat-icon';
            viewsIcon.title = 'Просмотры';
            const viewsIconEl = document.createElement('i');
            viewsIconEl.className = 'fas fa-eye';
            viewsIcon.appendChild(viewsIconEl);
            const viewsValue = document.createElement('div');
            viewsValue.className = 'stat-value';
            viewsValue.textContent = linkedProblem.Views || linkedProblem.Show || 0;
            viewsStat.appendChild(viewsIcon);
            viewsStat.appendChild(viewsValue);
            cardFooter.appendChild(viewsStat);
            
            // Комментарии/Подтверждения
            const commentsStat = document.createElement('div');
            commentsStat.className = 'stat-item comments';
            const commentsIcon = document.createElement('div');
            commentsIcon.className = 'stat-icon';
            commentsIcon.title = 'Подтверждения';
            const commentsIconEl = document.createElement('i');
            commentsIconEl.className = 'fas fa-check';
            commentsIcon.appendChild(commentsIconEl);
            const commentsValue = document.createElement('div');
            commentsValue.className = 'stat-value';
            commentsValue.textContent = linkedProblem.Confirmations || (linkedProblem.Solutions?.length || 0);
            commentsStat.appendChild(commentsIcon);
            commentsStat.appendChild(commentsValue);
            cardFooter.appendChild(commentsStat);
            
            // Ссылки
            const sharesStat = document.createElement('div');
            sharesStat.className = 'stat-item shares';
            const sharesIcon = document.createElement('div');
            sharesIcon.className = 'stat-icon';
            sharesIcon.title = 'Ссылки';
            const sharesIconEl = document.createElement('i');
            sharesIconEl.className = 'fas fa-share';
            sharesIcon.appendChild(sharesIconEl);
            const sharesValue = document.createElement('div');
            sharesValue.className = 'stat-value';
            sharesValue.textContent = linkedProblem.Shares || linkedProblem.Reply || 0;
            sharesStat.appendChild(sharesIcon);
            sharesStat.appendChild(sharesValue);
            cardFooter.appendChild(sharesStat);
            
            // Связанные проблемы
            const linksStat = document.createElement('div');
            linksStat.className = 'stat-item links';
            const linksIcon = document.createElement('div');
            linksIcon.className = 'stat-icon';
            linksIcon.title = 'Ссылки';
            const linksIconEl = document.createElement('i');
            linksIconEl.className = 'fas fa-link';
            linksIcon.appendChild(linksIconEl);
            const linksValue = document.createElement('div');
            linksValue.className = 'stat-value';
            linksValue.textContent = linkedProblem.ProblemLinks ? linkedProblem.ProblemLinks.length : 0;
            linksStat.appendChild(linksIcon);
            linksStat.appendChild(linksValue);
            cardFooter.appendChild(linksStat);
            
            cardContent.appendChild(cardFooter);
            problemCard.appendChild(cardContent);
            
            // Обработчик избранного
            favoriteIcon.addEventListener('click', (e) => {
                e.stopPropagation();
                e.preventDefault();
                toggleFavorite(linkedProblem.ID, favoriteIcon);
            });
            
            similarProblemsWrapper.appendChild(problemCard);
        });
        
        // Инициализируем прокрутку тегов после рендеринга
        setTimeout(() => {
            initTagsScroll();
        }, 100);
    }
    
    // Обработчик сортировки
    sortSelect.addEventListener('change', (e) => {
        const sorted = sortSolutions(currentSolutions, e.target.value);
        renderSolutions(sorted);
    });
    
    // Обработчики переключения вкладок
    solutionsTab.addEventListener('click', () => {
        solutionsTab.classList.add('active');
        similarProblemsTab.classList.remove('active');
        cardsWrapper.style.display = '';
        similarProblemsWrapper.style.display = 'none';
        sortContainer.style.display = 'flex';
    });
    
    similarProblemsTab.addEventListener('click', () => {
        similarProblemsTab.classList.add('active');
        solutionsTab.classList.remove('active');
        cardsWrapper.style.display = 'none';
        similarProblemsWrapper.style.display = '';
        sortContainer.style.display = 'none';
    });

    // --- Отображаем карточки решений ---
    renderSolutions(currentSolutions);
    
    // --- Отображаем похожие проблемы ---
    renderSimilarProblems(problem.LinkedProblems || []);
}

displaySolutions().finally(function () {
    if (typeof window.__showProblemPage === 'function') window.__showProblemPage();
});

// Переменные для модального окна похожих проблем
let selectedLinkedProblemsList = [];
let linkedProblemSearchTimeout = null;

// Функции для работы с модальным окном похожих проблем
function openLinkedProblemModal() {
    try {
        // Проверяем авторизацию
        auth.checkAuth(true).then(() => {
            const modalOverlay = document.getElementById('linked-problem-modal-overlay');
            if (modalOverlay) {
                modalOverlay.classList.add('active');
                document.body.style.overflow = 'hidden';
                selectedLinkedProblemsList = [];
                updateSelectedLinkedProblems();
            }
        }).catch(error => {
            console.error('Ошибка авторизации:', error);
            alert('Для добавления похожих проблем необходимо авторизоваться');
        });
    } catch (error) {
        console.error('Ошибка открытия модального окна:', error);
    }
}

function closeLinkedProblemModal() {
    const modalOverlay = document.getElementById('linked-problem-modal-overlay');
    if (modalOverlay) {
        modalOverlay.classList.remove('active');
        document.body.style.overflow = '';
        const searchInput = document.getElementById('linkedProblemSearch');
        if (searchInput) searchInput.value = '';
        const dropdown = document.getElementById('linkedProblemDropdown');
        if (dropdown) dropdown.style.display = 'none';
        selectedLinkedProblemsList = [];
        updateSelectedLinkedProblems();
    }
}

function updateSelectedLinkedProblems() {
    const container = document.getElementById('selectedLinkedProblems');
    if (!container) return;
    
    container.innerHTML = '';
    selectedLinkedProblemsList.forEach(problem => {
        const div = document.createElement('div');
        div.className = 'selected-problem';
        div.innerHTML = `${problem.title} <span class="remove" data-id="${problem.id}">×</span>`;
        container.appendChild(div);
    });
    
    // Добавляем обработчики удаления
    container.querySelectorAll('.remove').forEach(removeBtn => {
        removeBtn.addEventListener('click', (e) => {
            const id = parseInt(e.target.dataset.id);
            selectedLinkedProblemsList = selectedLinkedProblemsList.filter(p => p.id !== id);
            updateSelectedLinkedProblems();
        });
    });
}

async function searchLinkedProblems(query) {
    if (!query || query.length < 2) {
        const dropdown = document.getElementById('linkedProblemDropdown');
        if (dropdown) dropdown.style.display = 'none';
        return;
    }
    
    try {
        const token = localStorage.getItem('accessToken');
        const currentProblemId = currentProblem ? currentProblem.ID : null;
        
        // Исключаем текущую проблему из поиска
        let url = `/api/problems?search=${encodeURIComponent(query)}&limit=10`;
        if (currentProblemId) {
            url += `&exclude=${currentProblemId}`;
        }
        
        const response = await fetch(url, {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            const problems = await response.json();
            const dropdown = document.getElementById('linkedProblemDropdown');
            if (!dropdown) return;
            
            dropdown.innerHTML = '';
            
            // Фильтруем проблемы: исключаем текущую и уже выбранные
            const filteredProblems = problems.filter(problem => {
                if (currentProblemId && problem.ID === currentProblemId) return false;
                if (selectedLinkedProblemsList.some(p => p.id === problem.ID)) return false;
                return true;
            });
            
            if (filteredProblems.length === 0) {
                dropdown.innerHTML = '<div class="dropdown-item">Проблемы не найдены</div>';
            } else {
                filteredProblems.forEach(problem => {
                    const div = document.createElement('div');
                    div.className = 'dropdown-item';
                    div.textContent = problem.Name || 'Без названия';
                    div.setAttribute('data-id', problem.ID);
                    
                    div.addEventListener('click', () => {
                        // Проверяем, не выбрана ли уже эта проблема
                        if (!selectedLinkedProblemsList.some(p => p.id === problem.ID)) {
                            selectedLinkedProblemsList.push({
                                id: problem.ID,
                                title: problem.Name || 'Без названия'
                            });
                            updateSelectedLinkedProblems();
                        }
                        const searchInput = document.getElementById('linkedProblemSearch');
                        if (searchInput) searchInput.value = '';
                        dropdown.style.display = 'none';
                    });
                    
                    dropdown.appendChild(div);
                });
            }
            
            dropdown.style.display = 'block';
        } else {
            console.error('Ошибка поиска проблем:', response.status);
        }
    } catch (error) {
        console.error('Ошибка поиска проблем:', error);
    }
}

async function saveLinkedProblems() {
    if (!currentProblem || selectedLinkedProblemsList.length === 0) {
        alert('Выберите хотя бы одну проблему');
        return;
    }
    
    try {
        const token = localStorage.getItem('accessToken');
        const problemId = currentProblem.ID;
        
        // Добавляем связи для каждой выбранной проблемы
        let successCount = 0;
        let errorCount = 0;
        
        for (const linkedProblem of selectedLinkedProblemsList) {
            try {
                const response = await fetch(API_CONFIG.buildURL(`/problems/${problemId}/link`), {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        linked_problem_id: linkedProblem.id
                    })
                });
                
                if (response.ok) {
                    successCount++;
                } else {
                    const error = await response.json();
                    if (error.error && error.error.includes('уже существует')) {
                        // Связь уже существует - это не ошибка
                        successCount++;
                    } else {
                        errorCount++;
                        console.error('Ошибка добавления связи:', error);
                    }
                }
            } catch (error) {
                errorCount++;
                console.error('Ошибка добавления связи:', error);
            }
        }
        
        if (successCount > 0) {
            alert(`Успешно добавлено связей: ${successCount}${errorCount > 0 ? `. Ошибок: ${errorCount}` : ''}`);
            closeLinkedProblemModal();
            // Перезагружаем страницу для обновления данных
            displaySolutions();
        } else if (errorCount > 0) {
            alert(`Ошибка при добавлении связей. Попробуйте еще раз.`);
        }
    } catch (error) {
        console.error('Ошибка сохранения связей:', error);
        alert('Ошибка при сохранении. Попробуйте еще раз.');
    }
}

// Инициализация модального окна для добавления решения
document.addEventListener('DOMContentLoaded', function() {
    // Обновляем состояние корзины при загрузке страницы
    updateCartIconState();
    const solutionModalOverlay = document.getElementById('solution-modal-overlay');
    const solutionModal = document.getElementById('solution-modal');
    const closeSolutionModalBtn = document.getElementById('closeSolutionModal');
    const form = document.getElementById('solutionForm');
    const clearBtn = document.getElementById('clearSolutionBtn');
    const problemSearch = document.getElementById('problemSearch');
    const problemDropdown = document.getElementById('problemDropdown');
    const selectedProblems = document.getElementById('selectedProblems');

    if (!solutionModalOverlay || !solutionModal || !form) {
        document.addEventListener('click', async (e) => {
            if (e.target.closest('#addSolutionBtn')) {
                try {
                    await auth.checkAuth(true);
                    const problemId = currentProblem?.ID;
                    window.location.href = problemId ? `/html/add_solution.html?problem_id=${problemId}` : 'html/add_solution.html';
                } catch (err) {
                    console.error(err);
                }
            }
        });
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

    // Элементы для выбора типа решения
    const solutionTypeSelection = document.getElementById('solution-type-selection');
    const existingSolutionForm = document.getElementById('existing-solution-form');
    const selectExistingSolutionBtn = document.getElementById('selectExistingSolution');
    const createNewSolutionBtn = document.getElementById('createNewSolution');
    const switchToNewSolutionBtn = document.getElementById('switchToNewSolutionBtn');
    const switchToExistingSolutionBtn = document.getElementById('switchToExistingSolutionBtn');
    const solutionSearch = document.getElementById('solutionSearch');
    const solutionDropdown = document.getElementById('solutionDropdown');
    const selectedSolutions = document.getElementById('selectedSolutions');
    const clearExistingSolutionBtn = document.getElementById('clearExistingSolutionBtn');
    const addExistingSolutionBtn = document.getElementById('addExistingSolutionBtn');

    // Функция для обновления отображения выбранных решений
    function updateSelectedSolutions() {
        if (!selectedSolutions) return;
        
        selectedSolutions.innerHTML = '';
        selectedSolutionsList.forEach(solution => {
            const div = document.createElement('div');
            div.className = 'selected-solution';
            div.innerHTML = `${solution.title} <span class="remove" data-id="${solution.id}">×</span>`;
            selectedSolutions.appendChild(div);
        });
    }

    // Функции для открытия/закрытия модального окна
    function openSolutionModal() {
        // Сбрасываем состояние
        resetSolutionModal();
        
        solutionModalOverlay.classList.add('active');
        document.body.style.overflow = 'hidden';
        
        // Если нет выбора типа решения, показываем форму сразу и подставляем текущую проблему
        if (!solutionTypeSelection && form) {
            form.style.display = 'flex';
            if (currentProblem && !selectedProblemsList.some(p => p.id === currentProblem.ID)) {
                selectedProblemsList.push({
                    id: currentProblem.ID,
                    title: currentProblem.Name || 'Без названия'
                });
                updateSelectedProblems();
            }
        }
    }

    function closeSolutionModal() {
        solutionModalOverlay.classList.remove('active');
        document.body.style.overflow = '';
        resetSolutionModal();
    }

    function resetSolutionModal() {
        // Если есть выбор типа решения, показываем его, иначе показываем форму сразу
        if (solutionTypeSelection) {
            solutionTypeSelection.style.display = 'block';
            if (existingSolutionForm) existingSolutionForm.style.display = 'none';
            if (form) form.style.display = 'none';
        } else {
            // Если нет выбора типа, показываем форму сразу
            if (form) form.style.display = 'flex';
            if (existingSolutionForm) existingSolutionForm.style.display = 'none';
        }
        
        // Очищаем формы
        if (form) form.reset();
        if (solutionSearch) solutionSearch.value = '';
        selectedProblemsList = [];
        selectedSolutionsList = [];
        updateSelectedProblems();
        updateSelectedSolutions();
        if (problemDropdown) problemDropdown.style.display = 'none';
        if (solutionDropdown) solutionDropdown.style.display = 'none';
    }

    // Обработчики выбора типа решения
    if (selectExistingSolutionBtn) {
        selectExistingSolutionBtn.addEventListener('click', () => {
            if (solutionTypeSelection) solutionTypeSelection.style.display = 'none';
            if (existingSolutionForm) existingSolutionForm.style.display = 'block';
            if (form) form.style.display = 'none';
        });
    }

    if (createNewSolutionBtn) {
        createNewSolutionBtn.addEventListener('click', () => {
            // Предзаполняем текущую проблему
            if (currentProblem && !selectedProblemsList.some(p => p.id === currentProblem.ID)) {
                selectedProblemsList.push({
                    id: currentProblem.ID,
                    title: currentProblem.Name || 'Без названия'
                });
                updateSelectedProblems();
            }
            
            if (solutionTypeSelection) solutionTypeSelection.style.display = 'none';
            if (existingSolutionForm) existingSolutionForm.style.display = 'none';
            if (form) form.style.display = 'block';
        });
    }

    if (switchToNewSolutionBtn) {
        switchToNewSolutionBtn.addEventListener('click', () => {
            // Предзаполняем текущую проблему
            if (currentProblem && !selectedProblemsList.some(p => p.id === currentProblem.ID)) {
                selectedProblemsList.push({
                    id: currentProblem.ID,
                    title: currentProblem.Name || 'Без названия'
                });
                updateSelectedProblems();
            }
            
            if (existingSolutionForm) existingSolutionForm.style.display = 'none';
            if (form) form.style.display = 'block';
        });
    }

    if (switchToExistingSolutionBtn) {
        switchToExistingSolutionBtn.addEventListener('click', () => {
            if (form) form.style.display = 'none';
            if (existingSolutionForm) existingSolutionForm.style.display = 'block';
        });
    }

    // Обработчики событий для кнопки добавления решения
    // Используем делегирование событий, так как кнопка создается динамически
    document.addEventListener('click', async (e) => {
        if (e.target.closest('#addSolutionBtn')) {
            try {
                await auth.checkAuth(true);
                openSolutionModal();
            } catch (error) {
                console.error('Ошибка авторизации:', error);
            }
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

    // Поиск существующих решений
    if (solutionSearch && solutionDropdown) {
        solutionSearch.addEventListener('input', async (e) => {
            const query = e.target.value.trim();
            if (query.length > 2) {
                try {
                    const token = localStorage.getItem('accessToken');
                    const response = await fetch(API_CONFIG.buildURLWithParams(API_CONFIG.ENDPOINTS.SOLUTIONS, {search: query, limit: 10}), {
                        headers: {
                            'Authorization': `Bearer ${token}`,
                            'Content-Type': 'application/json'
                        }
                    });
                    
                    if (response.ok) {
                        const solutions = await response.json();
                        solutionDropdown.innerHTML = '';
                        
                        // Исключаем решения, которые уже связаны с текущей проблемой
                        const currentProblemSolutionIds = (currentProblem && currentProblem.Solutions && Array.isArray(currentProblem.Solutions))
                            ? currentProblem.Solutions.map(s => s.ID || s.id) 
                            : [];
                        
                        solutions.forEach(solution => {
                            // Проверяем, не выбрано ли уже это решение
                            if (selectedSolutionsList.some(s => s.id === solution.ID)) {
                                return;
                            }
                            
                            // Проверяем, не связано ли уже это решение с текущей проблемой
                            if (currentProblemSolutionIds.includes(solution.ID)) {
                                return;
                            }
                            
                            const div = document.createElement('div');
                            div.className = 'dropdown-item';
                            div.innerHTML = `
                                <div class="solution-item">
                                    <strong>${solution.Name || 'Без названия'}</strong>
                                    ${solution.Describe ? `<div class="solution-description">${solution.Describe.substring(0, 100)}${solution.Describe.length > 100 ? '...' : ''}</div>` : ''}
                                </div>
                            `;
                            div.setAttribute('data-id', solution.ID);
                            
                            div.addEventListener('click', () => {
                                selectedSolutionsList.push({ 
                                    id: solution.ID, 
                                    title: solution.Name || 'Без названия' 
                                });
                                updateSelectedSolutions();
                                solutionSearch.value = '';
                                solutionDropdown.style.display = 'none';
                            });
                            
                            solutionDropdown.appendChild(div);
                        });
                        
                        if (solutions.length > 0) {
                            solutionDropdown.style.display = 'block';
                        } else {
                            solutionDropdown.innerHTML = '<div class="dropdown-item">Решения не найдены</div>';
                            solutionDropdown.style.display = 'block';
                        }
                    }
                } catch (error) {
                    console.error('Ошибка поиска решений:', error);
                    solutionDropdown.style.display = 'none';
                }
            } else {
                solutionDropdown.style.display = 'none';
            }
        });
    }

    // Удаление выбранного решения
    if (selectedSolutions) {
        selectedSolutions.addEventListener('click', (e) => {
            if (e.target.classList.contains('remove')) {
                const id = parseInt(e.target.dataset.id);
                selectedSolutionsList = selectedSolutionsList.filter(s => s.id !== id);
                updateSelectedSolutions();
            }
        });
    }

    // Скрыть dropdown при клике вне
    document.addEventListener('click', (e) => {
        if (solutionSearch && solutionDropdown && 
            !solutionSearch.contains(e.target) && 
            !solutionDropdown.contains(e.target)) {
            solutionDropdown.style.display = 'none';
        }
    });

    // Очистка формы существующих решений
    if (clearExistingSolutionBtn) {
        clearExistingSolutionBtn.addEventListener('click', () => {
            selectedSolutionsList = [];
            updateSelectedSolutions();
            if (solutionSearch) solutionSearch.value = '';
            if (solutionDropdown) solutionDropdown.style.display = 'none';
        });
    }

    // Добавление существующего решения к проблеме
    if (addExistingSolutionBtn) {
        addExistingSolutionBtn.addEventListener('click', async () => {
            if (!currentProblem || selectedSolutionsList.length === 0) {
                alert('Выберите хотя бы одно решение');
                return;
            }
            
            try {
                const token = localStorage.getItem('accessToken');
                const problemId = currentProblem.ID;
                
                // Добавляем решения для каждой выбранной проблемы
                let successCount = 0;
                let errorCount = 0;
                
                for (const solution of selectedSolutionsList) {
                    try {
                        const response = await fetch(API_CONFIG.buildURL(`/problems/${problemId}/add-solution`), {
                            method: 'POST',
                            headers: {
                                'Authorization': `Bearer ${token}`,
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({
                                solution_id: solution.id
                            })
                        });
                        
                        if (response.ok) {
                            successCount++;
                        } else {
                            const error = await response.json();
                            if (error.error && error.error.includes('уже связано')) {
                                // Решение уже связано - это не ошибка
                                successCount++;
                            } else {
                                errorCount++;
                                console.error('Ошибка добавления решения:', error);
                            }
                        }
                    } catch (error) {
                        errorCount++;
                        console.error('Ошибка добавления решения:', error);
                    }
                }
                
                if (successCount > 0) {
                    alert(`Успешно добавлено решений: ${successCount}${errorCount > 0 ? `. Ошибок: ${errorCount}` : ''}`);
                    closeSolutionModal();
                    // Перезагружаем страницу для обновления данных
                    displaySolutions();
                } else if (errorCount > 0) {
                    alert(`Ошибка при добавлении решений. Попробуйте еще раз.`);
                }
            } catch (error) {
                console.error('Ошибка сохранения решений:', error);
                alert('Ошибка при сохранении. Попробуйте еще раз.');
            }
        });
    }

    // Инициализация
    updateSelectedProblems();
    updateSelectedSolutions();

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
                // Не позволяем удалить текущую проблему
                if (currentProblem && id === currentProblem.ID) {
                    alert('Нельзя удалить текущую проблему');
                    return;
                }
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
            // Снова добавляем текущую проблему
            if (currentProblem) {
                selectedProblemsList.push({
                    id: currentProblem.ID,
                    title: currentProblem.Name || 'Без названия'
                });
            }
            updateSelectedProblems();
            if (problemDropdown) problemDropdown.style.display = 'none';
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
                
                // Перезагружаем страницу для обновления списка решений
                displaySolutions();
            } else {
                const error = await response.json();
                alert('Ошибка: ' + (error.error || 'Неизвестная ошибка'));
            }
        } catch (error) {
            alert('Ошибка сети: ' + error.message);
        }
    });
    
    // Инициализация модального окна похожих проблем
    const linkedProblemModalOverlay = document.getElementById('linked-problem-modal-overlay');
    const linkedProblemModal = document.getElementById('linked-problem-modal');
    const closeLinkedProblemModalBtn = document.getElementById('closeLinkedProblemModal');
    const linkedProblemSearch = document.getElementById('linkedProblemSearch');
    const linkedProblemDropdown = document.getElementById('linkedProblemDropdown');
    const clearLinkedProblemBtn = document.getElementById('clearLinkedProblemBtn');
    const saveLinkedProblemBtn = document.getElementById('saveLinkedProblemBtn');
    
    if (linkedProblemModalOverlay && linkedProblemModal) {
        // Закрытие модального окна
        if (closeLinkedProblemModalBtn) {
            closeLinkedProblemModalBtn.addEventListener('click', closeLinkedProblemModal);
        }
        
        linkedProblemModalOverlay.addEventListener('click', (e) => {
            if (e.target === linkedProblemModalOverlay) {
                closeLinkedProblemModal();
            }
        });
        
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && linkedProblemModalOverlay.classList.contains('active')) {
                closeLinkedProblemModal();
            }
        });
        
        // Поиск проблем
        if (linkedProblemSearch && linkedProblemDropdown) {
            linkedProblemSearch.addEventListener('input', (e) => {
                const query = e.target.value.trim();
                
                // Очищаем предыдущий таймаут
                if (linkedProblemSearchTimeout) {
                    clearTimeout(linkedProblemSearchTimeout);
                }
                
                // Устанавливаем новый таймаут для задержки запроса
                linkedProblemSearchTimeout = setTimeout(() => {
                    searchLinkedProblems(query);
                }, 300);
            });
        }
        
        // Скрыть dropdown при клике вне
        document.addEventListener('click', (e) => {
            if (linkedProblemSearch && linkedProblemDropdown && 
                !linkedProblemSearch.contains(e.target) && 
                !linkedProblemDropdown.contains(e.target)) {
                linkedProblemDropdown.style.display = 'none';
            }
        });
        
        // Очистка
        if (clearLinkedProblemBtn) {
            clearLinkedProblemBtn.addEventListener('click', () => {
                selectedLinkedProblemsList = [];
                updateSelectedLinkedProblems();
                if (linkedProblemSearch) linkedProblemSearch.value = '';
                if (linkedProblemDropdown) linkedProblemDropdown.style.display = 'none';
            });
        }
        
        // Сохранение
        if (saveLinkedProblemBtn) {
            saveLinkedProblemBtn.addEventListener('click', saveLinkedProblems);
        }
    }
});

// Функции для работы с модальным окном просмотра изображений
function openImageViewer(imageSrc, imageAlt) {
    const modal = document.getElementById('image-viewer-modal');
    const viewerImage = document.getElementById('viewer-image');
    
    if (modal && viewerImage) {
        viewerImage.src = imageSrc;
        viewerImage.alt = imageAlt || 'Изображение';
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

function closeImageViewer() {
    const modal = document.getElementById('image-viewer-modal');
    
    if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
    }
}

// Инициализация обработчиков модального окна просмотра изображений
document.addEventListener('DOMContentLoaded', function() {
    const modal = document.getElementById('image-viewer-modal');
    const closeBtn = document.getElementById('closeImageViewer');
    
    if (closeBtn) {
        closeBtn.addEventListener('click', closeImageViewer);
    }
    
    if (modal) {
        // Закрытие при клике на overlay
        modal.addEventListener('click', (e) => {
            if (e.target === modal || e.target.classList.contains('image-viewer-overlay')) {
                closeImageViewer();
            }
        });
        
        // Закрытие при нажатии Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && modal.classList.contains('active')) {
                closeImageViewer();
            }
        });
    }
});
