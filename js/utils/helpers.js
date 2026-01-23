/**
 * Helper Utilities Module
 * Общие вспомогательные функции
 */

const Helpers = {
    /**
     * Форматирование даты
     * @param {Date|string} date - Дата для форматирования
     * @param {string} format - Формат (default, short, long, time)
     * @returns {string}
     */
    formatDate(date, format = 'default') {
        const d = typeof date === 'string' ? new Date(date) : date;

        if (!(d instanceof Date) || isNaN(d)) {
            return 'Неверная дата';
        }

        const options = {
            default: {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            },
            short: {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit'
            },
            long: {
                weekday: 'long',
                year: 'numeric',
                month: 'long',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            },
            time: {
                hour: '2-digit',
                minute: '2-digit'
            }
        };

        return d.toLocaleDateString('ru-RU', options[format] || options.default);
    },

    /**
     * Относительное время (например, "2 часа назад")
     * @param {Date|string} date - Дата
     * @returns {string}
     */
    timeAgo(date) {
        const d = typeof date === 'string' ? new Date(date) : date;
        const seconds = Math.floor((new Date() - d) / 1000);

        const intervals = {
            год: 31536000,
            месяц: 2592000,
            неделя: 604800,
            день: 86400,
            час: 3600,
            минута: 60,
            секунда: 1
        };

        for (const [name, secondsInInterval] of Object.entries(intervals)) {
            const interval = Math.floor(seconds / secondsInInterval);
            if (interval >= 1) {
                return `${interval} ${this._pluralize(interval, name)} назад`;
            }
        }

        return 'только что';
    },

    /**
     * Плюрализация (1 день, 2 дня, 5 дней)
     * @param {number} count - Количество
     * @param {string} word - Слово (год, месяц, день и т.д.)
     * @returns {string}
     * @private
     */
    _pluralize(count, word) {
        const cases = {
            год: ['год', 'года', 'лет'],
            месяц: ['месяц', 'месяца', 'месяцев'],
            неделя: ['неделю', 'недели', 'недель'],
            день: ['день', 'дня', 'дней'],
            час: ['час', 'часа', 'часов'],
            минута: ['минуту', 'минуты', 'минут'],
            секунда: ['секунду', 'секунды', 'секунд']
        };

        const forms = cases[word];
        if (!forms) return word;

        const n = Math.abs(count) % 100;
        const n1 = n % 10;

        if (n > 10 && n < 20) return forms[2];
        if (n1 > 1 && n1 < 5) return forms[1];
        if (n1 === 1) return forms[0];
        return forms[2];
    },

    /**
     * Форматирование числа с разделителями
     * @param {number} num - Число
     * @param {string} separator - Разделитель (default: ' ')
     * @returns {string}
     */
    formatNumber(num, separator = ' ') {
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, separator);
    },

    /**
     * Форматирование цены
     * @param {number} price - Цена
     * @param {string} currency - Валюта (default: '₽')
     * @returns {string}
     */
    formatPrice(price, currency = '₽') {
        return `${this.formatNumber(price)} ${currency}`;
    },

    /**
     * Обрезка текста с многоточием
     * @param {string} text - Текст
     * @param {number} maxLength - Максимальная длина
     * @returns {string}
     */
    truncate(text, maxLength) {
        if (!text || text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    },

    /**
     * Копирование текста в буфер обмена
     * @param {string} text - Текст для копирования
     * @returns {Promise<void>}
     */
    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            return true;
        } catch (err) {
            // Fallback для старых браузеров
            const textArea = document.createElement('textarea');
            textArea.value = text;
            textArea.style.position = 'fixed';
            textArea.style.opacity = '0';
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();

            try {
                document.execCommand('copy');
                document.body.removeChild(textArea);
                return true;
            } catch (err) {
                document.body.removeChild(textArea);
                return false;
            }
        }
    },

    /**
     * Генерация случайной строки
     * @param {number} length - Длина строки
     * @returns {string}
     */
    randomString(length = 10) {
        const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
        let result = '';
        for (let i = 0; i < length; i++) {
            result += chars.charAt(Math.floor(Math.random() * chars.length));
        }
        return result;
    },

    /**
     * Получение параметров URL
     * @param {string} name - Имя параметра (опционально)
     * @returns {string|Object} - Значение параметра или объект всех параметров
     */
    getUrlParam(name) {
        const params = new URLSearchParams(window.location.search);

        if (name) {
            return params.get(name);
        }

        const result = {};
        for (let [key, value] of params.entries()) {
            result[key] = value;
        }
        return result;
    },

    /**
     * Установка параметров URL без перезагрузки страницы
     * @param {Object} params - Объект с параметрами
     */
    setUrlParams(params) {
        const url = new URL(window.location);

        Object.keys(params).forEach(key => {
            if (params[key] === null || params[key] === undefined || params[key] === '') {
                url.searchParams.delete(key);
            } else {
                url.searchParams.set(key, params[key]);
            }
        });

        window.history.pushState({}, '', url);
    },

    /**
     * Сохранение данных в localStorage
     * @param {string} key - Ключ
     * @param {any} value - Значение
     */
    saveToStorage(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (e) {
            console.error('Ошибка сохранения в localStorage:', e);
            return false;
        }
    },

    /**
     * Получение данных из localStorage
     * @param {string} key - Ключ
     * @param {any} defaultValue - Значение по умолчанию
     * @returns {any}
     */
    getFromStorage(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (e) {
            console.error('Ошибка чтения из localStorage:', e);
            return defaultValue;
        }
    },

    /**
     * Удаление данных из localStorage
     * @param {string} key - Ключ
     */
    removeFromStorage(key) {
        try {
            localStorage.removeItem(key);
            return true;
        } catch (e) {
            console.error('Ошибка удаления из localStorage:', e);
            return false;
        }
    },

    /**
     * Скачивание файла
     * @param {string} url - URL файла
     * @param {string} filename - Имя файла
     */
    downloadFile(url, filename) {
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    },

    /**
     * Проверка мобильного устройства
     * @returns {boolean}
     */
    isMobile() {
        return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    },

    /**
     * Задержка выполнения
     * @param {number} ms - Миллисекунды
     * @returns {Promise<void>}
     */
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    },

    /**
     * Глубокое клонирование объекта
     * @param {any} obj - Объект для клонирования
     * @returns {any}
     */
    deepClone(obj) {
        if (obj === null || typeof obj !== 'object') return obj;

        if (obj instanceof Date) {
            return new Date(obj.getTime());
        }

        if (obj instanceof Array) {
            return obj.map(item => this.deepClone(item));
        }

        if (obj instanceof Object) {
            const clonedObj = {};
            for (let key in obj) {
                if (obj.hasOwnProperty(key)) {
                    clonedObj[key] = this.deepClone(obj[key]);
                }
            }
            return clonedObj;
        }
    },

    /**
     * Группировка массива по ключу
     * @param {Array} array - Массив объектов
     * @param {string} key - Ключ для группировки
     * @returns {Object}
     */
    groupBy(array, key) {
        return array.reduce((result, item) => {
            const group = item[key];
            if (!result[group]) {
                result[group] = [];
            }
            result[group].push(item);
            return result;
        }, {});
    },

    /**
     * Уникальные значения массива
     * @param {Array} array - Массив
     * @returns {Array}
     */
    unique(array) {
        return [...new Set(array)];
    },

    /**
     * Сортировка массива объектов
     * @param {Array} array - Массив объектов
     * @param {string} key - Ключ для сортировки
     * @param {boolean} ascending - По возрастанию (default: true)
     * @returns {Array}
     */
    sortBy(array, key, ascending = true) {
        return [...array].sort((a, b) => {
            const aVal = a[key];
            const bVal = b[key];

            if (aVal < bVal) return ascending ? -1 : 1;
            if (aVal > bVal) return ascending ? 1 : -1;
            return 0;
        });
    }
};

// Экспорт для использования в модулях
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Helpers;
}
