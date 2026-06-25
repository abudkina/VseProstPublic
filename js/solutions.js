// solutions.js
// Вместо дублированного кода auth
import { initAuthHandlers } from './common.js';
import { initTagsScroll } from './tagsScroll.js';
import { addToCart, checkInCart } from './cartFunctions.js';
import {
    loadCategories,
    initHashtagsTomSelect,
    initFilterHandlers,
    initTagClickHandler
} from './problemListCommon.js';
import { initMobileFilters } from './mobileFilters.js';

// Инициализация обработчиков авторизации
initAuthHandlers();

const PAGE_SIZE = 20;
let choicesInstance;
let hasMore = true;
let loadingMore = false;
let scrollSentinel = null;
let scrollObserver = null;

let currentFilters = {
  search: '',
  hashtags: [],
  category: null,
  limit: PAGE_SIZE,
  offset: 0
};

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

async function loadCards(append = false, onDone = null) {
  const container = document.querySelector('.cards-container');
  if (!append) container.innerHTML = 'Загрузка...';

  const searchEl = document.getElementById('search');
  const searchValue = (searchEl && searchEl.value && searchEl.value.trim()) || (currentFilters.search || '').trim();

  const params = new URLSearchParams();
  if (searchValue) params.append('search', searchValue);
  if (currentFilters.hashtags && currentFilters.hashtags.length)
    params.append('hashtags', currentFilters.hashtags.join(','));
  if (currentFilters.category != null && Number.isInteger(currentFilters.category))
    params.append('category', currentFilters.category);
  params.append('limit', currentFilters.limit);
  params.append('offset', currentFilters.offset);
  params.set('_', String(Date.now()));

  try {
    const response = await fetch(API_CONFIG.buildURL(`/solutions?${params.toString()}`), { cache: 'no-store' });
    if (!response.ok) throw new Error('Ошибка HTTP: ' + response.status);
    const data = await response.json();
    const list = (data && data.solutions !== undefined) ? data.solutions : (Array.isArray(data) ? data : []);
    const more = list.length >= currentFilters.limit;
    if (append) {
      renderCards(list, { append: true });
    } else {
      sortAndRender(list);
    }
    if (onDone) onDone(more);
  } catch (error) {
    if (!append) container.innerHTML = `<p style="color:red; text-align:center">Ошибка загрузки данных: ${error.message}</p>`;
    if (onDone) onDone(false);
  }
}

// Функция loadCategories теперь импортируется из problemListCommon.js

function sortAndRender(data) {
  const sortValue = document.getElementById('sort').value;

  switch (sortValue) {
    case 'popularity':
      data.sort((a, b) => (b.Favourite || 0) - (a.Favourite || 0));
      break;
    case 'show':
      data.sort((a, b) => (b.Show || 0) - (a.Show || 0));
      break;
    case 'date':
      data.sort((a, b) => new Date(b.Modified_date) - new Date(a.Modified_date));
      break;
    default:
      break;
  }

  renderCards(data);
}

// Теперь используем градиентный фон вместо внешних изображений

function renderCards(data, options = {}) {
  const container = document.querySelector('.cards-container');
  const append = options.append === true;
  if (!append) container.innerHTML = '';

  const templateElement = document.getElementById('card-template');
  if (!templateElement) {
    console.error("Шаблон не найден!");
    return;
  }
  const template = templateElement.content;

  if (data.length === 0) {
    if (append) return;
    container.innerHTML = '<p style="text-align:center;">Ничего не найдено</p>';
    return;
  }

  data.forEach(item => {
    const card = template.cloneNode(true);

    const link = card.querySelector('.card-title-link');
    link.href = (window.PATHS ? window.PATHS.solution(item.ID) : `/solution/${item.ID}`);

    const cardImg = card.querySelector('.card-image');
    const cardImageWrapper = card.querySelector('.card-image-wrapper');
    if (cardImg) cardImg.loading = 'lazy';

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
        ['#667eea', '#764ba2'], // Фиолетовый
        ['#f093fb', '#f5576c'], // Розовый
        ['#4facfe', '#00f2fe'], // Синий
        ['#43e97b', '#38f9d7'], // Зеленый
        ['#fa709a', '#fee140'], // Желто-розовый
        ['#30cfd0', '#330867'], // Бирюзовый
        ['#a8edea', '#fed6e3'], // Пастель
        ['#d299c2', '#fef9d7'], // Лаванда
        ['#ff9a9e', '#fecfef'], // Нежно-розовый
        ['#ffecd2', '#fcb69f'], // Персиковый
      ];
      
      const colorPair = colors[imageId % colors.length];
      
      // Очищаем название для текста
      const displayText = solutionName.trim()
        .replace(/[<>]/g, '')
        .substring(0, 30);
      
      // Создаем SVG изображение с градиентом и текстом
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
      
      // Кодируем SVG в data URL
      return 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg);
    }
    
    // Используем изображение из базы: наш origin или прокси — показываем как есть, внешние URL — fallback SVG
    const isOurImage = item.Image && item.Image.trim() !== '' &&
      (item.Image.startsWith('/') ||
       item.Image.includes('/api/storage-image') ||
       (item.Image.startsWith('http') && (item.Image.startsWith(window.location.origin) || item.Image.includes('storage-image'))));

    if (item.Image && item.Image.trim() !== '') {
      if (isOurImage) {
        cardImg.src = item.Image.startsWith('/') ? item.Image : (item.Image.startsWith('http') ? item.Image : '/' + item.Image.replace(/^\//, ''));
        cardImg.alt = item.Name || 'Решение';
        cardImg.style.display = 'block';
        if (cardImageWrapper) cardImageWrapper.style.background = 'none';
        cardImg.onerror = function() {
          const generatedImage = getImageFromInternet(item.Name);
          if (generatedImage) {
            this.src = generatedImage;
            if (cardImageWrapper) cardImageWrapper.style.background = 'none';
          } else {
            this.style.display = 'none';
            if (cardImageWrapper) cardImageWrapper.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
          }
        };
      } else if (item.Image.startsWith('http://') || item.Image.startsWith('https://')) {
        const generatedImage = getImageFromInternet(item.Name);
        if (generatedImage) {
          cardImg.src = generatedImage;
          cardImg.alt = item.Name || 'Решение';
          cardImg.style.display = 'block';
          if (cardImageWrapper) cardImageWrapper.style.background = 'none';
        } else {
          cardImg.style.display = 'none';
          if (cardImageWrapper) cardImageWrapper.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
        }
      } else {
        // Локальный файл - нормализуем путь (с ведущим /)
        cardImg.src = item.Image.startsWith('/') ? item.Image : '/' + item.Image.replace(/^\//, '');
        cardImg.alt = item.Name || 'Решение';
        cardImg.style.display = 'block';
        if (cardImageWrapper) {
          cardImageWrapper.style.background = 'none';
        }
        
        // Обработка ошибки загрузки локального изображения
        cardImg.onerror = function() {
          // При ошибке локального файла генерируем SVG изображение
          const generatedImage = getImageFromInternet(item.Name);
          if (generatedImage) {
            this.src = generatedImage;
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
    } else {
      // Нет изображения - генерируем SVG изображение
      const generatedImage = getImageFromInternet(item.Name);
      if (generatedImage) {
        cardImg.src = generatedImage;
        cardImg.alt = item.Name || 'Решение';
        cardImg.style.display = 'block';
        if (cardImageWrapper) {
          cardImageWrapper.style.background = 'none';
        }
      } else {
        // Не удалось сгенерировать - используем градиентный фон
        cardImg.style.display = 'none';
        if (cardImageWrapper) {
          cardImageWrapper.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
        }
      }
    }

    const cardTitleText = card.querySelector('.card-title-text');
    cardTitleText.href = (window.PATHS ? window.PATHS.solution(item.ID) : `/solution/${item.ID}`);
    cardTitleText.textContent = item.Name;

    const favoriteCount = card.querySelector('.card-favorites .favorite-count');
    favoriteCount.textContent = item.Favourite || 0;

    // Общий рейтинг
    const ratingNumber = card.querySelector('.rating-number');
    if (ratingNumber) {
      ratingNumber.textContent = item.Rating || 0;
    }

    // Обработчик избранного для решений
    const favoriteIcon = card.querySelector('.favorite-icon');
    if (favoriteIcon) {
      favoriteIcon.style.cursor = 'pointer';
      
      // Проверяем статус избранного и меняем иконку
      setFavoriteIconState(favoriteIcon, item.IsFavourite);
      
      favoriteIcon.addEventListener('click', async (e) => {
        e.preventDefault();
        e.stopPropagation();
        await toggleSolutionFavorite(item.ID, favoriteIcon);
      });
    }

    // Отображаем темы из связанных проблем
    const topicElement = card.querySelector('.problem-topic');
    if (topicElement) {
      topicElement.innerHTML = '';
      // Собираем уникальные темы из всех связанных проблем
      const topicsMap = new Map();
      if (item.Problems && Array.isArray(item.Problems)) {
        item.Problems.forEach(problem => {
          if (problem.TopicInfo && problem.TopicInfo.Name) {
            const topicId = problem.TopicInfo.ID;
            if (!topicsMap.has(topicId)) {
              topicsMap.set(topicId, problem.TopicInfo);
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

    const tagsColumn = card.querySelector('.tags-column');
    tagsColumn.innerHTML = '';
    if (item.Problems && Array.isArray(item.Problems)) {
      item.Problems.forEach(problem => {
        if (problem.Hashtags && Array.isArray(problem.Hashtags)) {
          problem.Hashtags.forEach(tag => {
            const tagElement = document.createElement('span');
            tagElement.className = 'tag';
            tagElement.textContent = tag.Name;
            tagElement.setAttribute('data-id', tag.ID);
            tagElement.style.cursor = 'pointer';
            tagsColumn.appendChild(tagElement);
          });
        }
      });
    }
    card.querySelector('.stat-item.views .stat-value').textContent = item.Show || 0;
    card.querySelector('.stat-item.comments .stat-value').textContent = item.CommentCount ?? item.CommentSolutions?.length ?? 0;
    card.querySelector('.stat-item.shares .stat-value').textContent = item.Reply || 0;
    
    // Количество линков (связанных решений)
    const linksValue = item.LinkedSolutionsCount || item.LinkedSolutions?.length || 0;
    const linksElem = card.querySelector('.stat-item.links .stat-value');
    if (linksElem) linksElem.textContent = linksValue;

    // Кнопка добавления в корзину
    const cartBtn = card.querySelector('.card-cart-btn');
    if (cartBtn) {
      const cartIcon = cartBtn.querySelector('i');
      
      cartBtn.addEventListener('click', async (e) => {
        e.preventDefault();
        e.stopPropagation();
        await handleAddToCart(item.ID, cartBtn, cartIcon);
      });
      
      // Проверяем, есть ли уже в корзине
      checkInCart(item.ID).then(inCart => {
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

    container.appendChild(card);
  });
  
  // Инициализируем прокрутку тегов после рендеринга
  setTimeout(() => {
    initTagsScroll();
  }, 100);
}

// Обработчик клика по тегам теперь используется через initTagClickHandler

// Функция initTomSelect заменена на использование initHashtagsTomSelect из problemListCommon.js

// Обработчики фильтров теперь инициализируются через initFilterHandlers

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

// Переключение избранного для решений
async function toggleSolutionFavorite(solutionId, iconElement) {
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
          const countElement = iconElement.closest('.card-favorites')?.querySelector('.favorite-count');
          if (countElement) {
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
    console.error('Ошибка добавления решения в избранное:', error);
  } finally {
    iconElement.dataset.pending = '0';
    iconElement.style.pointerEvents = '';
    if (wrapper) {
      wrapper.style.pointerEvents = '';
    }
  }
}

function addSentinel() {
  const container = document.querySelector('.cards-container');
  if (!container || container.querySelector('.scroll-sentinel')) return;
  const sentinel = document.createElement('div');
  sentinel.className = 'scroll-sentinel';
  sentinel.setAttribute('aria-hidden', 'true');
  container.appendChild(sentinel);
  scrollSentinel = sentinel;
  if (scrollObserver) scrollObserver.observe(sentinel);
}

function removeSentinel() {
  scrollSentinel?.remove();
  scrollSentinel = null;
}

function reloadCards() {
  currentFilters.append = false;
  currentFilters.offset = 0;
  loadCards(false, (more) => {
    hasMore = more;
    if (hasMore) addSentinel();
  });
}

function loadMoreCards() {
  if (loadingMore || !hasMore) return;
  loadingMore = true;
  const container = document.querySelector('.cards-container');
  currentFilters.offset = container ? container.querySelectorAll('.card').length : 0;
  currentFilters.append = true;
  loadCards(true, (more) => {
    hasMore = more;
    loadingMore = false;
    if (!hasMore) removeSentinel();
  });
}

// Инициализация
document.addEventListener('DOMContentLoaded', async () => {
  // Загружаем категории
  await loadCategories('category', false);
  
  // Инициализируем TomSelect для хэштегов
  scrollObserver = new IntersectionObserver(
    (entries) => { if (entries[0]?.isIntersecting) loadMoreCards(); },
    { rootMargin: '200px', threshold: 0 }
  );
  choicesInstance = initHashtagsTomSelect('hashtags', (instance) => {
    currentFilters.hashtags = instance.getValue().map(v => parseInt(v, 10));
    currentFilters.offset = 0;
    hasMore = true;
    reloadCards();
    document.querySelector('.vs-control')?.classList.add('has-items');
  });
  
  // Обработчик удаления хэштегов
  if (choicesInstance) {
    choicesInstance.control.addEventListener('click', function (event) {
      const tag = event.target.closest('.item');
      if (tag) {
        const value = tag.getAttribute('data-value');
        if (value !== null) {
          choicesInstance.removeItem(value);
          currentFilters.hashtags = choicesInstance.getValue().map(v => parseInt(v, 10));
          currentFilters.offset = 0;
          hasMore = true;
          // Очищаем опции и закрываем выпадающий список при удалении
          choicesInstance.clearOptions();
          choicesInstance.close();
          choicesInstance.control_input.value = '';
          reloadCards();
          if (choicesInstance.items.length == 0) {
            const tsControl = document.querySelector('.vs-control');
            if (tsControl) {
              tsControl.classList.remove('has-items');
              // Убеждаемся, что плейсхолдер виден
              const input = tsControl.querySelector('input[type="text"]');
              if (input && !input.value) {
                input.placeholder = 'Выберите хэштеги';
              }
            }
          }
        }
      }
    });
    
    initTagClickHandler(choicesInstance, currentFilters, reloadCards);
  }
  
  initFilterHandlers(currentFilters, choicesInstance, reloadCards);
  initMobileFilters({ onFilterChange: reloadCards });
  
  // Сортировка
  const sortSelect = document.getElementById('sort');
  if (sortSelect) {
    sortSelect.addEventListener('change', () => {
      currentFilters.offset = 0;
      reloadCards();
    });
  }
  
  // Загружаем карточки
  reloadCards();
});
