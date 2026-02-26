/**
 * Mobile Menu Handler - Управление мобильным меню в header
 * Обрабатывает бейджи уведомлений и корзины
 */

// Ждём полной загрузки DOM
document.addEventListener('DOMContentLoaded', function() {
    /**
     * Обновляет бейдж корзины
     * @param {number} count - Количество товаров в корзине
     */
    function updateCartBadge(count) {
        // Ищем иконку корзины в мобильном и десктопном меню
        const cartLinks = document.querySelectorAll('a[href*="cart.html"]');

        cartLinks.forEach(function(cartLink) {
            // Ищем существующий бейдж или создаём новый
            let badge = cartLink.querySelector('.cart-badge');

            if (count > 0) {
                if (!badge) {
                    badge = document.createElement('span');
                    badge.className = 'cart-badge';
                    cartLink.appendChild(badge);
                }
                badge.textContent = count > 99 ? '99+' : count;

                // Добавляем класс для подсветки корзины
                cartLink.classList.add('cart-filled');
            } else {
                if (badge) {
                    badge.remove();
                }
                cartLink.classList.remove('cart-filled');
            }
        });
    }

    /**
     * Обновляет бейдж уведомлений
     * @param {number} count - Количество непрочитанных уведомлений
     */
    function updateNotificationsBadge(count) {
        // Ищем иконку уведомлений в мобильном и десктопном меню
        const notificationLinks = document.querySelectorAll('a[href*="notifications.html"]');

        notificationLinks.forEach(function(notificationLink) {
            // Ищем существующий бейдж или создаём новый
            let badge = notificationLink.querySelector('.notification-badge');

            if (count > 0) {
                if (!badge) {
                    badge = document.createElement('span');
                    badge.className = 'notification-badge';
                    notificationLink.appendChild(badge);
                }
                badge.textContent = count > 99 ? '99+' : count;
            } else if (badge) {
                badge.remove();
            }
        });
    }

    /**
     * Проверяет количество товаров в корзине из localStorage
     */
    function checkCartCount() {
        try {
            const cart = JSON.parse(localStorage.getItem('cart') || '[]');
            const count = Array.isArray(cart) ? cart.length : 0;
            updateCartBadge(count);
        } catch (e) {
            console.error('Error reading cart from localStorage:', e);
        }
    }

    /**
     * Проверяет количество непрочитанных уведомлений из localStorage
     */
    function checkNotificationsCount() {
        try {
            const notifications = JSON.parse(localStorage.getItem('notifications') || '[]');
            const unreadCount = Array.isArray(notifications)
                ? notifications.filter(n => !n.read).length
                : 0;
            updateNotificationsBadge(unreadCount);
        } catch (e) {
            console.error('Error reading notifications from localStorage:', e);
        }
    }

    // Проверяем бейджи при загрузке страницы
    checkCartCount();
    checkNotificationsCount();

    // Слушаем изменения в localStorage (когда что-то изменяется в другой вкладке)
    window.addEventListener('storage', function(e) {
        if (e.key === 'cart') {
            checkCartCount();
        } else if (e.key === 'notifications') {
            checkNotificationsCount();
        }
    });

    // Периодически проверяем бейджи (на случай изменений в текущей вкладке)
    setInterval(function() {
        checkCartCount();
        checkNotificationsCount();
    }, 5000); // Каждые 5 секунд

    // Экспортируем функции для использования из других скриптов
    window.MobileMenu = {
        updateCartBadge: updateCartBadge,
        updateNotificationsBadge: updateNotificationsBadge
    };

    // Отладочная информация
    console.log('Mobile menu initialized successfully');
});
