// favourites.js
import * as auth from './authorizationFunctions.js';
import { initAuthHandlers } from './common.js';
import { initTagsScroll } from './tagsScroll.js';
import { updateCartIconState, addToCart, checkInCart } from './cartFunctions.js';
import {
    loadCategories,
    initHashtagsTomSelect,
    initFilterHandlers,
    initTagClickHandler
} from './problemListCommon.js';

// Инициализация обработчиков авторизации
initAuthHandlers();

// Теперь используем градиентный фон вместо внешних изображений

let choicesInstance;
let currentTab = 'problems'; // 'problems' или 'solutions'

let currentFilters = {
  search: '',
  hashtags: [],
  category: null,
  limit: 50,
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

async function loadCards() {
  const container = currentTab === 'problems' 
    ? document.getElementById('problems-container')
    : document.getElementById('solutions-container');
  
  if (!container) return;
  
  container.innerHTML = 'Загрузка...';

  try {
    // Проверяем аутентификацию
    await auth.checkAuth(true);
  } catch (error) {
    return;
  }

  const params = new URLSearchParams();
  if (currentFilters.search) params.append('search', currentFilters.search);
  if (currentFilters.hashtags.length)
    params.append('hashtags', currentFilters.hashtags.join(','));
  if (currentFilters.category != null)
    params.append('category', currentFilters.category);
  params.append('limit', currentFilters.limit);
  params.append('offset', currentFilters.offset);

  const apiUrl = currentTab === 'problems'
    ? `/api/problems/favorites?${params.toString()}`
    : `/api/solutions/favorites?${params.toString()}`;
  
  try {
    let response = await fetch(apiUrl, {
      method: 'GET',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    // Если получили 401, пробуем обновить токен и повторить запрос
    if (response.status === 401) {
      console.log('Получен 401, пробуем обновить токен...');
      
      try {
        await auth.refreshToken();
        console.log('Токен обновлен, повторяем запрос...');
        
        response = await fetch(apiUrl, {
          method: 'GET',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json'
          }
        });
        
        if (response.status === 401) {
          throw new Error('Требуется авторизация');
        }
        
      } catch (refreshError) {
        console.error('Ошибка обновления токена:', refreshError);
        localStorage.removeItem('isLoggedIn');
        sessionStorage.setItem('redirectAfterLogin', window.location.href);
        window.location.href = '/html/authorization.html';
        return;
      }
    }
    
    if (!response.ok) {
      throw new Error('Ошибка HTTP: ' + response.status);
    }
    
    const raw = await response.json();
    const data = Array.isArray(raw) ? raw : (raw?.solutions ?? raw?.problems ?? []);
    
    // Применяем сортировку перед рендерингом
    const sortedData = sortData(data);
    
    if (currentTab === 'problems') {
      renderProblemCards(sortedData);
    } else {
      renderSolutionCards(sortedData);
    }

  } catch (error) {
    console.error('Ошибка загрузки избранного:', error);
    container.innerHTML = `<p style="color:red; text-align:center">Ошибка загрузки данных: ${error.message}</p>`;
    
    if (error.message.includes('Требуется авторизация') || error.message.includes('401')) {
      setTimeout(() => {
        localStorage.removeItem('isLoggedIn');
        sessionStorage.setItem('redirectAfterLogin', window.location.href);
        window.location.href = '/html/authorization.html';
      }, 2000);
    }
  }
}

// Функция loadCategories теперь импортируется из problemListCommon.js

// Функция сортировки данных
function sortData(data) {
  const sortValue = document.getElementById('sort')?.value || 'default';
  const sorted = [...data]; // Создаем копию массива
  
  switch (sortValue) {
    case 'popularity':
      sorted.sort((a, b) => (b.Favourite || 0) - (a.Favourite || 0));
      break;
    case 'show':
      sorted.sort((a, b) => (b.Show || 0) - (a.Show || 0));
      break;
    case 'date':
      sorted.sort((a, b) => {
        const dateA = new Date(a.Modified_date || a.Created_date || 0);
        const dateB = new Date(b.Modified_date || b.Created_date || 0);
        return dateB - dateA;
      });
      break;
    default:
      break;
  }
  
  return sorted;
}

function renderProblemCards(data) {
  const container = document.getElementById('problems-container');
  if (!container) return;
  
  container.innerHTML = '';

  const templateElement = document.getElementById('problem-card-template');
  if (!templateElement) {
    console.error("Шаблон проблем не найден!");
    return;
  }
  const template = templateElement.content;

  if (!data || data.length === 0) {
    container.innerHTML = '<p style="text-align:center;">Нет избранных проблем</p>';
    return;
  }

  data.forEach(item => {
    const card = template.cloneNode(true);

    const link = card.querySelector('.card-title-link');
    if (link) {
      link.href = `/problem/${item.ID}`;
    }

    const cardImg = card.querySelector('.card-image');
    if (cardImg) {
      cardImg.loading = 'lazy';
      cardImg.src = item.Image || '../images/default.png';
      cardImg.alt = item.Name || 'Проблема';
    }

    const cardTitleText = card.querySelector('.card-title-text');
    if (cardTitleText) {
      cardTitleText.textContent = item.Name || 'Без названия';
      if (cardTitleText.tagName === 'A') {
        cardTitleText.href = `/problem/${item.ID}`;
      }
    }

    const favoriteCount = card.querySelector('.card-favorites .favorite-count');
    if (favoriteCount) {
      favoriteCount.textContent = item.Favourite || 0;
    }

    // Меняем иконку в зависимости от статуса избранного
    const favoriteIcon = card.querySelector('.favorite-icon');
    if (favoriteIcon) {
      setFavoriteIconState(favoriteIcon, item.IsFavourite ?? true);
    }

    // Тема проблемы
    const topicElement = card.querySelector('.problem-topic');
    if (topicElement) {
      if (item.TopicInfo && item.TopicInfo.Name) {
        topicElement.innerHTML = '';
        const topicLink = document.createElement('a');
        topicLink.className = 'topic-link';
        topicLink.href = '/';
        topicLink.textContent = item.TopicInfo.Name;
        topicLink.setAttribute('data-topic-id', item.TopicInfo.ID);
        topicLink.style.cursor = 'pointer';
        topicLink.addEventListener('click', (e) => {
          e.preventDefault();
          e.stopPropagation();
          window.location.href = `/?topic=${item.TopicInfo.ID}`;
        });
        topicElement.appendChild(topicLink);
        topicElement.style.display = 'block';
      } else {
        topicElement.style.display = 'none';
      }
    }

    const tagsColumn = card.querySelector('.tags-column');
    if (tagsColumn) {
      tagsColumn.innerHTML = '';
      if (item.Hashtags && Array.isArray(item.Hashtags)) {
        item.Hashtags.forEach(tag => {
          const tagElement = document.createElement('span');
          tagElement.className = 'tag';
          tagElement.textContent = tag.Name;
          tagElement.setAttribute('data-id', tag.ID);
          tagsColumn.appendChild(tagElement);
        });
      }
    }
    
    // Добавляем обработчик клика на теги для фильтрации
    const tags = card.querySelectorAll('.tag');
    tags.forEach(tag => {
      tag.style.cursor = 'pointer';
    });

    // Статистика
    const viewsElem = card.querySelector('.stat-item.views .stat-value');
    if (viewsElem) viewsElem.textContent = item.Show || 0;
    
    const commentsElem = card.querySelector('.stat-item.comments .stat-value');
    if (commentsElem) commentsElem.textContent = item.Solutions || 0;
    
    const sharesElem = card.querySelector('.stat-item.shares .stat-value');
    if (sharesElem) sharesElem.textContent = item.Reply || 0;
    
    const linksElem = card.querySelector('.stat-item.links .stat-value');
    if (linksElem) linksElem.textContent = item.LinkedProblems || 0;

    container.appendChild(card);
  });
  
  // Инициализируем прокрутку тегов после рендеринга
  setTimeout(() => {
    initTagsScroll();
  }, 100);
}

function renderSolutionCards(data) {
  const container = document.getElementById('solutions-container');
  if (!container) return;
  
  container.innerHTML = '';

  const templateElement = document.getElementById('solution-card-template');
  if (!templateElement) {
    console.error("Шаблон решений не найден!");
    return;
  }
  const template = templateElement.content;

  if (!data || data.length === 0) {
    container.innerHTML = '<p style="text-align:center;">Нет избранных решений</p>';
    return;
  }

  data.forEach(item => {
    const card = template.cloneNode(true);

    const link = card.querySelector('.card-title-link');
    if (link) {
      link.href = `/solution/${item.ID}`;
    }

    const cardImg = card.querySelector('.card-image');
    const cardImageWrapper = card.querySelector('.card-image-wrapper');
    if (cardImg) cardImg.loading = 'lazy';

    if (cardImg) {
      // Функция для получения изображения из интернета по названию
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
      
      // Используем изображение решения напрямую из API
      if (item.Image && item.Image.trim() !== '') {
        // Если это внешний URL, ищем изображение в интернете по названию
        if (item.Image.startsWith('http://') || item.Image.startsWith('https://')) {
          const internetImage = getImageFromInternet(item.Name);
          if (internetImage) {
            cardImg.src = internetImage;
            cardImg.style.display = 'block';
            if (cardImageWrapper) {
              cardImageWrapper.style.background = 'none';
            }
            
            cardImg.onerror = function() {
              this.style.display = 'none';
              if (cardImageWrapper) {
                cardImageWrapper.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
              }
            };
          } else {
            cardImg.style.display = 'none';
            if (cardImageWrapper) {
              cardImageWrapper.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
            }
          }
        } else {
          // Локальный файл - используем как есть
          cardImg.src = item.Image.startsWith('/') ? item.Image : '/' + item.Image;
          cardImg.style.display = 'block';
          if (cardImageWrapper) {
            cardImageWrapper.style.background = 'none';
          }
          
          // Обработка ошибки загрузки локального изображения - пробуем интернет
          cardImg.onerror = function() {
            const internetImage = getImageFromInternet(item.Name);
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
      } else {
        // Если изображения нет, ищем в интернете по названию
        const internetImage = getImageFromInternet(item.Name);
        if (internetImage) {
          cardImg.src = internetImage;
          cardImg.style.display = 'block';
          if (cardImageWrapper) {
            cardImageWrapper.style.background = 'none';
          }
          
          cardImg.onerror = function() {
            this.style.display = 'none';
            if (cardImageWrapper) {
              cardImageWrapper.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
            }
          };
        } else {
          cardImg.style.display = 'none';
          if (cardImageWrapper) {
            cardImageWrapper.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
          }
        }
      }
      cardImg.alt = item.Name || 'Решение';
    }

    const cardTitleText = card.querySelector('.card-title-text');
    if (cardTitleText) {
      cardTitleText.textContent = item.Name || 'Без названия';
      if (cardTitleText.tagName === 'A') {
        cardTitleText.href = `/solution/${item.ID}`;
      }
    }

    const favoriteCount = card.querySelector('.card-favorites .favorite-count');
    if (favoriteCount) {
      favoriteCount.textContent = item.Favourite || 0;
    }

    // Общий рейтинг
    const ratingNumber = card.querySelector('.rating-number');
    if (ratingNumber) {
      ratingNumber.textContent = item.Rating || 0;
    }

    // Меняем иконку в зависимости от статуса избранного
    const favoriteIcon = card.querySelector('.favorite-icon');
    if (favoriteIcon) {
      setFavoriteIconState(favoriteIcon, item.IsFavourite ?? true);
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
    if (tagsColumn) {
      tagsColumn.innerHTML = '';
      if (item.Problems && Array.isArray(item.Problems)) {
        item.Problems.forEach(problem => {
          // Добавляем хэштеги из проблем
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
    }

    // Статистика
    const viewsElem = card.querySelector('.stat-item.views .stat-value');
    if (viewsElem) viewsElem.textContent = item.Show || 0;
    
    const commentsElem = card.querySelector('.stat-item.comments .stat-value');
    if (commentsElem) commentsElem.textContent = item.Comments?.length || 0;
    
    // Количество линков (связанных решений)
    const linksValue = item.LinkedSolutionsCount || item.LinkedSolutions?.length || 0;
    const linksElem = card.querySelector('.stat-item.links .stat-value');
    if (linksElem) linksElem.textContent = linksValue;

    // Кнопка корзины
    const cartBtn = card.querySelector('.card-cart-btn');
    if (cartBtn) {
      const cartIcon = cartBtn.querySelector('i');
      
      // Функция для обновления иконки корзины
      const updateCartIcon = (inCart) => {
        if (!cartIcon) return;
        
        if (inCart) {
          cartIcon.classList.add('cart-in-cart');
        } else {
          cartIcon.classList.remove('cart-in-cart');
        }
      };
      
      cartBtn.addEventListener('click', async (e) => {
        e.preventDefault();
        e.stopPropagation();
        
        const result = await addToCart(item.ID);
        
        if (result.success) {
          cartBtn.classList.add('in-cart');
          cartBtn.title = 'Уже в корзине';
          updateCartIcon(true);
          alert(result.message || 'Решение добавлено в корзину');
        } else {
          alert(result.error || 'Не удалось добавить в корзину');
        }
      });
      
      // Проверяем, есть ли уже в корзине
      checkInCart(item.ID).then(inCart => {
        if (inCart) {
          cartBtn.classList.add('in-cart');
          cartBtn.title = 'Уже в корзине';
          updateCartIcon(true);
        } else {
          updateCartIcon(false);
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

// Функция initTomSelect заменена на использование initHashtagsTomSelect из problemListCommon.js

// Переключение вкладок
function switchTab(tabName) {
  currentTab = tabName;
  
  // Сбрасываем offset при переключении вкладок
  currentFilters.offset = 0;
  
  // Обновляем активную вкладку
  document.querySelectorAll('.tab-button').forEach(btn => {
    btn.classList.remove('active');
    if (btn.dataset.tab === tabName) {
      btn.classList.add('active');
    }
  });
  
  // Показываем/скрываем контейнеры
  const problemsContainer = document.getElementById('problems-container');
  const solutionsContainer = document.getElementById('solutions-container');
  
  if (tabName === 'problems') {
    if (problemsContainer) problemsContainer.style.display = 'grid';
    if (solutionsContainer) solutionsContainer.style.display = 'none';
  } else {
    if (problemsContainer) problemsContainer.style.display = 'none';
    if (solutionsContainer) solutionsContainer.style.display = 'grid';
  }
  
  // Загружаем данные для выбранной вкладки
  loadCards();
}

// Функция для перезагрузки карточек
function reloadCards() {
  loadCards();
}

// Инициализация
document.addEventListener('DOMContentLoaded', async () => {
  // Обновляем состояние корзины при загрузке страницы
  updateCartIconState();
  
  // Загружаем категории
  await loadCategories('category', true);
  
  // Инициализируем TomSelect для хэштегов
  choicesInstance = initHashtagsTomSelect('hashtags', (instance) => {
    currentFilters.hashtags = instance.getValue().map(v => parseInt(v, 10));
    currentFilters.offset = 0;
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
    
    // Инициализация обработчиков фильтров
    initFilterHandlers(currentFilters, choicesInstance, reloadCards);
    initTagClickHandler(choicesInstance, currentFilters, reloadCards);
  }
  
  // Сортировка
  const sortSelect = document.getElementById('sort');
  if (sortSelect) {
    sortSelect.addEventListener('change', () => {
      currentFilters.offset = 0;
      reloadCards();
    });
  }
  
  // Обработчики вкладок
  document.querySelectorAll('.tab-button').forEach(btn => {
    btn.addEventListener('click', () => {
      switchTab(btn.dataset.tab);
    });
  });
  
  // Загружаем карточки
  reloadCards();
});
