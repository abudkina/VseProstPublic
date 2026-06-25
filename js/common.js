// common.js - общие функции для всех страниц
import * as auth from './authorizationFunctions.js';
import { updateCartIconState, updateNotificationIconState } from './cartFunctions.js';

export function initAuthHandlers() {
  let updateCalled = false;
  
  // Функция для обновления иконок (с защитой от множественных вызовов)
  const updateIcons = () => {
    if (updateCalled) return;
    updateCalled = true;
    setTimeout(() => {
      updateCartIconState();
      updateNotificationIconState();
      // Разрешаем повторный вызов через небольшую задержку для случаев, когда это действительно нужно
      setTimeout(() => { updateCalled = false; }, 1000);
    }, 300);
  };
  
  // Обновляем при DOMContentLoaded (основной обработчик)
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
      console.log('DOMContentLoaded: вызов updateCartIconState и updateNotificationIconState');
      updateIcons();
    });
  } else {
    // Если страница уже загружена, вызываем сразу
    console.log('Страница уже загружена: вызов updateCartIconState и updateNotificationIconState');
    updateIcons();
  }
  
  // Дополнительная проверка авторизации при загрузке страницы
  window.addEventListener('load', function () {
    if (localStorage.getItem('isLoggedIn')) {
      auth.checkAuth(false).then(() => {
        // Обновляем иконки после успешной проверки авторизации
        updateIcons();
      }).catch(() => {
        localStorage.removeItem('isLoggedIn');
        // Обновляем корзину и уведомления даже если авторизация не прошла (покажет 0)
        updateIcons();
      });
    } else {
      // Обновляем корзину и уведомления даже если пользователь не залогинен (покажет 0)
      updateIcons();
    }
  });
  
  const favoritesLink = document.getElementById('favoritesLink');
  const profileBtn = document.getElementById('profileBtn');
  
  if (favoritesLink) {
    favoritesLink.addEventListener('click', function (e) {
      e.preventDefault();
      if (!localStorage.getItem('isLoggedIn') && !window.SITE_CONFIG?.isStaticMode) {
        sessionStorage.setItem('redirectAfterLogin', 'html/favourites.html');
        window.location.href = 'html/authorization.html';
        return;
      }
      auth.checkAuth(true).then(userID => {
        window.location.href = 'html/favourites.html';
      }).catch(() => {});
    });
  }
  
  if (profileBtn) {
    profileBtn.addEventListener('click', () => {
      auth.checkAuth(false).then(userID => {
        window.location.href = 'html/profile.html';
      }).catch(() => {
        sessionStorage.setItem('redirectAfterLogin', window.location.href);
        window.location.href = 'html/authorization.html';
      });
    });
  }
}