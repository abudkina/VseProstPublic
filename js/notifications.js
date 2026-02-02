// notifications.js
import * as auth from './authorizationFunctions.js';
import { updateCartIconState, updateNotificationIconState } from './cartFunctions.js';

// Глобальная переменная для уведомлений
let notifications = [];

// Обновляем состояние корзины и уведомлений при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    updateCartIconState();
    updateNotificationIconState();
});

// Проверяем аутентификацию перед загрузкой
(async () => {
    try {
        await auth.checkAuth(true); // true — редирект при ошибке
        await init(); // Запускаем загрузку уведомлений
        // Обновляем корзину и уведомления после инициализации
        updateCartIconState();
        updateNotificationIconState();
    } catch (error) {
        console.error('Ошибка авторизации:', error);
        // checkAuth уже обработает редирект
        // Обновляем корзину и уведомления даже при ошибке (покажет 0)
        updateCartIconState();
        updateNotificationIconState();
    }
})();

// Функция для загрузки уведомлений по API
async function loadNotifications() {
    try {
        const token = localStorage.getItem('accessToken');
        const headers = { 'Content-Type': 'application/json' };
        if (token && token !== 'null' && token !== 'undefined') {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const response = await fetch(API_CONFIG.buildURL(API_CONFIG.ENDPOINTS.NOTIFICATIONS), {
            method: 'GET',
            headers,
            credentials: 'include'
        });
        
        if (response.status === 401) {
            // Попробуем обновить токен
            const refreshed = await auth.refreshToken();
            if (refreshed) {
                return await loadNotifications(); // Повторяем запрос
            }
            throw new Error('Требуется авторизация');
        }
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error('Ошибка HTTP: ' + response.status + ' - ' + errorText);
        }
        
        const data = await response.json();
        return Array.isArray(data) ? data : []; // Массив объектов {ID, Name, Description, Read, CreatedDate}
    } catch (error) {
        console.error('Error loading notifications:', error);
        return [];
    }
}

// Функция для toggle read/unread по API
async function toggleRead(id) {
    try {
        const token = localStorage.getItem('accessToken');
        const headers = { 'Content-Type': 'application/json' };
        if (token && token !== 'null' && token !== 'undefined') {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const response = await fetch(API_CONFIG.buildURLWithParams('/notifications/toggle-read', {id: id}), {
            method: 'PATCH',
            headers,
            credentials: 'include'
        });
        
        if (response.status === 401) {
            // Попробуем обновить токен
            const refreshed = await auth.refreshToken();
            if (refreshed) {
                return await toggleRead(id); // Повторяем запрос
            }
            throw new Error('Требуется авторизация');
        }
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error('Ошибка HTTP: ' + response.status + ' - ' + errorText);
        }
        
        const data = await response.json();
        return data.read; // Возвращает новое состояние read
    } catch (error) {
        console.error('Error toggling read:', error);
        return null;
    }
}

// Функция для форматирования даты
function formatDate(dateString) {
    if (!dateString) return '';
    
    try {
        const date = new Date(dateString);
        const day = date.getDate().toString().padStart(2, '0');
        const month = (date.getMonth() + 1).toString().padStart(2, '0');
        const year = date.getFullYear();
        const hours = date.getHours().toString().padStart(2, '0');
        const minutes = date.getMinutes().toString().padStart(2, '0');
        
        const today = new Date();
        const isToday = date.toDateString() === today.toDateString();
        
        if (isToday) {
            return `Сегодня в ${hours}:${minutes}`;
        }
        
        const yesterday = new Date(today);
        yesterday.setDate(yesterday.getDate() - 1);
        const isYesterday = date.toDateString() === yesterday.toDateString();
        
        if (isYesterday) {
            return `Вчера в ${hours}:${minutes}`;
        }
        
        return `${day}.${month}.${year} в ${hours}:${minutes}`;
    } catch (e) {
        console.error('Ошибка форматирования даты:', e);
        return '';
    }
}

// Функция для получения частичного текста (превью)
function getPreviewText(text, maxLength = 150) {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

// Функция для рендеринга уведомлений
function renderNotifications() {
    const container = document.getElementById('notifications-container');
    if (!container) {
        console.error('Контейнер для уведомлений не найден');
        return;
    }
    
    container.innerHTML = ''; // Очистить контейнер

    if (notifications.length === 0) {
        container.innerHTML = '<p style="text-align: center; color: #999; font-size: 1.2em; padding: 60px 20px;">Нет уведомлений</p>';
        return;
    }

    notifications.forEach(notification => {
        const card = document.createElement('div');
        card.classList.add('notification-card');
        if (!notification.Read) {
            card.classList.add('unread-card');
        }
        card.setAttribute('data-id', notification.ID);

        // Заголовок
        const title = document.createElement('div');
        title.classList.add('notification-title');
        title.textContent = notification.Name || 'Без названия';

        // Текст (частичный)
        const text = document.createElement('div');
        text.classList.add('notification-text');
        text.textContent = getPreviewText(notification.Description || '');

        // Справа блок с иконкой и датой
        const rightBlock = document.createElement('div');
        rightBlock.classList.add('notification-right');

        const icon = document.createElement('span');
        icon.classList.add('notification-icon');
        if (notification.Read) {
            icon.textContent = '✓';
            icon.classList.add('read');
            icon.title = 'Прочитано';
        } else {
            icon.textContent = '●';
            icon.classList.add('unread');
            icon.title = 'Не прочитано';
        }

        // Обработчик клика на иконку для toggle
        icon.addEventListener('click', async (e) => {
            e.stopPropagation();
            const newRead = await toggleRead(notification.ID);
            if (newRead !== null) {
                notification.Read = newRead;
                renderNotifications(); // Перерендерить
                updateNotificationIconState(); // Обновить бейдж
            }
        });

        // Дата уведомления под иконкой
        const date = document.createElement('div');
        date.classList.add('notification-date');
        date.textContent = formatDate(notification.CreatedDate);

        rightBlock.appendChild(icon);
        rightBlock.appendChild(date);

        card.appendChild(title);
        card.appendChild(text);
        card.appendChild(rightBlock);

        // Клик на карточку открывает модальное окно
        card.addEventListener('click', (e) => {
            // Не открываем модальное окно, если клик был на иконку
            if (e.target.classList.contains('notification-icon')) {
                return;
            }
            showModal(notification);
        });

        container.appendChild(card);
    });
}

// Функция для показа модального окна
async function showModal(notification) {
    const modal = document.getElementById('notification-modal');
    const modalTitle = document.getElementById('modal-title');
    const modalText = document.getElementById('modal-text');
    const modalDate = document.getElementById('modal-date');
    
    if (!modal || !modalTitle || !modalText || !modalDate) {
        console.error('Элементы модального окна не найдены');
        return;
    }
    
    modalTitle.textContent = notification.Name || 'Без названия';
    modalText.textContent = notification.Description || '';
    modalDate.textContent = formatDate(notification.CreatedDate);
    modal.style.display = 'block';

    // Отметить как прочитанное, если не прочитано
    if (!notification.Read) {
        const newRead = await toggleRead(notification.ID);
        if (newRead !== null) {
            notification.Read = newRead;
            renderNotifications(); // Перерендерить
            updateNotificationIconState(); // Обновить бейдж
        }
    }
}

// Закрытие модального окна
document.addEventListener('DOMContentLoaded', () => {
    const closeBtn = document.querySelector('.close');
    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            const modal = document.getElementById('notification-modal');
            if (modal) {
                modal.style.display = 'none';
            }
        });
    }
    
    // Закрытие модального окна при клике вне его
    window.addEventListener('click', (event) => {
        const modal = document.getElementById('notification-modal');
        if (modal && event.target === modal) {
            modal.style.display = 'none';
        }
    });
    
    // Закрытие модального окна по клавише Escape
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') {
            const modal = document.getElementById('notification-modal');
            if (modal && modal.style.display === 'block') {
                modal.style.display = 'none';
            }
        }
    });
});

// Инициализация
async function init() {
    notifications = await loadNotifications();
    renderNotifications();
}

// Экспортируем функции, если нужно использовать в других файлах
export { init, loadNotifications, toggleRead };
