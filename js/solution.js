// solution.js

// Вместо дублированного кода auth
import { initAuthHandlers } from './common.js';
import { addToCart, checkInCart, updateCartIconState } from './cartFunctions.js';
import { getAuthHeaders } from './authorizationFunctions.js';
import { initTagsScroll } from './tagsScroll.js';
import { updateSEOMetaTags, addStructuredData, createSolutionStructuredData } from './utils/seo.js';

// Инициализация обработчиков авторизации
initAuthHandlers();

// Теперь используем градиентный фон вместо внешних изображений

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

// Создаёт элемент с указанным тегом, классом и текстом (опционально)
function createElem(tag, className, text) {
  const el = document.createElement(tag);
  if (className) el.className = className;
  if (text) el.textContent = text;
  return el;
}

// Создаёт блок с иконкой и числом
function createIconWithCount(iconClass, count, title) {
  const wrapper = createElem('div', 'icon-item');
  wrapper.title = title;
  const icon = createElem('i', `icon ${iconClass}`);
  const countSpan = createElem('span');
  countSpan.textContent = count;
  wrapper.append(icon, countSpan);
  return wrapper;
}

// Создаёт блок рейтинга с подписью и числовым значением справа
function createRatingBlock(label, rating, solutionID, ratingType) {
  const block = createElem('div', 'rating-block');
  const labelElem = createElem('span', 'rating-label', label);
  const isLoggedIn = localStorage.getItem('isLoggedIn') === 'true';
  if (isLoggedIn) {
    const starsElem = createInteractiveStars(solutionID, ratingType);
    block.append(labelElem, starsElem);
  } else {
    const authMsg = createElem('span', 'rating-auth-message', 'Оценивать могут только авторизованные пользователи');
    block.append(labelElem, authMsg);
  }
  const valueElem = createElem('span', 'rating-value', rating.toString());
  block.appendChild(valueElem);
  return block;
}

// Создаёт комментарий с лайками/дизлайками
function createComment(comment) {
  const commentDiv = createElem('div', 'comment');

  const textDiv = createElem('div', 'comment-text');
  textDiv.innerHTML = `<b>${comment.Creator.User}</b> (${comment.CreatedDate}): ${comment.Text}`;

  const votesDiv = createElem('div', 'comment-votes');

  // Лайк и дизлайк иконки
  const likeBtn = createElem('button', 'like-btn');
  likeBtn.innerHTML = `<i class="fas fa-thumbs-up icon" aria-hidden="true"></i>${comment.LikeCount}`;

  const unlikeBtn = createElem('button', 'unlike-btn');
  unlikeBtn.innerHTML = `<i class="fas fa-thumbs-down icon" aria-hidden="true"></i>${comment.NotLikeCount}`;

  votesDiv.append(likeBtn, unlikeBtn);
  commentDiv.append(textDiv, votesDiv);

  return commentDiv;
}

function getParameterByName(name) {
  if (name === 'solutionId' || name === 'id') {
    const pathMatch = window.location.pathname.match(/\/solution\/(\d+)/);
    if (pathMatch) return pathMatch[1];
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('solutionId') || urlParams.get('id');
  }

  const url = window.location.href;
  const regex = new RegExp('[?&]' + name + '(=([^&#]*)|&|#|$)');
  const results = regex.exec(url);
  if (!results) return null;
  if (!results[2]) return '';
  return decodeURIComponent(results[2].replace(/\+/g, ' '));
}

function createInteractiveStars(solutionID, ratingType) {
  const container = createElem('div', 'interactive-stars');
  container.title = 'Ваш рейтинг';

  const stars = [];
  let savedRating = 0;
  let hoverRating = 0;
  let isLoading = true;

  // Загружаем сохраненную оценку пользователя с сервера асинхронно
  (async () => {
    try {
      const token = localStorage.getItem('accessToken');
      if (token && token !== 'null' && token !== 'undefined') {
        const response = await fetch(API_CONFIG.buildURL(`/solutions/${solutionID}/rating`), {
          method: 'GET',
          headers: getAuthHeaders(),
          credentials: 'include'
        });
        
        if (response.ok) {
          const data = await response.json();
          if (data.ratings && data.ratings[ratingType]) {
            savedRating = data.ratings[ratingType];
            updateStars();
          }
        }
      }
    } catch (error) {
      console.error('Ошибка загрузки оценки:', error);
    } finally {
      isLoading = false;
      updateStars();
    }
  })();

  for (let i = 1; i <= 5; i++) {
    const star = createElem('span', 'star');
    star.textContent = '☆';
    star.style.cursor = 'pointer';
    star.style.fontSize = '24px';
    star.style.transition = 'color 0.3s, transform 0.3s';

    star.addEventListener('mouseenter', () => {
      if (!isLoading) {
        hoverRating = i;
        updateStars();
      }
    });

    star.addEventListener('click', async () => {
      if (isLoading) return;
      
      const newRating = i;
      savedRating = newRating;
      updateStars();
      
      try {
        const response = await fetch(API_CONFIG.buildURL(`/solutions/${solutionID}/rating`), {
          method: 'POST',
          headers: getAuthHeaders(),
          credentials: 'include',
          body: JSON.stringify({
            rating_type: ratingType,
            rating_value: newRating
          })
        });
        
        if (response.ok) {
          const data = await response.json();
          // Обновляем общий рейтинг на странице, если нужно
          console.log('Оценка сохранена:', data);
        } else {
          const error = await response.json().catch(() => ({}));
          if (response.status === 401) {
            localStorage.setItem('isLoggedIn', 'false');
            alert('Необходимо авторизоваться для оценки');
          } else {
            alert('Не удалось сохранить оценку: ' + (error.error || 'Неизвестная ошибка'));
          }
          console.error('Ошибка сохранения оценки:', error);
          savedRating = 0;
          updateStars();
        }
      } catch (error) {
        console.error('Ошибка отправки оценки:', error);
        alert('Ошибка при сохранении оценки');
        // Откатываем визуальное изменение
        savedRating = 0;
        updateStars();
      }
    });

    container.appendChild(star);
    stars.push(star);
  }

  container.addEventListener('mouseleave', () => {
    hoverRating = 0;
    updateStars();
  });

  function updateStars() {
    const activeRating = hoverRating || savedRating;
    stars.forEach((star, idx) => {
      if (idx < activeRating) {
        star.textContent = '★';
        star.style.color = 'red';
        star.style.transform = 'scale(1.2)';
      } else {
        star.textContent = '☆';
        star.style.color = 'lightgray';
        star.style.transform = 'scale(1)';
      }
    });
  }

  // Инициализируем звезды сразу
  updateStars();

  return container;
}

// Функция для создания полной карточки решения (аналогично solutions.html)
function createSolutionCard(item) {
  const card = createElem('article', 'card');
  
  // Обертка для изображения
  const imageWrapper = createElem('div', 'card-image-wrapper');
  
  // Ссылка на изображение
  const imageLink = createElem('a', 'card-title-link');
  imageLink.href = `/solution/${item.ID}`;
  
  const cardImg = createElem('img', 'card-image');
  cardImg.loading = 'lazy';

  function getImageFromInternet(solutionName) {
    if (!solutionName || solutionName.trim() === '') {
      return null;
    }
    
    let hash = 0;
    for (let i = 0; i < solutionName.length; i++) {
      const char = solutionName.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash;
    }
    
    const imageId = Math.abs(hash) % 1000;
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

  const norm = window.normalizeImageSrc || ((raw) => raw ? (window.assetUrl ? window.assetUrl(raw) : raw) : null);

  if (item.Image && item.Image.trim() !== '' && item.Image !== '../images/default.png') {
    cardImg.src = norm(item.Image);
    cardImg.alt = item.Name || 'Решение';
    cardImg.style.display = 'block';
    cardImg.onerror = function() {
      const internetImage = getImageFromInternet(item.Name);
      if (internetImage) {
        this.src = internetImage;
      } else {
        this.style.display = 'none';
      }
    };
  } else {
    const internetImage = getImageFromInternet(item.Name);
    if (internetImage) {
      cardImg.src = internetImage;
      cardImg.style.display = 'block';
      cardImg.onerror = function() { this.style.display = 'none'; };
    } else {
      cardImg.style.display = 'none';
    }
  }
  
  imageLink.appendChild(cardImg);
  imageWrapper.appendChild(imageLink);
  
  // Overlay для названия
  const titleOverlay = createElem('div', 'card-title-overlay');
  imageWrapper.appendChild(titleOverlay);
  
  // Название решения
  const cardTitleText = createElem('a', 'card-title-text');
  cardTitleText.href = `/solution/${item.ID}`;
  cardTitleText.textContent = item.Name || 'Решение';
  imageWrapper.appendChild(cardTitleText);
  
  // Избранное
  const cardFavorites = createElem('div', 'card-favorites');
  const favoriteIcon = createElem('i', 'fas fa-heart favorite-icon');
  favoriteIcon.setAttribute('aria-label', 'Избранное');
  setFavoriteIconState(favoriteIcon, item.IsFavourite);
  favoriteIcon.style.cursor = 'pointer';
  const favoriteCount = createElem('span', 'favorite-count');
  favoriteCount.textContent = item.Favourite || 0;
  cardFavorites.appendChild(favoriteIcon);
  cardFavorites.appendChild(favoriteCount);
  
  // Обработчик избранного
  favoriteIcon.addEventListener('click', async (e) => {
    e.preventDefault();
    e.stopPropagation();
    await toggleSolutionFavoriteForCard(item.ID, favoriteIcon, favoriteCount);
  });
  
  imageWrapper.appendChild(cardFavorites);
  
  // Кнопка корзины
  const cartBtn = createElem('button', 'card-cart-btn');
  cartBtn.title = 'Добавить в корзину';
  const cartIcon = createElem('i', 'fas fa-shopping-basket icon');
  cartBtn.appendChild(cartIcon);
  
  cartBtn.addEventListener('click', async (e) => {
    e.preventDefault();
    e.stopPropagation();
    await handleAddToCartForCard(item.ID, cartBtn, cartIcon);
  });
  
  // Проверяем, есть ли уже в корзине
  checkInCart(item.ID).then(inCart => {
    if (inCart) {
      cartBtn.classList.add('in-cart');
      cartBtn.title = 'Уже в корзине';
      cartIcon.classList.add('cart-in-cart');
    } else {
      cartIcon.classList.remove('cart-in-cart');
    }
  });
  
  imageWrapper.appendChild(cartBtn);
  
  // Рейтинг
  const rating = createElem('div', 'rating');
  const ratingNumber = createElem('span', 'rating-number');
  ratingNumber.textContent = item.Rating || 0;
  rating.appendChild(ratingNumber);
  imageWrapper.appendChild(rating);
  
  card.appendChild(imageWrapper);
  
  // Контент карточки
  const cardContent = createElem('div', 'card-content');
  
  // Тема проблемы
  const problemTopic = createElem('div', 'problem-topic');
  problemTopic.style.display = 'none';
  if (item.Problems && Array.isArray(item.Problems) && item.Problems.length > 0) {
    const topicsMap = new Map();
    item.Problems.forEach(problem => {
      if (problem.TopicInfo && problem.TopicInfo.Name) {
        const topicId = problem.TopicInfo.ID;
        if (!topicsMap.has(topicId)) {
          topicsMap.set(topicId, problem.TopicInfo);
        }
      }
    });
    
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
      problemTopic.appendChild(topicLink);
      problemTopic.style.display = 'block';
    }
  }
  cardContent.appendChild(problemTopic);
  
  // Теги
  const tagsWrapper = createElem('div', 'tags-wrapper');
  const tagsColumn = createElem('div', 'tags-column');
  if (item.Problems && Array.isArray(item.Problems) && item.Problems.length > 0) {
    item.Problems.forEach(problem => {
      if (problem.Hashtags && Array.isArray(problem.Hashtags) && problem.Hashtags.length > 0) {
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
  tagsWrapper.appendChild(tagsColumn);
  cardContent.appendChild(tagsWrapper);
  
  // Футер со статистикой
  const cardFooter = createElem('div', 'card-footer');
  
  // Просмотры
  const statViews = createElem('div', 'stat-item views');
  const statIconViews = createElem('div', 'stat-icon');
  statIconViews.title = 'Просмотры';
  const iconViews = createElem('i', 'fas fa-eye');
  statIconViews.appendChild(iconViews);
  const statValueViews = createElem('div', 'stat-value');
  statValueViews.textContent = item.Show || 0;
  statViews.appendChild(statIconViews);
  statViews.appendChild(statValueViews);
  cardFooter.appendChild(statViews);
  
  // Комментарии
  const statComments = createElem('div', 'stat-item comments');
  const statIconComments = createElem('div', 'stat-icon');
  statIconComments.title = 'Подтверждения';
  const iconComments = createElem('i', 'fas fa-check');
  statIconComments.appendChild(iconComments);
  const statValueComments = createElem('div', 'stat-value');
  statValueComments.textContent = (item.CommentSolutions && item.CommentSolutions.length) || (item.Comments && item.Comments.length) || 0;
  statComments.appendChild(statIconComments);
  statComments.appendChild(statValueComments);
  cardFooter.appendChild(statComments);
  
  // Ссылки
  const statShares = createElem('div', 'stat-item shares');
  const statIconShares = createElem('div', 'stat-icon');
  statIconShares.title = 'Ссылки';
  const iconShares = createElem('i', 'fas fa-link');
  statIconShares.appendChild(iconShares);
  const statValueShares = createElem('div', 'stat-value');
  statValueShares.textContent = item.Reply || 0;
  statShares.appendChild(statIconShares);
  statShares.appendChild(statValueShares);
  cardFooter.appendChild(statShares);
  
  // Линки (связанные решения)
  const statLinks = createElem('div', 'stat-item links');
  const statIconLinks = createElem('div', 'stat-icon');
  statIconLinks.title = 'Линки';
  const iconLinks = createElem('i', 'fas fa-link');
  statIconLinks.appendChild(iconLinks);
  const statValueLinks = createElem('div', 'stat-value');
  statValueLinks.textContent = item.LinkedSolutionsCount || item.LinkedSolutions?.length || 0;
  statLinks.appendChild(statIconLinks);
  statLinks.appendChild(statValueLinks);
  cardFooter.appendChild(statLinks);
  
  cardContent.appendChild(cardFooter);
  card.appendChild(cardContent);
  
  return card;
}

// Функция для добавления в корзину (для карточек)
async function handleAddToCartForCard(solutionId, button, icon) {
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

// Функция для переключения избранного (для карточек)
async function toggleSolutionFavoriteForCard(solutionId, iconElement, countElement) {
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

async function renderSolutionPage() {
  const solutionID = getParameterByName("solutionId");  // Уже правильно
  if (!solutionID) {
    const container = document.getElementById('solutionContainer');
    if (container) {
      container.innerHTML = '<p style="color:red; text-align:center; padding:20px;">Отсутствует параметр solutionId в URL</p>';
    }
    return;
  }
  
  const container = document.getElementById('solutionContainer');
  if (!container) {
    console.error('Контейнер solutionContainer не найден');
    return;
  }
  
  // Показываем индикатор загрузки
  container.innerHTML = '<p style="text-align:center; padding:20px;">Загрузка решения...</p>';
  
  try {
    // Используйте решение по ID
    const response = await fetch(API_CONFIG.buildURL(API_CONFIG.ENDPOINTS.SOLUTION_BY_ID(solutionID)));
    
    if (!response.ok) {
      let errorMessage = 'Не удалось загрузить решение';
      let errorDetails = '';
      
      // Пытаемся получить детали ошибки от сервера
      try {
        const errorData = await response.json().catch(() => ({}));
        if (errorData.error) {
          errorDetails = errorData.error;
        } else if (errorData.details) {
          errorDetails = errorData.details;
        }
      } catch (e) {
        // Игнорируем ошибку парсинга JSON
      }
      
      if (response.status === 404) {
        errorMessage = 'Решение не найдено';
      } else if (response.status === 500) {
        errorMessage = 'Ошибка сервера при загрузке решения. Попробуйте обновить страницу.';
        console.error('Ошибка 500 при загрузке решения:', solutionID);
        if (errorDetails) {
          console.error('Детали ошибки сервера:', errorDetails);
        }
      } else if (response.status === 401) {
        errorMessage = 'Требуется авторизация для просмотра решения';
      } else {
        errorMessage = `Ошибка загрузки (код: ${response.status})`;
        if (errorDetails) {
          errorMessage += `: ${errorDetails}`;
        }
      }
      
      const errorHtml = `<p style="color:red; text-align:center; padding:20px;">
        <strong>${errorMessage}</strong>
        ${errorDetails ? `<br><small style="color:#666;">${errorDetails}</small>` : ''}
        <br><br>
        <button onclick="window.location.reload()" style="padding:8px 16px; background:#667eea; color:white; border:none; border-radius:8px; cursor:pointer;">
          Обновить страницу
        </button>
      </p>`;
      
      container.innerHTML = errorHtml;
      return;
    }

    const solution = await response.json();

    container.innerHTML = '';

    if (!solution) {
      container.textContent = 'Решение не найдено.';
      return;
    }

    // Обновляем SEO мета-теги
    const baseUrl = window.location.origin;
    const solutionUrl = `/solution/${solution.ID}`;
    const solutionImage = solution.Image || 'assets/og-image.png';
    
    updateSEOMetaTags({
        title: `${solution.Name} - Всё Прост`,
        description: solution.Details || `Решение: ${solution.Name}. Подробное описание на платформе Всё Прост (VseProst, ВсеПрост, Все Просто, ВсёПрост).`,
        image: solutionImage,
        url: solutionUrl,
        type: 'article'
    });

    // Добавляем структурированные данные
    addStructuredData(createSolutionStructuredData(solution));

    // Верхний блок с заголовком и иконками - в одной строке
    const headerRow = createElem('div', 'header-row');

  const title = createElem('h1', 'solution-title', solution.Name);
  headerRow.appendChild(title);

  // Блок иконок (top-block)
  const topBlock = createElem('div', 'top-block');
  topBlock.style.margin = '0'; // убираем внешние отступы, если нужно

  // Кнопка добавления в корзину (как иконка, перед остальными)
  const cartButton = createElem('button', 'icon-item');
  cartButton.style.cursor = 'pointer';
  cartButton.title = 'Добавить в корзину';
  const cartIcon = createElem('i', 'fas fa-shopping-basket icon');
  cartButton.appendChild(cartIcon);
  
  // Функция для установки зеленого цвета иконки корзины
  const setCartIconGreen = (button) => {
    button.classList.add('in-cart');
    const icon = button.querySelector('i');
    if (icon) {
      icon.classList.add('cart-in-cart');
    }
  };
  
  cartButton.addEventListener('click', async () => {
    const result = await addToCart(solutionID);
    if (result.success) {
      cartButton.title = 'В корзине';
      cartButton.disabled = true;
      setCartIconGreen(cartButton);
      // Обновляем бейдж корзины в header
      await updateCartIconState();
      alert(result.message || 'Решение добавлено в корзину');
    } else {
      alert(result.error || 'Не удалось добавить в корзину');
    }
  });
  
  // Проверяем, есть ли уже в корзине
  checkInCart(solutionID).then(inCart => {
    if (inCart) {
      cartButton.title = 'В корзине';
      cartButton.disabled = true;
      setCartIconGreen(cartButton);
    }
  });
  
  topBlock.appendChild(cartButton);
  topBlock.appendChild(createIconWithCount('fas fa-eye', solution.Show, 'Просмотры'));
  
  // Создаем иконку избранного с возможностью клика (только для авторизованных)
  const favoriteIconWrapper = createIconWithCount('fas fa-heart', solution.Favourite, 'Избранное');
  const favoriteIcon = favoriteIconWrapper.querySelector('.icon');
  setFavoriteIconState(favoriteIcon, solution.IsFavourite);

  if (localStorage.getItem('isLoggedIn') === 'true') {
    favoriteIconWrapper.style.cursor = 'pointer';
    const favoriteCount = favoriteIconWrapper.querySelector('span');
    favoriteIconWrapper.addEventListener('click', async (e) => {
      e.preventDefault();
      e.stopPropagation();
      await toggleSolutionFavorite(solutionID, favoriteIcon, favoriteCount);
    });
  }

  topBlock.appendChild(favoriteIconWrapper);
  
  // Кнопка для добавления похожих решений (только для авторизованных)
  const linkButton = createIconWithCount('fas fa-link', solution.Reply, 'Ссылки');
  if (localStorage.getItem('isLoggedIn') === 'true') {
    linkButton.style.cursor = 'pointer';
    linkButton.addEventListener('click', () => {
      openLinkedSolutionModal(solutionID);
    });
  }
  topBlock.appendChild(linkButton);

  headerRow.appendChild(topBlock);
  container.appendChild(headerRow);

  // Основной блок с картинкой слева и описанием справа
  const mainBlock = createElem('div', 'main-block');

  const img = createElem('img');
  img.src = (window.normalizeImageSrc || ((x) => x))(solution.Image);
  img.alt = solution.Name;
  img.className = 'solution-image';
  
  // Добавляем обработчик клика для открытия модального окна
  img.addEventListener('click', () => {
    const imageSrc = img.src;
    const imageAlt = img.alt || solution.Name || 'Решение';
    // Пропускаем SVG изображения
    if (imageSrc && !imageSrc.startsWith('data:image/svg+xml')) {
      openImageViewer(imageSrc, imageAlt);
    }
  });
  
  mainBlock.appendChild(img);

  // Описание + рейтинги в одном блоке справа от картинки
  const descAndRatings = createElem('div', 'desc-and-ratings');

  const desc = createElem('p', 'solution-description', solution.Describe);
  descAndRatings.appendChild(desc);

  const ratingsWrapper = createElem('div', 'ratings-wrapper');
  ratingsWrapper.appendChild(createRatingBlock('Цена', solution.Price, solutionID, 'price'));
  ratingsWrapper.appendChild(createRatingBlock('Эффективность', solution.Efficiency, solutionID, 'efficiency'));
  ratingsWrapper.appendChild(createRatingBlock('Сложность', solution.Complexity, solutionID, 'complexity'));
  ratingsWrapper.appendChild(createRatingBlock('Время', solution.Time, solutionID, 'time'));
  descAndRatings.appendChild(ratingsWrapper);

  mainBlock.appendChild(descAndRatings);
  container.appendChild(mainBlock);

  // Блок комментариев с возможностью сворачивания
  const commentsSection = createElem('div', 'comments-section');
  
  const commentsCount = (solution.CommentSolutions && solution.CommentSolutions.length) || 0;
  const commentsHeader = createElem('div', 'section-header');
  const commentsTitle = createElem('h2', 'comments-title', `Комментарии (${commentsCount})`);
  const commentsToggle = createElem('button', 'toggle-btn', '▶');
  commentsToggle.title = 'Свернуть/Развернуть';
  commentsHeader.appendChild(commentsTitle);
  commentsHeader.appendChild(commentsToggle);
  commentsSection.appendChild(commentsHeader);

  const commentsContent = createElem('div', 'section-content');
  commentsContent.style.display = 'none'; // По умолчанию скрыт

  if (Array.isArray(solution.CommentSolutions) && solution.CommentSolutions.length > 0) {
    solution.CommentSolutions.forEach(comment => {
      commentsContent.appendChild(createComment(comment));
    });
  } else {
    const noComments = createElem('p', 'no-comments', 'Комментариев пока нет.');
    commentsContent.appendChild(noComments);
  }

  // Поле для нового комментария (только для авторизованных)
  const isLoggedIn = localStorage.getItem('isLoggedIn') === 'true';
  if (isLoggedIn) {
    const commentForm = createElem('form', 'comment-form');

    const textarea = document.createElement('textarea');
    textarea.placeholder = 'Напишите свой комментарий';
    textarea.rows = 3;

    const submitBtn = createElem('button', null, 'Отправить');
    submitBtn.type = 'submit';

    commentForm.append(textarea, submitBtn);
    commentsContent.appendChild(commentForm);

    // Обработка отправки комментария
    commentForm.addEventListener('submit', e => {
      e.preventDefault();
      if (!textarea.value.trim()) return alert('Введите текст комментария');
      const newComment = {
        date: new Date().toLocaleDateString('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' }),
        author: 'Пользователь',
        text: textarea.value.trim(),
        likes: 0,
        unlikes: 0
      };
      if (!Array.isArray(solution.comments)) {
        solution.comments = [];
      }
      solution.comments.push(newComment);
      commentsContent.insertBefore(createComment(newComment), commentForm);
      const newCount = (solution.CommentSolutions?.length || 0) + (solution.comments?.length || 0);
      if (commentsTitle) commentsTitle.textContent = `Комментарии (${newCount})`;
      textarea.value = '';
    });
  } else {
    const authMsg = createElem('p', 'auth-required-message', 'Комментарии могут оставлять только авторизованные пользователи.');
    commentsContent.appendChild(authMsg);
  }

  // Обработчик сворачивания/разворачивания комментариев
  let commentsExpanded = false;
  commentsToggle.addEventListener('click', () => {
    commentsExpanded = !commentsExpanded;
    commentsContent.style.display = commentsExpanded ? 'block' : 'none';
    commentsToggle.textContent = commentsExpanded ? '▼' : '▶';
  });

  commentsSection.appendChild(commentsContent);
  container.appendChild(commentsSection);

  // Блок похожих решений с возможностью сворачивания
  const linkedSolutionsSection = createElem('div', 'linked-solutions-section');
  
  const linkedSolutions = solution.LinkedSolutions || [];
  const linkedSolutionsHeader = createElem('div', 'section-header');
  const linkedSolutionsTitle = createElem('h2', 'linked-solutions-title', `Похожие решения (${linkedSolutions.length})`);
  const linkedSolutionsToggle = createElem('button', 'toggle-btn', '▶');
  linkedSolutionsToggle.title = 'Свернуть/Развернуть';
  linkedSolutionsHeader.appendChild(linkedSolutionsTitle);
  linkedSolutionsHeader.appendChild(linkedSolutionsToggle);
  linkedSolutionsSection.appendChild(linkedSolutionsHeader);

  const linkedSolutionsContent = createElem('div', 'section-content linked-solutions-content');
  linkedSolutionsContent.style.display = 'none'; // По умолчанию скрыт

  const linkedSolutionsList = linkedSolutions;
  if (linkedSolutionsList.length > 0) {
    const linkedSolutionsContainer = createElem('div', 'cards-container');
    
    linkedSolutionsList.forEach(linkedSolution => {
      const card = createSolutionCard(linkedSolution);
      linkedSolutionsContainer.appendChild(card);
    });
    
    linkedSolutionsContent.appendChild(linkedSolutionsContainer);
    
    // Инициализируем прокрутку тегов для похожих решений
    setTimeout(() => {
      initTagsScroll();
    }, 100);
  } else {
    const noLinkedSolutions = createElem('p', 'no-linked-solutions', 'Похожих решений пока нет.');
    linkedSolutionsContent.appendChild(noLinkedSolutions);
  }

  // Обработчик сворачивания/разворачивания похожих решений
  let linkedSolutionsExpanded = false;
  linkedSolutionsToggle.addEventListener('click', () => {
    linkedSolutionsExpanded = !linkedSolutionsExpanded;
    linkedSolutionsContent.style.display = linkedSolutionsExpanded ? 'block' : 'none';
    linkedSolutionsToggle.textContent = linkedSolutionsExpanded ? '▼' : '▶';
  });

  linkedSolutionsSection.appendChild(linkedSolutionsContent);
  container.appendChild(linkedSolutionsSection);
  
  } catch (error) {
    console.error('Ошибка при отображении решения:', error);
    const container = document.getElementById('solutionContainer');
    if (container) {
      container.innerHTML = `<p style="color:red; text-align:center; padding:20px;">Ошибка при загрузке решения: ${error.message || 'Неизвестная ошибка'}</p>`;
    }
  }
}


// Переменные для модального окна похожих решений
let selectedLinkedSolutionsList = [];
let currentSolutionId = null;

// Переключение избранного для решений
async function toggleSolutionFavorite(solutionId, iconElement, countElement) {
  if (!iconElement || iconElement.dataset.pending === '1') {
    return;
  }
  iconElement.dataset.pending = '1';
  iconElement.style.pointerEvents = 'none';
  const wrapper = iconElement.closest('.icon-item');
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
          // Обновляем счетчик
          if (countElement) {
            const currentCount = parseInt(countElement.textContent) || 0;
            countElement.textContent = data.is_favourite ? currentCount + 1 : Math.max(0, currentCount - 1);
          }
          // Обновляем иконку
          setFavoriteIconState(iconElement, data.is_favourite);
        }
      }
    } else if (response.ok) {
      const data = await response.json();
      // Обновляем счетчик
      if (countElement) {
        const currentCount = parseInt(countElement.textContent) || 0;
        countElement.textContent = data.is_favourite ? currentCount + 1 : Math.max(0, currentCount - 1);
      }
      // Обновляем иконку
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

// Функции для работы с модальным окном похожих решений
function openLinkedSolutionModal(solutionId) {
  currentSolutionId = solutionId;
  selectedLinkedSolutionsList = [];
  const modalOverlay = document.getElementById('linked-solution-modal-overlay');
  const modal = document.getElementById('linked-solution-modal');
  if (modalOverlay && modal) {
    modalOverlay.classList.add('active');
    document.body.style.overflow = 'hidden';
    updateSelectedLinkedSolutions();
    const searchInput = document.getElementById('linkedSolutionSearch');
    if (searchInput) {
      searchInput.value = '';
      searchInput.focus();
    }
  }
}

function closeLinkedSolutionModal() {
  const modalOverlay = document.getElementById('linked-solution-modal-overlay');
  if (modalOverlay) {
    modalOverlay.classList.remove('active');
    document.body.style.overflow = '';
  }
  selectedLinkedSolutionsList = [];
  currentSolutionId = null;
  const searchInput = document.getElementById('linkedSolutionSearch');
  const dropdown = document.getElementById('linkedSolutionDropdown');
  if (searchInput) searchInput.value = '';
  if (dropdown) dropdown.style.display = 'none';
  updateSelectedLinkedSolutions();
}

function updateSelectedLinkedSolutions() {
  const container = document.getElementById('selectedLinkedSolutions');
  if (!container) return;
  
  container.innerHTML = '';
  selectedLinkedSolutionsList.forEach(solution => {
    const div = document.createElement('div');
    div.className = 'selected-solution';
    div.innerHTML = `${solution.title} <span class="remove" data-id="${solution.id}">×</span>`;
    container.appendChild(div);
  });
}

// Инициализация обработчиков модального окна
document.addEventListener('DOMContentLoaded', () => {
  const modalOverlay = document.getElementById('linked-solution-modal-overlay');
  const closeBtn = document.getElementById('closeLinkedSolutionModal');
  const clearBtn = document.getElementById('clearLinkedSolutionBtn');
  const saveBtn = document.getElementById('saveLinkedSolutionBtn');
  const searchInput = document.getElementById('linkedSolutionSearch');
  const dropdown = document.getElementById('linkedSolutionDropdown');
  const selectedContainer = document.getElementById('selectedLinkedSolutions');

  // Закрытие модального окна
  if (closeBtn) {
    closeBtn.addEventListener('click', closeLinkedSolutionModal);
  }

  if (modalOverlay) {
    modalOverlay.addEventListener('click', (e) => {
      if (e.target === modalOverlay) {
        closeLinkedSolutionModal();
      }
    });
  }

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && modalOverlay && modalOverlay.classList.contains('active')) {
      closeLinkedSolutionModal();
    }
  });

  // Очистка выбранных решений
  if (clearBtn) {
    clearBtn.addEventListener('click', () => {
      selectedLinkedSolutionsList = [];
      updateSelectedLinkedSolutions();
      if (searchInput) searchInput.value = '';
      if (dropdown) dropdown.style.display = 'none';
    });
  }

  // Поиск решений
  if (searchInput && dropdown) {
    let searchTimeout;
    searchInput.addEventListener('input', async (e) => {
      const query = e.target.value.trim();
      
      // Очищаем предыдущий таймаут
      clearTimeout(searchTimeout);
      
      if (query.length < 2) {
        dropdown.style.display = 'none';
        return;
      }

      // Задержка перед поиском (debounce)
      searchTimeout = setTimeout(async () => {
        try {
          const token = localStorage.getItem('accessToken');
          let url = `/api/solutions?search=${encodeURIComponent(query)}&limit=10`;
          if (currentSolutionId) {
            url += `&exclude=${currentSolutionId}`;
          }
          
          const response = await fetch(url, {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            }
          });
          
          if (response.ok) {
            const solutions = await response.json();
            dropdown.innerHTML = '';
            
            // Фильтруем решения: исключаем текущее и уже выбранные
            const filteredSolutions = solutions.filter(solution => {
              if (currentSolutionId && solution.ID === currentSolutionId) return false;
              if (selectedLinkedSolutionsList.some(s => s.id === solution.ID)) return false;
              return true;
            });
            
            if (filteredSolutions.length === 0) {
              dropdown.innerHTML = '<div class="dropdown-item">Решения не найдены</div>';
            } else {
              filteredSolutions.forEach(solution => {
                const div = document.createElement('div');
                div.className = 'dropdown-item';
                div.textContent = solution.Name || 'Без названия';
                div.setAttribute('data-id', solution.ID);
                
                div.addEventListener('click', () => {
                  selectedLinkedSolutionsList.push({
                    id: solution.ID,
                    title: solution.Name || 'Без названия'
                  });
                  updateSelectedLinkedSolutions();
                  searchInput.value = '';
                  dropdown.style.display = 'none';
                });
                
                dropdown.appendChild(div);
              });
            }
            
            dropdown.style.display = 'block';
          } else {
            dropdown.style.display = 'none';
          }
        } catch (error) {
          console.error('Ошибка поиска решений:', error);
          dropdown.style.display = 'none';
        }
      }, 300); // Задержка 300мс
    });
  }

  // Удаление выбранного решения
  if (selectedContainer) {
    selectedContainer.addEventListener('click', (e) => {
      if (e.target.classList.contains('remove')) {
        const id = parseInt(e.target.dataset.id);
        selectedLinkedSolutionsList = selectedLinkedSolutionsList.filter(s => s.id !== id);
        updateSelectedLinkedSolutions();
      }
    });
  }

  // Сохранение связей
  if (saveBtn) {
    saveBtn.addEventListener('click', async () => {
      if (selectedLinkedSolutionsList.length === 0) {
        alert('Выберите хотя бы одно решение для связи');
        return;
      }

      if (!currentSolutionId) {
        alert('Ошибка: не указано текущее решение');
        return;
      }

      try {
        const token = localStorage.getItem('accessToken');
        let successCount = 0;
        let errorCount = 0;

        for (const linkedSolution of selectedLinkedSolutionsList) {
          try {
            const response = await fetch(API_CONFIG.buildURL(`/solutions/${currentSolutionId}/link`), {
              method: 'POST',
              headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
              },
              body: JSON.stringify({
                linked_solution_id: linkedSolution.id
              })
            });

            if (response.ok) {
              successCount++;
            } else {
              const error = await response.json();
              console.error(`Ошибка добавления связи с решением ${linkedSolution.id}:`, error);
              errorCount++;
            }
          } catch (error) {
            console.error(`Ошибка при добавлении связи с решением ${linkedSolution.id}:`, error);
            errorCount++;
          }
        }

        if (successCount > 0) {
          alert(`Успешно добавлено связей: ${successCount}${errorCount > 0 ? `, ошибок: ${errorCount}` : ''}`);
          closeLinkedSolutionModal();
          // Перезагружаем страницу для обновления данных
          window.location.reload();
        } else {
          alert(`Не удалось добавить связи. Ошибок: ${errorCount}`);
        }
      } catch (error) {
        console.error('Ошибка сохранения связей:', error);
        alert('Ошибка при сохранении связей');
      }
    });
  }

  // Скрытие dropdown при клике вне
  document.addEventListener('click', (e) => {
    if (searchInput && dropdown && 
        !searchInput.contains(e.target) && 
        !dropdown.contains(e.target)) {
      dropdown.style.display = 'none';
    }
  });
});

// Обработка ошибок при загрузке страницы
renderSolutionPage().catch(error => {
  console.error('Критическая ошибка при загрузке страницы решения:', error);
  const container = document.getElementById('solutionContainer');
  if (container) {
    container.innerHTML = `<p style="color:red; text-align:center; padding:20px;">Произошла ошибка при загрузке страницы. Пожалуйста, обновите страницу или вернитесь на главную.</p>`;
  }
}).finally(function () {
  if (typeof window.__showSolutionPage === 'function') window.__showSolutionPage();
});

// Обновляем бейдж корзины при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
  updateCartIconState();
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
