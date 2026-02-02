// cart.js
import * as auth from './authorizationFunctions.js';
import { updateCartIconState } from './cartFunctions.js';

let cartItems = [];

// Загрузка корзины
async function loadCart() {
  const container = document.getElementById('cart-items-container');
  const emptyState = document.getElementById('cart-empty');
  
  if (!container) return;
  
  container.innerHTML = 'Загрузка...';

  try {
    // Проверяем аутентификацию
    await auth.checkAuth(true);
  } catch (error) {
    container.innerHTML = '<p style="color:red; text-align:center">Требуется авторизация</p>';
    return;
  }

  try {
    const token = localStorage.getItem('accessToken');
    const response = await fetch(API_CONFIG.buildURL(API_CONFIG.ENDPOINTS.CART), {
      method: 'GET',
      credentials: 'include',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });

    // Если получили 401, пробуем обновить токен
    if (response.status === 401) {
      try {
        await auth.refreshToken();
        const newToken = localStorage.getItem('accessToken');
        const retryResponse = await fetch(API_CONFIG.buildURL(API_CONFIG.ENDPOINTS.CART), {
          method: 'GET',
          credentials: 'include',
          headers: {
            'Authorization': `Bearer ${newToken}`,
            'Content-Type': 'application/json'
          }
        });
        
        if (retryResponse.status === 401) {
          throw new Error('Требуется авторизация');
        }
        
        if (!retryResponse.ok) {
          throw new Error('Ошибка HTTP: ' + retryResponse.status);
        }
        
        cartItems = await retryResponse.json();
        renderCart();
        updateCartCount();
        // Обновляем состояние иконки корзины в header
        await updateCartIconState();
        return;
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

    cartItems = await response.json();
    renderCart();
    updateCartCount();
    // Обновляем состояние иконки корзины в header
    await updateCartIconState();

  } catch (error) {
    console.error('Ошибка загрузки корзины:', error);
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

// Отображение корзины
function renderCart() {
  const container = document.getElementById('cart-items-container');
  const emptyState = document.getElementById('cart-empty');
  
  if (!container) return;

  if (cartItems.length === 0) {
    container.style.display = 'none';
    if (emptyState) emptyState.style.display = 'block';
    return;
  }

  container.style.display = 'block';
  if (emptyState) emptyState.style.display = 'none';
  container.innerHTML = '';

  const template = document.getElementById('cart-item-template');
  if (!template) {
    console.error('Шаблон карточки не найден!');
    return;
  }

  cartItems.forEach(item => {
    const card = template.content.cloneNode(true);
    
    // Ссылка на решение
    const link = card.querySelector('.cart-item-link');
    if (link) {
      link.href = `/html/solution.html?solutionId=${encodeURIComponent(item.ID)}`;
    }
    
    const titleLink = card.querySelector('.cart-item-title');
    if (titleLink) {
      titleLink.href = `/html/solution.html?solutionId=${encodeURIComponent(item.ID)}`;
      titleLink.textContent = item.Name || 'Без названия';
    }

    // Информация о проблеме
    const problemLink = card.querySelector('.problem-link');
    if (problemLink && item.Problem) {
      problemLink.href = `/html/problem.html?problemId=${encodeURIComponent(item.Problem.ID)}`;
      problemLink.textContent = item.Problem.Name || 'Не указана';
    } else if (problemLink) {
      problemLink.textContent = 'Не указана';
      problemLink.style.color = '#999';
      problemLink.style.pointerEvents = 'none';
    }

    // Статус покупки
    const statusBadge = card.querySelector('.status-badge');
    if (statusBadge) {
      if (item.IsBought) {
        statusBadge.textContent = 'Куплено';
        statusBadge.className = 'status-badge bought';
      } else {
        statusBadge.textContent = 'Не куплено';
        statusBadge.className = 'status-badge not-bought';
      }
    }

    // Изображение
    const img = card.querySelector('.cart-item-img');
    if (img) {
      img.src = item.Image || '../images/default.png';
      img.alt = item.Name || 'Решение';
    }

    // Кнопка удаления
    const removeBtn = card.querySelector('.cart-item-remove');
    if (removeBtn) {
      // Добавляем класс в зависимости от статуса покупки
      if (item.IsBought) {
        removeBtn.classList.add('bought');
      }
      
      removeBtn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        removeFromCart(item.ID, item.CartItemId);
      });
    }

    container.appendChild(card);
  });
}

// Удаление из корзины
async function removeFromCart(solutionId, cartItemId) {
  if (!confirm('Удалить решение из корзины?')) {
    return;
  }

  try {
    const token = localStorage.getItem('accessToken');
    
    // Используем cartItemId если есть, иначе solutionId
    const url = cartItemId 
      ? `/api/cart/item/${cartItemId}`
      : `/api/cart/${solutionId}`;
    
    const response = await fetch(url, {
      method: 'DELETE',
      credentials: 'include',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });

    if (response.status === 401) {
      try {
        await auth.refreshToken();
        const newToken = localStorage.getItem('accessToken');
        const retryResponse = await fetch(url, {
          method: 'DELETE',
          credentials: 'include',
          headers: {
            'Authorization': `Bearer ${newToken}`,
            'Content-Type': 'application/json'
          }
        });
        
        if (!retryResponse.ok) {
          throw new Error('Ошибка удаления');
        }
        
        // Обновляем список корзины
        await loadCart();
        // Обновляем состояние иконки корзины в header
        await updateCartIconState();
        return;
      } catch (refreshError) {
        console.error('Ошибка обновления токена:', refreshError);
        alert('Ошибка авторизации. Пожалуйста, войдите снова.');
        return;
      }
    } else if (!response.ok) {
      throw new Error('Ошибка удаления из корзины');
    }

    // Обновляем список корзины
    await loadCart();
    // Обновляем состояние иконки корзины в header
    await updateCartIconState();

  } catch (error) {
    console.error('Ошибка удаления из корзины:', error);
    alert('Не удалось удалить решение из корзины');
  }
}

// Обновление счетчика корзины
function updateCartCount() {
  const countElement = document.getElementById('cart-count');
  if (countElement) {
    countElement.textContent = cartItems.length;
  }
}

// Инициализация
document.addEventListener('DOMContentLoaded', () => {
  // Обновляем состояние корзины в header при загрузке страницы
  updateCartIconState();
  loadCart();
});

