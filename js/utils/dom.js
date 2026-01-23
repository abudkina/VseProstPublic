/**
 * DOM Utility Module
 * Вспомогательные функции для работы с DOM
 */

const DOM = {
    /**
     * Создает элемент с классами и атрибутами
     * @param {string} tag - Тег элемента
     * @param {Object} options - Опции элемента
     * @param {string|string[]} options.className - Класс или массив классов
     * @param {Object} options.attributes - Атрибуты элемента
     * @param {string} options.text - Текстовое содержимое
     * @param {string} options.html - HTML содержимое
     * @returns {HTMLElement}
     */
    createElement(tag, options = {}) {
        const element = document.createElement(tag);

        if (options.className) {
            if (Array.isArray(options.className)) {
                element.classList.add(...options.className);
            } else {
                element.className = options.className;
            }
        }

        if (options.attributes) {
            Object.keys(options.attributes).forEach(key => {
                element.setAttribute(key, options.attributes[key]);
            });
        }

        if (options.text) {
            element.textContent = options.text;
        }

        if (options.html) {
            element.innerHTML = options.html;
        }

        return element;
    },

    /**
     * Показывает элемент
     * @param {HTMLElement|string} element - Элемент или селектор
     */
    show(element) {
        const el = typeof element === 'string' ? document.querySelector(element) : element;
        if (el) {
            el.style.display = '';
            el.classList.remove('hidden');
        }
    },

    /**
     * Скрывает элемент
     * @param {HTMLElement|string} element - Элемент или селектор
     */
    hide(element) {
        const el = typeof element === 'string' ? document.querySelector(element) : element;
        if (el) {
            el.style.display = 'none';
            el.classList.add('hidden');
        }
    },

    /**
     * Переключает видимость элемента
     * @param {HTMLElement|string} element - Элемент или селектор
     */
    toggle(element) {
        const el = typeof element === 'string' ? document.querySelector(element) : element;
        if (el) {
            if (el.style.display === 'none' || el.classList.contains('hidden')) {
                this.show(el);
            } else {
                this.hide(el);
            }
        }
    },

    /**
     * Очищает содержимое элемента
     * @param {HTMLElement|string} element - Элемент или селектор
     */
    clear(element) {
        const el = typeof element === 'string' ? document.querySelector(element) : element;
        if (el) {
            el.innerHTML = '';
        }
    },

    /**
     * Добавляет обработчик события с делегированием
     * @param {HTMLElement} parent - Родительский элемент
     * @param {string} eventType - Тип события
     * @param {string} selector - Селектор целевого элемента
     * @param {Function} handler - Обработчик события
     */
    delegate(parent, eventType, selector, handler) {
        parent.addEventListener(eventType, (event) => {
            const target = event.target.closest(selector);
            if (target && parent.contains(target)) {
                handler.call(target, event);
            }
        });
    },

    /**
     * Показывает уведомление
     * @param {string} message - Сообщение
     * @param {string} type - Тип уведомления (success, error, warning, info)
     * @param {number} duration - Длительность показа в мс
     */
    showNotification(message, type = 'info', duration = 3000) {
        // Удаляем предыдущие уведомления
        const existingNotification = document.querySelector('.notification-toast');
        if (existingNotification) {
            existingNotification.remove();
        }

        const notification = this.createElement('div', {
            className: ['notification-toast', `notification-${type}`],
            html: `
                <span class="notification-message">${this.escapeHtml(message)}</span>
                <button class="notification-close">&times;</button>
            `
        });

        document.body.appendChild(notification);

        // Показываем с анимацией
        setTimeout(() => notification.classList.add('show'), 10);

        // Обработчик закрытия
        const closeBtn = notification.querySelector('.notification-close');
        closeBtn.addEventListener('click', () => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        });

        // Автоматическое закрытие
        if (duration > 0) {
            setTimeout(() => {
                notification.classList.remove('show');
                setTimeout(() => notification.remove(), 300);
            }, duration);
        }
    },

    /**
     * Показывает индикатор загрузки
     * @param {HTMLElement|string} container - Контейнер или селектор
     * @param {string} text - Текст загрузки
     * @returns {HTMLElement} - Элемент индикатора
     */
    showLoader(container, text = 'Загрузка...') {
        const el = typeof container === 'string' ? document.querySelector(container) : container;
        if (!el) return null;

        const loader = this.createElement('div', {
            className: 'loader-container',
            html: `
                <div class="loader-spinner"></div>
                <div class="loader-text">${this.escapeHtml(text)}</div>
            `
        });

        el.appendChild(loader);
        return loader;
    },

    /**
     * Скрывает индикатор загрузки
     * @param {HTMLElement} loader - Элемент индикатора
     */
    hideLoader(loader) {
        if (loader && loader.parentNode) {
            loader.parentNode.removeChild(loader);
        }
    },

    /**
     * Экранирует HTML
     * @param {string} text - Текст для экранирования
     * @returns {string}
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    /**
     * Получает значение из формы
     * @param {HTMLFormElement} form - Форма
     * @returns {Object} - Объект со значениями полей
     */
    getFormData(form) {
        const formData = new FormData(form);
        const data = {};

        for (let [key, value] of formData.entries()) {
            // Если ключ уже существует, делаем массив
            if (data[key]) {
                if (!Array.isArray(data[key])) {
                    data[key] = [data[key]];
                }
                data[key].push(value);
            } else {
                data[key] = value;
            }
        }

        return data;
    },

    /**
     * Заполняет форму данными
     * @param {HTMLFormElement} form - Форма
     * @param {Object} data - Данные для заполнения
     */
    setFormData(form, data) {
        Object.keys(data).forEach(key => {
            const field = form.elements[key];
            if (field) {
                if (field.type === 'checkbox') {
                    field.checked = !!data[key];
                } else if (field.type === 'radio') {
                    const radio = form.querySelector(`input[name="${key}"][value="${data[key]}"]`);
                    if (radio) radio.checked = true;
                } else {
                    field.value = data[key];
                }
            }
        });
    },

    /**
     * Добавляет CSS стили на страницу
     * @param {string} css - CSS строка
     */
    addStyles(css) {
        const style = this.createElement('style', { text: css });
        document.head.appendChild(style);
    },

    /**
     * Плавная прокрутка к элементу
     * @param {HTMLElement|string} element - Элемент или селектор
     * @param {Object} options - Опции прокрутки
     */
    scrollTo(element, options = {}) {
        const el = typeof element === 'string' ? document.querySelector(element) : element;
        if (el) {
            el.scrollIntoView({
                behavior: 'smooth',
                block: 'start',
                ...options
            });
        }
    },

    /**
     * Дебаунс функции
     * @param {Function} func - Функция для дебаунса
     * @param {number} wait - Время ожидания в мс
     * @returns {Function}
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    /**
     * Throttle функции
     * @param {Function} func - Функция для throttle
     * @param {number} limit - Лимит времени в мс
     * @returns {Function}
     */
    throttle(func, limit) {
        let inThrottle;
        return function executedFunction(...args) {
            if (!inThrottle) {
                func(...args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
};

// Добавляем базовые стили для уведомлений
DOM.addStyles(`
    .notification-toast {
        position: fixed;
        top: 20px;
        right: 20px;
        min-width: 300px;
        max-width: 500px;
        padding: 15px 20px;
        background: white;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 15px;
        opacity: 0;
        transform: translateX(400px);
        transition: all 0.3s ease;
        z-index: 10000;
    }

    .notification-toast.show {
        opacity: 1;
        transform: translateX(0);
    }

    .notification-toast.notification-success {
        border-left: 4px solid #4caf50;
    }

    .notification-toast.notification-error {
        border-left: 4px solid #f44336;
    }

    .notification-toast.notification-warning {
        border-left: 4px solid #ff9800;
    }

    .notification-toast.notification-info {
        border-left: 4px solid #2196f3;
    }

    .notification-message {
        flex: 1;
        color: #333;
    }

    .notification-close {
        background: none;
        border: none;
        font-size: 24px;
        color: #999;
        cursor: pointer;
        padding: 0;
        width: 24px;
        height: 24px;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .notification-close:hover {
        color: #333;
    }

    .loader-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 40px;
    }

    .loader-spinner {
        border: 4px solid #f3f3f3;
        border-top: 4px solid #3498db;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        animation: spin 1s linear infinite;
    }

    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }

    .loader-text {
        margin-top: 15px;
        color: #666;
        font-size: 14px;
    }

    .hidden {
        display: none !important;
    }
`);

// Экспорт для использования в модулях
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DOM;
}
