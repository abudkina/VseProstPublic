/**
 * Validation Utility Module
 * Функции для валидации данных форм
 */

const Validation = {
    /**
     * Валидация email
     * @param {string} email - Email для проверки
     * @returns {boolean}
     */
    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    },

    /**
     * Валидация пароля
     * @param {string} password - Пароль для проверки
     * @param {Object} options - Опции валидации
     * @returns {Object} - {valid: boolean, errors: string[]}
     */
    isValidPassword(password, options = {}) {
        const {
            minLength = 6,
            requireUppercase = false,
            requireLowercase = false,
            requireNumbers = false,
            requireSpecialChars = false
        } = options;

        const errors = [];

        if (!password || password.length < minLength) {
            errors.push(`Пароль должен содержать минимум ${minLength} символов`);
        }

        if (requireUppercase && !/[A-Z]/.test(password)) {
            errors.push('Пароль должен содержать заглавные буквы');
        }

        if (requireLowercase && !/[a-z]/.test(password)) {
            errors.push('Пароль должен содержать строчные буквы');
        }

        if (requireNumbers && !/\d/.test(password)) {
            errors.push('Пароль должен содержать цифры');
        }

        if (requireSpecialChars && !/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
            errors.push('Пароль должен содержать специальные символы');
        }

        return {
            valid: errors.length === 0,
            errors
        };
    },

    /**
     * Валидация имени пользователя
     * @param {string} username - Имя пользователя
     * @returns {Object} - {valid: boolean, error: string}
     */
    isValidUsername(username) {
        if (!username || username.length < 3) {
            return { valid: false, error: 'Имя пользователя должно содержать минимум 3 символа' };
        }

        if (username.length > 30) {
            return { valid: false, error: 'Имя пользователя не должно превышать 30 символов' };
        }

        if (!/^[a-zA-Z0-9_\u0400-\u04FF]+$/.test(username)) {
            return { valid: false, error: 'Имя пользователя может содержать только буквы, цифры и подчеркивание' };
        }

        return { valid: true, error: null };
    },

    /**
     * Валидация URL
     * @param {string} url - URL для проверки
     * @returns {boolean}
     */
    isValidUrl(url) {
        try {
            new URL(url);
            return true;
        } catch (e) {
            return false;
        }
    },

    /**
     * Валидация номера телефона
     * @param {string} phone - Телефон для проверки
     * @returns {boolean}
     */
    isValidPhone(phone) {
        const phoneRegex = /^[\+]?[(]?[0-9]{1,4}[)]?[-\s\.]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{1,9}$/;
        return phoneRegex.test(phone);
    },

    /**
     * Валидация числа
     * @param {any} value - Значение для проверки
     * @param {Object} options - Опции валидации
     * @returns {Object} - {valid: boolean, error: string}
     */
    isValidNumber(value, options = {}) {
        const { min, max, integer = false } = options;
        const num = Number(value);

        if (isNaN(num)) {
            return { valid: false, error: 'Значение должно быть числом' };
        }

        if (integer && !Number.isInteger(num)) {
            return { valid: false, error: 'Значение должно быть целым числом' };
        }

        if (min !== undefined && num < min) {
            return { valid: false, error: `Значение должно быть не меньше ${min}` };
        }

        if (max !== undefined && num > max) {
            return { valid: false, error: `Значение должно быть не больше ${max}` };
        }

        return { valid: true, error: null };
    },

    /**
     * Валидация длины строки
     * @param {string} value - Строка для проверки
     * @param {number} min - Минимальная длина
     * @param {number} max - Максимальная длина
     * @returns {Object} - {valid: boolean, error: string}
     */
    isValidLength(value, min, max) {
        if (!value) {
            return { valid: false, error: 'Значение не может быть пустым' };
        }

        if (min && value.length < min) {
            return { valid: false, error: `Минимальная длина ${min} символов` };
        }

        if (max && value.length > max) {
            return { valid: false, error: `Максимальная длина ${max} символов` };
        }

        return { valid: true, error: null };
    },

    /**
     * Валидация файла
     * @param {File} file - Файл для проверки
     * @param {Object} options - Опции валидации
     * @returns {Object} - {valid: boolean, error: string}
     */
    isValidFile(file, options = {}) {
        const {
            maxSize = 32 * 1024 * 1024, // 32MB по умолчанию
            allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        } = options;

        if (!file) {
            return { valid: false, error: 'Файл не выбран' };
        }

        if (file.size > maxSize) {
            const maxSizeMB = Math.round(maxSize / (1024 * 1024));
            return { valid: false, error: `Размер файла не должен превышать ${maxSizeMB}MB` };
        }

        if (allowedTypes.length > 0 && !allowedTypes.includes(file.type)) {
            const types = allowedTypes.map(t => t.split('/')[1]).join(', ');
            return { valid: false, error: `Допустимые форматы: ${types}` };
        }

        return { valid: true, error: null };
    },

    /**
     * Валидация формы
     * @param {HTMLFormElement} form - Форма для валидации
     * @param {Object} rules - Правила валидации
     * @returns {Object} - {valid: boolean, errors: Object}
     */
    validateForm(form, rules) {
        const errors = {};
        let isValid = true;

        Object.keys(rules).forEach(fieldName => {
            const field = form.elements[fieldName];
            if (!field) return;

            const fieldRules = rules[fieldName];
            const value = field.value;

            // Обязательное поле
            if (fieldRules.required && !value.trim()) {
                errors[fieldName] = fieldRules.requiredMessage || 'Поле обязательно для заполнения';
                isValid = false;
                this._setFieldError(field, errors[fieldName]);
                return;
            }

            // Email
            if (fieldRules.email && value && !this.isValidEmail(value)) {
                errors[fieldName] = 'Неверный формат email';
                isValid = false;
                this._setFieldError(field, errors[fieldName]);
                return;
            }

            // Минимальная длина
            if (fieldRules.minLength && value.length < fieldRules.minLength) {
                errors[fieldName] = `Минимальная длина ${fieldRules.minLength} символов`;
                isValid = false;
                this._setFieldError(field, errors[fieldName]);
                return;
            }

            // Максимальная длина
            if (fieldRules.maxLength && value.length > fieldRules.maxLength) {
                errors[fieldName] = `Максимальная длина ${fieldRules.maxLength} символов`;
                isValid = false;
                this._setFieldError(field, errors[fieldName]);
                return;
            }

            // Пользовательская функция валидации
            if (fieldRules.custom && typeof fieldRules.custom === 'function') {
                const customResult = fieldRules.custom(value, form);
                if (!customResult.valid) {
                    errors[fieldName] = customResult.error;
                    isValid = false;
                    this._setFieldError(field, errors[fieldName]);
                    return;
                }
            }

            // Убираем ошибку если валидация прошла
            this._clearFieldError(field);
        });

        return { valid: isValid, errors };
    },

    /**
     * Устанавливает ошибку для поля
     * @param {HTMLElement} field - Поле формы
     * @param {string} message - Сообщение об ошибке
     * @private
     */
    _setFieldError(field, message) {
        field.classList.add('error');

        // Убираем старую ошибку если есть
        const existingError = field.parentElement.querySelector('.field-error');
        if (existingError) {
            existingError.remove();
        }

        // Добавляем новую ошибку
        const errorElement = document.createElement('div');
        errorElement.className = 'field-error';
        errorElement.textContent = message;
        field.parentElement.appendChild(errorElement);
    },

    /**
     * Очищает ошибку для поля
     * @param {HTMLElement} field - Поле формы
     * @private
     */
    _clearFieldError(field) {
        field.classList.remove('error');

        const existingError = field.parentElement.querySelector('.field-error');
        if (existingError) {
            existingError.remove();
        }
    },

    /**
     * Очищает все ошибки формы
     * @param {HTMLFormElement} form - Форма
     */
    clearFormErrors(form) {
        const errorFields = form.querySelectorAll('.error');
        errorFields.forEach(field => this._clearFieldError(field));
    }
};

// Добавляем стили для ошибок
if (typeof document !== 'undefined') {
    const style = document.createElement('style');
    style.textContent = `
        .error {
            border-color: #f44336 !important;
        }

        .field-error {
            color: #f44336;
            font-size: 12px;
            margin-top: 4px;
        }
    `;
    document.head.appendChild(style);
}

// Экспорт для использования в модулях
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Validation;
}
