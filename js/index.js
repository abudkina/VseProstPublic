import * as auth from './authorizationFunctions.js';

let choicesInstance;

let currentFilters = {
  search: '',
  hashtags: [],
  category: null,
  limit: 50,
  offset: 0
};

// При загрузке index.html/js — опционально проверить авторизацию
window.addEventListener('load', function() {
    if (localStorage.getItem('isLoggedIn')) {
        auth.checkAuth(false).catch(() => {
            // Тихо сбросить флаг, если токен истёк
            localStorage.removeItem('isLoggedIn');
        });
    }
});

// Обработчик клика на ссылку/кнопку "Избранное" в index.js
document.getElementById('favoritesLink').addEventListener('click', function(e) {
    e.preventDefault();
    
    // Быстрая проверка флага (опционально, для UX)
    if (!localStorage.getItem('isLoggedIn')) {
        sessionStorage.setItem('redirectAfterLogin', '/html/favourites.html');
        window.location.href = '../html/authorization.html';
        return;
    }
    
    // Проверка через API
    auth.checkAuth(true).then(userID => {
        // Если OK, переход
        window.location.href = '../html/favourites.html';  // Или SPA-роутинг, если используете
    }).catch(() => {
        // Уже обработано в checkAuth
    });
});

// Изменённый обработчик клика на кнопку профиля
document.getElementById('profileBtn').addEventListener('click', () => {
    // Проверяем авторизацию без автоматического редиректа
    auth.checkAuth(false).then(userID => {
        // Если авторизован, перейти на страницу профиля
        window.location.href = '../html/profile.html';
    }).catch(() => {
        // Если не авторизован, сохранить текущий URL и перейти на авторизацию
        sessionStorage.setItem('redirectAfterLogin', window.location.href);
        window.location.href = '../html/authorization.html';
    });
});

async function loadCards(search = '', category = null, hashtags = [], offset = 0) {
  const container = document.querySelector('.cards-container');
  container.innerHTML = 'Загрузка...';

  const params = new URLSearchParams();
  if (currentFilters.search) params.append('search', currentFilters.search);
  if (currentFilters.hashtags.length)
    params.append('hashtags', currentFilters.hashtags.join(','));
  if (currentFilters.category != null)
    params.append('category', currentFilters.category);
  params.append('limit', currentFilters.limit);
  params.append('offset', currentFilters.offset);

  try {
    const response = await fetch(`http://127.0.0.1:8080/api/problems?${params.toString()}`);
    if (!response.ok) throw new Error('Ошибка HTTP: ' + response.status);
    const data = await response.json();

    renderCards(data);
    sortAndRender(data);

  } catch (error) {
    container.innerHTML = `<p style="color:red; text-align:center">Ошибка загрузки данных: ${error.message}</p>`;
  }
}

async function loadCategories() {
  try {
    const response = await fetch('http://127.0.0.1:8080/api/categories');
    const categories = await response.json();

    const categorySelect = document.getElementById('category');
    categorySelect.innerHTML = '<option value="">Выберите категорию</option>';

    categories.forEach(cat => {
      const option = document.createElement('option');
      option.value = cat.ID;
      option.textContent = cat.Name;
      categorySelect.appendChild(option);
    });
  } catch (error) {
    console.error('Ошибка загрузки категорий:', error);
  }
}

async function loadMoreData() {
  currentFilters.offset += currentFilters.limit;
  try {
    const container = document.querySelector('.cards-container');
    const params = new URLSearchParams();
    if (currentFilters.search) params.append('search', currentFilters.search);
    if (currentFilters.hashtags.length)
      params.append('hashtags', currentFilters.hashtags.join(','));
    if (currentFilters.category != null)
      params.append('category', currentFilters.category);
    params.append('limit', currentFilters.limit);
    params.append('offset', currentFilters.offset);

    const response = await fetch(`http://127.0.0.1:8080/api/problems?${params.toString()}`);
    if (!response.ok) throw new Error('Ошибка HTTP: ' + response.status);
    const moreData = await response.json();

    if (moreData.length === 0) {
      window.removeEventListener('scroll', onScrollLoadMore);
      return;
    }

    appendCards(moreData);

  } catch (error) {
    console.error(error);
  }
}

function sortAndRender(data) {
  const sortValue = document.getElementById('sort').value;

  switch (sortValue) {
    case 'popularity':
      data.sort((a, b) => (b.Favourite || 0) - (a.Favourite || 0));
      break;
    case 'show':
      data.sort((a, b) => (b.Show || 0) - (a.Show || 0));
      break;
    case 'date':
      data.sort((a, b) => new Date(b.Modified_date) - new Date(a.Modified_date));
      break;
    default:
      break;
  }

  renderCards(data);
}

function renderCards(data) {
  const container = document.querySelector('.cards-container');
  container.innerHTML = '';

  const templateElement = document.getElementById('card-template');
  if (!templateElement) {
    console.error("Шаблон не найден!");
    return;
  }
  const template = templateElement.content;

  if (data.length === 0) {
    container.innerHTML = '<p style="text-align:center;">Ничего не найдено</p>';
    return;
  }

  data.forEach(item => {
    const card = template.cloneNode(true);

    const link = card.querySelector('.card-title-link');
    link.href = `../html/problem.html?problemId=${encodeURIComponent(item.ID)}`;

    const cardImg = card.querySelector('.card-image');
    cardImg.src = item.Image;

    const cardTitleText = card.querySelector('.card-title-text');
    cardTitleText.href = `../html/problem.html?problemId=${encodeURIComponent(item.ID)}`;
    cardTitleText.textContent = item.Name;

    const favoriteCount = card.querySelector('.card-favorites .favorite-count');
    favoriteCount.textContent = item.Favourite || 0;

    const tagsColumn = card.querySelector('.tags-column');
    tagsColumn.innerHTML = '';
    item.Hashtags.forEach(tag => {
      const tagElement = document.createElement('span');
      tagElement.className = 'tag';
      tagElement.textContent = tag.Name;
      tagElement.setAttribute('data-id', tag.ID);
      tagsColumn.appendChild(tagElement);
    });

    card.querySelector('.stat-item.views .stat-value').textContent = item.Show || 0;
    card.querySelector('.stat-item.comments .stat-value').textContent = item.Solutions.length || 0;
    card.querySelector('.stat-item.shares .stat-value').textContent = item.Reply || 0;
    card.querySelector('.stat-item.links .stat-value').textContent = item.ProblemLinks.length || 0;

    container.appendChild(card);
  });
}

document.addEventListener('click', (event) => {
  if (event.target.classList.contains('tag')) {
    const tagId = event.target.getAttribute('data-id');
    if (tagId) {
      choicesInstance.setValue([tagId]);
      loadCards([parseInt(tagId)]);
    } else {
      alert(`Хэштег не найден в данных.`);
    }
  }
});

function initTomSelect() {
  choicesInstance = new TomSelect('#hashtags', {
    valueField: 'ID',
    labelField: 'Name',
    searchField: 'Name',
    maxItems: null,
    create: false,
    loadThrottle: 300,
    placeholder: 'Выберите хэштеги',
    load(query, callback) {
      if (!query.length || query.length < 2) return callback();

      fetch(`http://127.0.0.1:8080/api/hashtags?q=${encodeURIComponent(query)}`)
        .then(res => res.json())
        .then(json => callback(json))
        .catch(() => callback());
    },
    onItemAdd() {
      this.control_input.value = '';
      this.refreshOptions(false);
      currentFilters.hashtags = this.getValue().map(v => parseInt(v, 10));
      currentFilters.offset = 0;
      loadCards();
      document.querySelector('.ts-control').classList.add('has-items');
    },
  });
  choicesInstance.control.addEventListener('click', function (event) {
    const tag = event.target.closest('.item');
    if (tag) {
      const value = tag.getAttribute('data-value');
      if (value !== null) {
        choicesInstance.removeItem(value);
        currentFilters.hashtags = choicesInstance.getValue().map(v => parseInt(v, 10));
        currentFilters.offset = 0;
        loadCards();
        if (choicesInstance.items.length == 0) {
          reloadTomSelect();
        }
      }
    }
  });
}

function reloadTomSelect() {
  if (choicesInstance) {
    choicesInstance.destroy();  // уничтожаем текущий экземпляр
    choicesInstance = null;
  }
  initTomSelect(); // создаём новый экземпляр
}

document.getElementById('search').addEventListener('input', (e) => {
  currentFilters.search = e.target.value.trim();
  currentFilters.offset = 0; // сбрасываем для новой загрузки
  loadCards();
});

document.getElementById('category').addEventListener('change', (e) => {
  const val = e.target.value;
  currentFilters.category = val === '' ? null : parseInt(val, 10);
  currentFilters.offset = 0;
  loadCards();
});

initTomSelect();
loadCards();
loadCategories();
