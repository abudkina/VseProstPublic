// admin_hashtags.js
import * as auth from './authorizationFunctions.js';

let currentFilters = {
  search: '',
  isNew: false,
  limit: 50,
  offset: 0
};

window.addEventListener('load', async function() {
    // Проверяем авторизацию перед загрузкой
    try {
        await auth.checkAuth(true);
    } catch (error) {
        console.error('Ошибка авторизации:', error);
        return;
    }
    
    loadCards();
    initModal();
});

document.getElementById('favoritesLink').addEventListener('click', function(e) {
    e.preventDefault();
    if (!localStorage.getItem('isLoggedIn')) {
        sessionStorage.setItem('redirectAfterLogin', '/html/favourites.html');
        window.location.href = '/html/authorization.html';
        return;
    }
    auth.checkAuth(true).then(userID => {
        window.location.href = '/html/favourites.html';
    }).catch(() => {});
});

document.getElementById('profileBtn').addEventListener('click', () => {
    auth.checkAuth(false).then(userID => {
        window.location.href = '/html/profile.html';
    }).catch(() => {
        sessionStorage.setItem('redirectAfterLogin', window.location.href);
        window.location.href = '/html/authorization.html';
    });
});

document.addEventListener('click', (event) => {
    const item = event.target.closest('[data-hashtag-id]');
    if (item) {
        const hashtagId = item.getAttribute('data-hashtag-id');
        if (hashtagId) {
            event.preventDefault();
            loadHashtagById(hashtagId).then(hashtag => {
                fillEditForm(hashtag);
                const modal = document.getElementById('editModal');
                modal.style.display = 'flex';
                modal.classList.add('active');
            }).catch(err => {
                alert('Ошибка загрузки хэштега: ' + err.message);
            });
        }
    }
});

function initModal() {
    const modal = document.getElementById('editModal');
    const closeBtn = modal.querySelector('.close');
    const clearBtn = document.getElementById('clearBtn');
    const deleteBtn = document.getElementById('deleteBtn');

    // Явно скрываем модальное окно при инициализации
    if (modal) {
        modal.style.display = 'none';
        modal.classList.remove('active');
    }

    closeBtn.addEventListener('click', () => { 
        modal.style.display = 'none';
        modal.classList.remove('active');
    });
    window.addEventListener('click', (e) => { 
        if (e.target === modal) {
            modal.style.display = 'none';
            modal.classList.remove('active');
        }
    });

    clearBtn.addEventListener('click', () => {
        document.getElementById('editForm').reset();
    });

    deleteBtn.addEventListener('click', () => {
        const hashtagId = document.getElementById('hashtagId').value;
        if (confirm('Удалить хэштег?')) {
            deleteHashtag(hashtagId).then(() => {
                modal.style.display = 'none';
                modal.classList.remove('active');
                loadCards();
            }).catch(err => alert('Ошибка удаления: ' + err.message));
        }
    });

    document.getElementById('editForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const hashtagId = document.getElementById('hashtagId').value;
        if (!hashtagId) {
            alert('ID хэштега не найден');
            return;
        }
        
        const data = {
            name: document.getElementById('editName').value.trim(),
            show: parseInt(document.getElementById('editShow').value) || 0,
            isnew: document.getElementById('editIsNew').checked
        };
        
        try {
            await updateHashtag(hashtagId, data);
            alert('Хэштег успешно обновлен');
            const modal = document.getElementById('editModal');
            modal.style.display = 'none';
            modal.classList.remove('active');
            loadCards();
        } catch (err) {
            alert('Ошибка сохранения: ' + err.message);
        }
    });
}

async function loadHashtagById(hashtagId) {
    try {
        const response = await fetch(API_CONFIG.buildURL(API_CONFIG.ENDPOINTS.HASHTAGS), {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include' // Важно для отправки cookies с токеном
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const result = await response.json();
        const hashtags = result.hashtags || result;
        const hashtag = Array.isArray(hashtags) ? hashtags.find(h => h.ID == hashtagId || h.id == hashtagId) : null;
        
        if (!hashtag) {
            throw new Error('Хэштег не найден');
        }
        
        // Нормализуем формат
        return {
            ID: hashtag.ID || hashtag.id,
            Name: hashtag.Name || hashtag.name,
            show: hashtag.show || 0,
            isnew: hashtag.isnew || hashtag.is_new || false
        };
    } catch (err) {
        console.error('Error loading hashtag:', err);
        throw err;
    }
}

function fillEditForm(hashtag) {
    document.getElementById('hashtagId').value = hashtag.ID || hashtag.id;
    document.getElementById('editName').value = hashtag.Name || hashtag.name || '';
    document.getElementById('editShow').value = hashtag.show || 0;
    document.getElementById('editIsNew').checked = hashtag.isnew || hashtag.is_new || false;
}

async function updateHashtag(id, data) {
    const response = await fetch(API_CONFIG.buildURL(`/hashtags/${id}`), {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        credentials: 'include', // Важно для отправки cookies с токеном
        body: JSON.stringify(data)
    });
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'Неизвестная ошибка' }));
        throw new Error(errorData.error || 'Ошибка HTTP: ' + response.status);
    }
    return await response.json();
}

async function deleteHashtag(id) {
    const response = await fetch(API_CONFIG.buildURL(`/hashtags/${id}`), {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json'
        },
        credentials: 'include' // Важно для отправки cookies с токеном
    });
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'Неизвестная ошибка' }));
        throw new Error(errorData.error || 'Ошибка HTTP: ' + response.status);
    }
    return await response.json();
}

document.getElementById('newBtn').addEventListener('click', () => {
    currentFilters.isNew = !currentFilters.isNew;
    document.getElementById('newBtn').classList.toggle('active', currentFilters.isNew);
    currentFilters.offset = 0;
    loadCards();
});

async function loadCards() {
    const container = document.querySelector('.cards-container');
    container.innerHTML = 'Загрузка...';

    try {
        const response = await fetch(API_CONFIG.buildURL(API_CONFIG.ENDPOINTS.HASHTAGS), {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include' // Важно для отправки cookies с токеном
        });
        
        if (response.status === 401) {
            // Попробуем обновить токен и повторить запрос
            try {
                await auth.refreshToken();
                const retryResponse = await fetch(API_CONFIG.buildURL(API_CONFIG.ENDPOINTS.HASHTAGS), {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    credentials: 'include'
                });
                if (!retryResponse.ok) throw new Error('Ошибка HTTP: ' + retryResponse.status);
                const result = await retryResponse.json();
                const hashtags = result.hashtags || (Array.isArray(result) ? result : []);
                processHashtags(hashtags);
                return;
            } catch (refreshError) {
                throw new Error('Требуется авторизация');
            }
        }
        
        if (!response.ok) throw new Error('Ошибка HTTP: ' + response.status);
        const result = await response.json();
        const hashtags = result.hashtags || (Array.isArray(result) ? result : []);
        processHashtags(hashtags);
    } catch (error) {
        container.innerHTML = `<p style="color:red; text-align:center">Ошибка загрузки данных: ${error.message}</p>`;
    }
}

function processHashtags(hashtags) {
        
    let filtered = hashtags;
    if (currentFilters.search) {
        filtered = filtered.filter(h => {
            const name = (h.Name || h.name || '').toLowerCase();
            return name.includes(currentFilters.search.toLowerCase());
        });
    }
    if (currentFilters.isNew) {
        filtered = filtered.filter(h => h.isnew || h.is_new);
    }
    
    renderHashtags(filtered);
}

function renderHashtags(hashtags) {
    const container = document.querySelector('.cards-container');
    container.innerHTML = '';

    if (hashtags.length === 0) {
        container.innerHTML = '<p style="text-align:center">Нет хэштегов для отображения</p>';
        return;
    }

    hashtags.forEach(hashtag => {
        const div = document.createElement('div');
        div.className = 'card';
        div.setAttribute('data-hashtag-id', hashtag.ID || hashtag.id);
        const badges = [];
        if (hashtag.isnew || hashtag.is_new) badges.push('<span class="badge new">Новый</span>');
        div.innerHTML = `
            <h3>#${hashtag.Name || hashtag.name || 'Без названия'}</h3>
            <p><strong>Показов:</strong> ${hashtag.show || 0}</p>
            ${badges.length > 0 ? `<div style="margin-top: 12px;">${badges.join('')}</div>` : ''}
        `;
        container.appendChild(div);
    });
}

document.getElementById('search').addEventListener('input', (e) => {
    currentFilters.search = e.target.value;
    currentFilters.offset = 0;
    loadCards();
});

