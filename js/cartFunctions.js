// cartFunctions.js - общие функции для работы с корзиной и уведомлениями
import * as auth from './authorizationFunctions.js';

/**
 * Добавление решения в корзину
 */
export async function addToCart(solutionId) {
  try {
    // Проверяем аутентификацию
    await auth.checkAuth(true);
  } catch (error) {
    alert('Для добавления в корзину необходимо войти в систему');
    return false;
  }

  try {
    const token = localStorage.getItem('accessToken');
    const response = await fetch(API_CONFIG.buildURL(`/cart/${solutionId}`), {
      method: 'POST',
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
        const retryResponse = await fetch(API_CONFIG.buildURL(`/cart/${solutionId}`), {
          method: 'POST',
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
          const errorData = await retryResponse.json();
          throw new Error(errorData.error || 'Ошибка добавления в корзину');
        }
        
        const data = await retryResponse.json();
        
        // Обновляем состояние иконки корзины в header
        await updateCartIconState();
        
        return { success: true, message: data.message || 'Решение добавлено в корзину', inCart: data.in_cart };
      } catch (refreshError) {
        console.error('Ошибка обновления токена:', refreshError);
        alert('Ошибка авторизации. Пожалуйста, войдите снова.');
        return { success: false, error: 'Ошибка авторизации' };
      }
    }

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Ошибка добавления в корзину');
    }

    const data = await response.json();
    
    // Обновляем состояние иконки корзины в header
    await updateCartIconState();
    
    return { success: true, message: data.message || 'Решение добавлено в корзину', inCart: data.in_cart };

  } catch (error) {
    console.error('Ошибка добавления в корзину:', error);
    return { success: false, error: error.message };
  }
}

/**
 * Удаление решения из корзины
 */
export async function removeFromCart(solutionId) {
  try {
    const token = localStorage.getItem('accessToken');
    const response = await fetch(API_CONFIG.buildURL(`/cart/${solutionId}`), {
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
        const retryResponse = await fetch(API_CONFIG.buildURL(`/cart/${solutionId}`), {
          method: 'DELETE',
          credentials: 'include',
          headers: {
            'Authorization': `Bearer ${newToken}`,
            'Content-Type': 'application/json'
          }
        });
        
        if (!retryResponse.ok) {
          throw new Error('Ошибка удаления из корзины');
        }
        
        // Обновляем состояние иконки корзины в header
        await updateCartIconState();
        
        return { success: true };
      } catch (refreshError) {
        console.error('Ошибка обновления токена:', refreshError);
        return { success: false, error: 'Ошибка авторизации' };
      }
    }

    if (!response.ok) {
      throw new Error('Ошибка удаления из корзины');
    }

    // Обновляем состояние иконки корзины в header
    await updateCartIconState();

    return { success: true };

  } catch (error) {
    console.error('Ошибка удаления из корзины:', error);
    return { success: false, error: error.message };
  }
}

/**
 * Проверка, находится ли решение в корзине
 */
export async function checkInCart(solutionId) {
  try {
    await auth.checkAuth(true);
  } catch (error) {
    return false;
  }

  try {
    const token = localStorage.getItem('accessToken');
    const response = await fetch(API_CONFIG.buildURL(`/cart/check/${solutionId}`), {
      method: 'GET',
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
        const retryResponse = await fetch(API_CONFIG.buildURL(`/cart/check/${solutionId}`), {
          method: 'GET',
          credentials: 'include',
          headers: {
            'Authorization': `Bearer ${newToken}`,
            'Content-Type': 'application/json'
          }
        });
        
        if (!retryResponse.ok) {
          return false;
        }
        
        const data = await retryResponse.json();
        return data.in_cart || false;
      } catch (refreshError) {
        return false;
      }
    }

    if (!response.ok) {
      return false;
    }

    const data = await response.json();
    return data.in_cart || false;

  } catch (error) {
    console.error('Ошибка проверки корзины:', error);
    return false;
  }
}

/**
 * Получение количества решений в корзине
 */
export async function getCartCount() {
  try {
    await auth.checkAuth(false);
  } catch (error) {
    // Пользователь не авторизован - это нормально, возвращаем 0
    console.log('getCartCount: пользователь не авторизован');
    return 0;
  }

  try {
    // Токен хранится в HttpOnly cookies, поэтому не нужно его получать из localStorage
    // Просто отправляем запрос с credentials: 'include', и сервер сам проверит токен из cookies
    console.log('getCartCount: отправка запроса на /api/cart/count');
    const response = await fetch(API_CONFIG.buildURL(API_CONFIG.ENDPOINTS.CART_COUNT), {
      method: 'GET',
      credentials: 'include', // Включаем cookies (токен там)
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    console.log('getCartCount: ответ получен, status:', response.status);

    if (response.status === 401) {
      try {
        await auth.refreshToken();
        // После обновления токена повторяем запрос (токен в cookies)
        const retryResponse = await fetch(API_CONFIG.buildURL(API_CONFIG.ENDPOINTS.CART_COUNT), {
          method: 'GET',
          credentials: 'include', // Токен в cookies
          headers: {
            'Content-Type': 'application/json'
          }
        });
        
        if (!retryResponse.ok) {
          // При ошибке 500 или другой ошибке просто возвращаем 0
          if (retryResponse.status === 500) {
            console.warn('Ошибка сервера при получении количества корзины (500)');
          }
          return 0;
        }
        
        const data = await retryResponse.json();
        return data.count || 0;
      } catch (refreshError) {
        console.warn('Ошибка обновления токена при получении количества корзины:', refreshError);
        return 0;
      }
    }

    if (!response.ok) {
      // При ошибке 500 или другой ошибке просто возвращаем 0, не показываем ошибку пользователю
      if (response.status === 500) {
        console.warn('Ошибка сервера при получении количества корзины (500)');
      }
      return 0;
    }

    const data = await response.json();
    console.log('getCartCount: данные получены:', data);
    const count = data.count || 0;
    console.log('getCartCount: возвращаем count =', count);
    return count;

  } catch (error) {
    // Тихая обработка ошибок - не показываем пользователю, просто возвращаем 0
    console.warn('Ошибка получения количества корзины:', error);
    return 0;
  }
}

/**
 * Обновление визуального состояния иконки корзины в header
 */
export async function updateCartIconState() {
  try {
    console.log('updateCartIconState вызвана');
    const count = await getCartCount();
    console.log('Количество товаров в корзине:', count);
    
    // Находим все ссылки на корзину в header (desktop и mobile меню)
    // Используем более широкий селектор для надежности
    let cartLinks = Array.from(document.querySelectorAll('a[href*="cart.html"], a[title="Корзина"]'));
    console.log('Найдено ссылок на корзину (основной селектор):', cartLinks.length);
    
    if (cartLinks.length === 0) {
      // Пробуем найти через другие селекторы
      const altCartLinks = Array.from(document.querySelectorAll('header a[href*="cart"], nav a[href*="cart"]'));
      console.log('Найдено ссылок (альтернативный селектор):', altCartLinks.length);
      cartLinks = altCartLinks.filter(link => {
        const img = link.querySelector('img');
        const icon = link.querySelector('i');
        const hasIcon = icon
          ? (icon.classList.contains('fa-shopping-basket')
            || icon.classList.contains('fa-shopping-bag')
            || icon.classList.contains('fa-shopping-cart'))
          : false;
        return (img && img.src.includes('shopping')) || hasIcon || link.textContent.includes('Корзина');
      });
      console.log('Отфильтровано ссылок:', cartLinks.length);
    }
    
    if (cartLinks.length === 0) {
      // Попробуем найти все ссылки в header
      const allHeaderLinks = Array.from(document.querySelectorAll('header a, nav a'));
      console.log('Всего ссылок в header:', allHeaderLinks.length);
      allHeaderLinks.forEach((link, index) => {
        const href = link.getAttribute('href') || '';
        const title = link.getAttribute('title') || '';
        const img = link.querySelector('img');
        const imgSrc = img ? img.getAttribute('src') || img.src : '';
        const icon = link.querySelector('i');
        const iconClass = icon ? icon.className : '';
        console.log(`Ссылка ${index}: href="${href}", title="${title}", img="${imgSrc}", icon="${iconClass}"`);
      });
      console.warn('Ссылки на корзину не найдены в header');
      return;
    }
    
    console.log('Обработка', cartLinks.length, 'ссылок на корзину');
    
    cartLinks.forEach((link, index) => {
      console.log(`Обработка ссылки ${index}:`, link);
      const img = link.querySelector('img');
      const icon = link.querySelector('i');
      if (!img && !icon) {
        console.warn('Иконка не найдена в ссылке корзины');
        return;
      }
      
      console.log(`Ссылка ${index}: count=${count}`);
      
      if (count > 0) {
        link.classList.add('cart-filled');
        
        // Добавляем или обновляем счетчик товаров
        let badge = link.querySelector('.cart-badge');
        if (!badge) {
          console.log(`Создание бейджа для ссылки ${index}`);
          badge = document.createElement('span');
          badge.className = 'cart-badge';
          // Убеждаемся, что ссылка имеет position: relative для правильного позиционирования бейджа
          const computedStyle = window.getComputedStyle(link);
          if (computedStyle.position === 'static') {
            link.style.position = 'relative';
          }
          link.appendChild(badge);
          console.log('Бейдж создан и добавлен к ссылке');
        } else {
          console.log(`Бейдж уже существует для ссылки ${index}`);
        }
        badge.textContent = count > 99 ? '99+' : count.toString();
        badge.style.display = 'flex';
        badge.style.visibility = 'visible';
        badge.style.opacity = '1';
        badge.style.position = 'absolute';
        console.log(`Бейдж обновлен: текст="${badge.textContent}", display="${badge.style.display}"`);
        
      } else {
        // Если корзина пуста
        link.classList.remove('cart-filled');
        
        // Скрываем счетчик товаров
        const badge = link.querySelector('.cart-badge');
        if (badge) {
          badge.style.display = 'none';
        }
      }
    });
  } catch (error) {
    console.error('Ошибка обновления состояния иконки корзины:', error);
  }
}

/**
 * Получение количества непрочитанных уведомлений
 */
export async function getUnreadNotificationsCount() {
  try {
    await auth.checkAuth(false);
  } catch (error) {
    // Пользователь не авторизован - это нормально, возвращаем 0
    return 0;
  }

  try {
    // Токен хранится в HttpOnly cookies, поэтому не нужно его получать из localStorage
    // Просто отправляем запрос с credentials: 'include', и сервер сам проверит токен из cookies
    const response = await fetch(API_CONFIG.buildURL('/notifications/count-unread'), {
      method: 'GET',
      credentials: 'include', // Включаем cookies (токен там)
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    if (response.status === 401) {
      try {
        await auth.refreshToken();
        // После обновления токена повторяем запрос (токен в cookies)
        const retryResponse = await fetch(API_CONFIG.buildURL('/notifications/count-unread'), {
          method: 'GET',
          credentials: 'include', // Токен в cookies
          headers: {
            'Content-Type': 'application/json'
          }
        });
        
        if (!retryResponse.ok) {
          return 0;
        }
        
        const data = await retryResponse.json();
        return data.count || 0;
      } catch (refreshError) {
        return 0;
      }
    }

    if (!response.ok) {
      return 0;
    }

    const data = await response.json();
    return data.count || 0;

  } catch (error) {
    console.warn('Ошибка получения количества непрочитанных уведомлений:', error);
    return 0;
  }
}

/**
 * Обновление визуального состояния иконки уведомлений в header
 */
export async function updateNotificationIconState() {
  try {
    const count = await getUnreadNotificationsCount();
    
    // Находим все ссылки на уведомления в header (desktop и mobile меню)
    let notificationLinks = Array.from(document.querySelectorAll('a[href*="notifications.html"], a[title="Уведомления"]'));
    
    if (notificationLinks.length === 0) {
      // Пробуем найти через другие селекторы
      const altNotificationLinks = Array.from(document.querySelectorAll('header a[href*="notification"], nav a[href*="notification"]'));
      notificationLinks = altNotificationLinks.filter(link => {
        const img = link.querySelector('img');
        const icon = link.querySelector('i');
        const hasIcon = icon ? icon.classList.contains('fa-bell') : false;
        return (img && img.src.includes('notification')) || hasIcon || link.textContent.includes('Уведомления');
      });
    }
    
    if (notificationLinks.length === 0) {
      return;
    }
    
    notificationLinks.forEach((link) => {
      const img = link.querySelector('img');
      const icon = link.querySelector('i');
      if (!img && !icon) {
        return;
      }
      
      if (count > 0) {
        // Добавляем или обновляем счетчик непрочитанных уведомлений
        let badge = link.querySelector('.notification-badge');
        if (!badge) {
          badge = document.createElement('span');
          badge.className = 'notification-badge';
          // Убеждаемся, что ссылка имеет position: relative для правильного позиционирования бейджа
          const computedStyle = window.getComputedStyle(link);
          if (computedStyle.position === 'static') {
            link.style.position = 'relative';
          }
          link.appendChild(badge);
        }
        badge.textContent = count > 99 ? '99+' : count.toString();
        badge.style.display = 'flex';
        badge.style.visibility = 'visible';
        badge.style.opacity = '1';
        badge.style.position = 'absolute';
        
      } else {
        // Скрываем счетчик уведомлений
        const badge = link.querySelector('.notification-badge');
        if (badge) {
          badge.style.display = 'none';
        }
      }
    });
  } catch (error) {
    console.error('Ошибка обновления состояния иконки уведомлений:', error);
  }
}

