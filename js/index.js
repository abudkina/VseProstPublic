// index.js
import { initAuthHandlers } from './common.js';
import {
    loadCategories,
    initHashtagsTomSelect,
    loadProblemsCards,
    renderProblemCards,
    initFilterHandlers,
    initTagClickHandler
} from './problemListCommon.js';

// Инициализация обработчиков авторизации
initAuthHandlers();

let choicesInstance;

let currentFilters = {
  search: '',
  hashtags: [],
  category: null,
  topic: null,
  sort: 'default',
  limit: 50,
  offset: 0
};

// Функция для перезагрузки карточек
function reloadCards() {
    loadProblemsCards(currentFilters, (list, meta) => {
        renderProblemCards(list, {
            ...meta, 
            isAdmin: false,
            onTopicClick: (topicId) => {
                // При клике на тему фильтруем по этой теме
                currentFilters.topic = topicId;
                currentFilters.offset = 0;
                reloadCards();
            }
        });
    });
}

// Инициализация
document.addEventListener('DOMContentLoaded', async () => {
    // Проверяем параметр topic в URL
    const urlParams = new URLSearchParams(window.location.search);
    const topicParam = urlParams.get('topic');
    if (topicParam) {
        const topicId = parseInt(topicParam, 10);
        if (Number.isInteger(topicId)) currentFilters.topic = topicId;
    }
    
    // Загружаем категории
    await loadCategories('category', false);
    
    // Инициализируем TomSelect для хэштегов
    choicesInstance = initHashtagsTomSelect('hashtags', (instance) => {
        currentFilters.hashtags = instance.getValue().map(v => parseInt(v, 10));
        currentFilters.offset = 0;
        reloadCards();
        document.querySelector('.vs-control')?.classList.add('has-items');
    });
    
    // Обработчик удаления хэштегов
    if (choicesInstance) {
        choicesInstance.control.addEventListener('click', function (event) {
            const tag = event.target.closest('.item');
            if (tag) {
                const value = tag.getAttribute('data-value');
                if (value !== null) {
                    choicesInstance.removeItem(value);
                    currentFilters.hashtags = choicesInstance.getValue().map(v => parseInt(v, 10));
                    currentFilters.offset = 0;
                    
                    // Очищаем опции и закрываем выпадающий список при удалении
                    choicesInstance.clearOptions();
                    choicesInstance.close();
                    choicesInstance.control_input.value = '';
                    
                    reloadCards();
                    if (choicesInstance.items.length == 0) {
                        const tsControl = document.querySelector('.vs-control');
                        if (tsControl) {
                            tsControl.classList.remove('has-items');
                            // Убеждаемся, что плейсхолдер виден
                            const input = tsControl.querySelector('input[type="text"]');
                            if (input && !input.value) {
                                input.placeholder = 'Выберите хэштеги';
                            }
                        }
                    }
                }
            }
        });
        
        // Инициализация обработчиков фильтров
        initFilterHandlers(currentFilters, choicesInstance, reloadCards);
        initTagClickHandler(choicesInstance, currentFilters, reloadCards);
    }
    
    // Скрываем ссылку "Добавить проблему" для неавторизованных
    const addProblemLink = document.getElementById('addProblem');
    if (addProblemLink && localStorage.getItem('isLoggedIn') !== 'true') {
        addProblemLink.style.display = 'none';
    }

    // Загружаем карточки
    reloadCards();
});