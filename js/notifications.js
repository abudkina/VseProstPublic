// Импорт всего из другого файла
import * as auth from './authorizationFunctions.js';

// Проверяем аутентификацию перед загрузкой
(async () => {
    const authenticated = await auth.checkAuth(true); // true — редирект при ошибке
    if (!authenticated) return; // checkAuth уже обработает редирект
})();

// Функция для загрузки уведомлений по API
async function loadNotifications() {
    try {
        const response = await fetch(`http://127.0.0.1:8080/api/getNotifications`, {
            method: 'GET',
            credentials: 'include'  // Отправляем куки автоматически — сервер извлечёт userID
        });
        if (!response.ok) throw new Error('Ошибка HTTP: ' + response.status);
        const data = await response.json();
        return data; // Массив объектов {id, title, text, read}
    } catch (error) {
        console.error('Error loading notifications:', error);
        return [];
    }
}

// Функция для toggle read/unread по API
async function toggleRead(id) {
    try {
        const response = await fetch(`http://127.0.0.1:8080/api/toggleRead?id=${id}`, {
            method: 'PATCH',
            credentials: 'include'
        });
        if (!response.ok) throw new Error('Ошибка HTTP: ' + response.status);
        const data = await response.json();
        return data.Read; // Возвращает новое состояние read
    } catch (error) {
        console.error('Error toggling read:', error);
        return null;
    }
}

// Функция для рендеринга таблицы (принимает notifications как параметр)
function renderNotifications(notifications) {
    const container = document.getElementById('notifications-container');
    container.innerHTML = ''; // Очистить контейнер

    notifications.forEach(notification => {
        const card = document.createElement('div');
        card.classList.add('notification-card');
        card.setAttribute('data-id', notification.ID);

        // Заголовок
        const title = document.createElement('div');
        title.classList.add('notification-title');
        title.textContent = notification.Name;

        // Текст с многоточием, если не помещается
        const text = document.createElement('div');
        text.classList.add('notification-text');
        text.textContent = notification.Description;

        // Справа блок с иконкой и датой
        const rightBlock = document.createElement('div');
        rightBlock.classList.add('notification-right');

        const icon = document.createElement('span');
        icon.classList.add('notification-icon');
        if (notification.Read) {
            icon.textContent = '📖'; // или можно заменить на svg/картинку
            icon.classList.add('read');
        } else {
            icon.textContent = '📧';
            icon.classList.add('unread');
        }

        // Обработчик клика на иконку для toggle
        icon.addEventListener('click', async (e) => {
            e.stopPropagation(); // Предотвратить открытие модального
            const newRead = await toggleRead(notification.ID);
            if (newRead !== null) {
                notification.Read = newRead;
                renderNotifications(notifications); // Перерендерить
            }
        });

        // Дата уведомления под иконкой
        const date = document.createElement('div');
        date.classList.add('notification-date');
        if (notification.CreatedDate) {
            const d = new Date(notification.CreatedDate);
            date.textContent = `${d.getDate()}.${d.getMonth() + 1}.${d.getFullYear()}`;
        } else {
            date.textContent = '';
        }

        rightBlock.appendChild(icon);
        rightBlock.appendChild(date);

        card.appendChild(title);
        card.appendChild(text);
        card.appendChild(rightBlock);

        card.addEventListener('click', () => {
            showModal(notification);
        });

        container.appendChild(card);
    });
}

// Функция для показа модального окна (принимает объект notification)
async function showModal(notification) {
    document.getElementById('modal-title').textContent = notification.Name;
    document.getElementById('modal-text').textContent = notification.Description;
    document.getElementById('notification-modal').style.display = 'block';

    // Отметить как прочитанное, если не прочитано
    if (!notification.Read) {
        const newRead = await toggleRead(notification.ID);
        if (newRead !== null) {
            notification.Read = newRead;
            renderNotifications(notifications); // Перерендерить
        }
    }
}

// Закрытие модального окна
document.querySelector('.close').addEventListener('click', () => {
    document.getElementById('notification-modal').style.display = 'none';
});

// Закрытие модального окна при клике вне его
window.addEventListener('click', (event) => {
    if (event.target === document.getElementById('notification-modal')) {
        document.getElementById('notification-modal').style.display = 'none';
    }
});

// Глобальная переменная для уведомлений (для перерендера)
let notifications = [];

// Инициализация
async function init() {
    notifications = await loadNotifications();
    renderNotifications(notifications);
}

init(); // Запуск