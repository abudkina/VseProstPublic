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
import { initMobileFilters } from './mobileFilters.js';

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
    // Параметры из URL
    const urlParams = new URLSearchParams(window.location.search);
    const searchFromUrl = urlParams.get('search');
    if (searchFromUrl != null && searchFromUrl !== '') {
        currentFilters.search = searchFromUrl.trim();
        const searchInput = document.getElementById('search');
        if (searchInput) searchInput.value = currentFilters.search;
    }
    const categoryParam = urlParams.get('category');
    if (categoryParam !== null && categoryParam !== '') {
        const categoryId = parseInt(categoryParam, 10);
        if (!Number.isNaN(categoryId)) currentFilters.category = categoryId;
    }
    const topicParam = urlParams.get('topic');
    if (topicParam) {
        const topicId = parseInt(topicParam, 10);
        if (Number.isInteger(topicId)) currentFilters.topic = topicId;
    }
    const hashtagsParam = urlParams.get('hashtags');
    if (hashtagsParam) {
        currentFilters.hashtags = hashtagsParam.split(',').map(s => parseInt(String(s).trim(), 10)).filter(n => !Number.isNaN(n));
    }
    
    // Загружаем категории
    await loadCategories('category', false);
    if (currentFilters.category != null) {
        const categorySelect = document.getElementById('category');
        if (categorySelect) categorySelect.value = String(currentFilters.category);
    }
    // Инициализируем TomSelect для хэштегов
    choicesInstance = initHashtagsTomSelect('hashtags', (instance) => {
        currentFilters.hashtags = instance.getValue().map(v => parseInt(v, 10));
        currentFilters.offset = 0;
        reloadCards();
        document.querySelector('.vs-control')?.classList.add('has-items');
    });
    // Подставить хэштеги из URL в фильтр и в TomSelect
    if (choicesInstance && currentFilters.hashtags.length > 0) {
        currentFilters.hashtags.forEach(id => {
            if (!choicesInstance.options[id]) choicesInstance.addOption({ ID: id, Name: '#' + id });
        });
        choicesInstance.setValue(currentFilters.hashtags);
        document.querySelector('.vs-control')?.classList.add('has-items');
    }
    
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
        
        initTagClickHandler(choicesInstance, currentFilters, reloadCards);
    }
    
    // Обработчики фильтров (поиск, категория, сортировка) — всегда, не только при успешном TomSelect
    initFilterHandlers(currentFilters, choicesInstance, reloadCards);
    initMobileFilters({ onFilterChange: reloadCards });
    
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