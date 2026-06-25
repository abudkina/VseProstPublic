// logoAdmin.js - обработчик клика на логотип для админов
import { checkIsAdmin } from './authorizationFunctions.js';

// Инициализация клика на логотип для админов
export function initAdminLogo() {
    const logo = document.querySelector('.logo');
    if (!logo) return;
    
    // Проверяем, является ли пользователь админом
    checkIsAdmin().then(isAdmin => {
        if (isAdmin) {
            logo.style.cursor = 'pointer';
            logo.title = 'Перейти в админку';
            logo.addEventListener('click', (e) => {
                e.preventDefault();
                window.location.href = 'html/admin.html';
            });
        }
    }).catch(() => {
        // Если ошибка, просто не делаем логотип кликабельным
    });
}

// Автоматическая инициализация при загрузке
document.addEventListener('DOMContentLoaded', () => {
    initAdminLogo();
});

