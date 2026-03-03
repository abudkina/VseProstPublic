// index.js
import { initAuthHandlers } from './common.js';
import {
    loadCategories,
    initHashtagsTomSelect,
    loadProblemsCards,
    renderProblemCards,
    initFilterHandlers,
    initTagClickHandler,
    PAGE_SIZE
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
  limit: PAGE_SIZE,
  offset: 0
};
let hasMore = true;
let loadingMore = false;
let scrollSentinel = null;
let scrollObserver = null;

const renderOptions = () => ({
  isAdmin: false,
  onTopicClick: (topicId) => {
    currentFilters.topic = topicId;
    currentFilters.offset = 0;
    hasMore = true;
    reloadCards();
  }
});

function addSentinel() {
  const container = document.querySelector('.cards-container');
  if (!container || container.querySelector('.scroll-sentinel')) return;
  const sentinel = document.createElement('div');
  sentinel.className = 'scroll-sentinel';
  sentinel.setAttribute('aria-hidden', 'true');
  container.appendChild(sentinel);
  scrollSentinel = sentinel;
  if (scrollObserver) scrollObserver.observe(sentinel);
}

function removeSentinel() {
  scrollSentinel?.remove();
  scrollSentinel = null;
}

function reloadCards() {
  currentFilters.append = false;
  currentFilters.offset = 0;
  loadProblemsCards(currentFilters, (list, meta) => {
    hasMore = meta.hasMore !== false;
    renderProblemCards(list, { ...meta, ...renderOptions() });
    if (hasMore) addSentinel();
  });
}

function loadMoreCards() {
  if (loadingMore || !hasMore) return;
  loadingMore = true;
  const container = document.querySelector('.cards-container');
  currentFilters.offset = container ? container.querySelectorAll('.card').length : 0;
  currentFilters.append = true;
  loadProblemsCards(currentFilters, (list, meta) => {
    hasMore = meta.hasMore !== false;
    renderProblemCards(list, { ...meta, append: true, ...renderOptions() });
    loadingMore = false;
    if (!hasMore) removeSentinel();
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

    scrollObserver = new IntersectionObserver(
        (entries) => { if (entries[0]?.isIntersecting) loadMoreCards(); },
        { rootMargin: '200px', threshold: 0 }
    );
    reloadCards();
});