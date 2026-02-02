// admin_topics.js
import * as auth from './authorizationFunctions.js';
import { getAuthHeaders } from './authorizationFunctions.js';

let currentFilters = {
  search: '',
  isNew: false
};

window.addEventListener('load', async function() {
    if (localStorage.getItem('isLoggedIn')) {
        auth.checkAuth(false).catch(() => {
            localStorage.removeItem('isLoggedIn');
        });
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
    const item = event.target.closest('[data-topic-id]');
    if (item) {
        const topicId = item.getAttribute('data-topic-id');
        if (topicId) {
            event.preventDefault();
            loadTopicById(topicId).then(topic => {
                fillEditForm(topic);
                const modal = document.getElementById('editModal');
                const content = modal.querySelector('.modal-content');
                
                let forceStyle = document.getElementById('force-editModal-style');
                if (!forceStyle) {
                    forceStyle = document.createElement('style');
                    forceStyle.id = 'force-editModal-style';
                    document.head.appendChild(forceStyle);
                }
                
                const centerModal = () => {
                    forceStyle.textContent = `
                        #editModal {
                            display: block !important;
                            position: fixed !important;
                            left: 0 !important;
                            right: 0 !important;
                            top: 0 !important;
                            bottom: 0 !important;
                            width: 100% !important;
                            height: 100% !important;
                            margin: 0 !important;
                            padding: 0 !important;
                            background: linear-gradient(135deg, rgba(0, 0, 0, 0.6) 0%, rgba(0, 0, 0, 0.8) 100%) !important;
                            backdrop-filter: blur(4px) !important;
                            -webkit-backdrop-filter: blur(4px) !important;
                            z-index: 10000 !important;
                            overflow: auto !important;
                            box-sizing: border-box !important;
                        }
                        #editModal .modal-content {
                            position: relative !important;
                            left: auto !important;
                            right: auto !important;
                            top: auto !important;
                            transform: none !important;
                            width: 100% !important;
                            max-width: 100% !important;
                            height: 100% !important;
                            max-height: 100% !important;
                            margin: 0 !important;
                            padding: 20px !important;
                            background: linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%) !important;
                            border-radius: 0 !important;
                            box-shadow: none !important;
                            overflow-y: auto !important;
                            display: flex !important;
                            flex-direction: column !important;
                        }
                    `;
                };
                centerModal();
                modal.classList.add('active');
                setTimeout(centerModal, 10);
                setTimeout(centerModal, 50);
                setTimeout(centerModal, 100);
                window.addEventListener('resize', centerModal);
            }).catch(err => {
                alert('Ошибка загрузки темы: ' + err.message);
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
        const topicId = document.getElementById('topicId').value;
        if (confirm('Удалить тему?')) {
            deleteTopic(topicId).then(() => {
                modal.style.display = 'none';
                modal.classList.remove('active');
                loadCards();
            }).catch(err => alert('Ошибка удаления: ' + err.message));
        }
    });

    document.getElementById('editForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const topicId = document.getElementById('topicId').value;
        if (!topicId) {
            alert('ID темы не найден');
            return;
        }
        
        const data = {
            name: document.getElementById('editName').value.trim(),
            is_new: document.getElementById('editIsNew').checked
        };
        
        try {
            await updateTopic(topicId, data);
            alert('Тема успешно обновлена');
            const modal = document.getElementById('editModal');
            modal.style.display = 'none';
            modal.classList.remove('active');
            loadCards();
        } catch (err) {
            alert('Ошибка сохранения: ' + err.message);
        }
    });
}

async function loadTopicById(topicId) {
    try {
        const response = await fetch(API_CONFIG.buildURL(`/topics/${topicId}`), {
            headers: getAuthHeaders(),
            credentials: 'include'
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const topic = await response.json();
        
        if (!topic) {
            throw new Error('Тема не найдена');
        }
        
        return topic;
    } catch (err) {
        console.error('Error loading topic:', err);
        throw err;
    }
}

function fillEditForm(topic) {
    document.getElementById('topicId').value = topic.ID || topic.id;
    document.getElementById('editName').value = topic.Name || topic.name || '';
    document.getElementById('editIsNew').checked = topic.is_new || topic.isnew || false;
}

async function updateTopic(id, data) {
    const response = await fetch(API_CONFIG.buildURL(`/topics/${id}`), {
        method: 'PUT',
        headers: getAuthHeaders(),
        credentials: 'include',
        body: JSON.stringify(data)
    });
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'Неизвестная ошибка' }));
        throw new Error(errorData.error || 'Ошибка HTTP: ' + response.status);
    }
    return await response.json();
}

async function deleteTopic(id) {
    const response = await fetch(API_CONFIG.buildURL(`/topics/${id}`), {
        method: 'DELETE',
        headers: getAuthHeaders(),
        credentials: 'include'
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
    loadCards();
});

async function loadCards() {
    const container = document.querySelector('.cards-container');
    container.innerHTML = 'Загрузка...';

    try {
        const token = localStorage.getItem('accessToken');
        // Загружаем все темы для админки
        const headers = {
            'Content-Type': 'application/json'
        };
        // Добавляем Authorization только если токен есть и он валидный
        if (token && token !== 'null' && token !== 'undefined') {
            headers['Authorization'] = `Bearer ${token}`;
        }
        const response = await fetch(API_CONFIG.buildURLWithParams(API_CONFIG.ENDPOINTS.TOPICS, {all: true}), {
            headers: headers,
            credentials: 'include'  // Важно для работы с cookies
        });
        if (!response.ok) throw new Error('Ошибка HTTP: ' + response.status);
        let topics = await response.json();
        
        let filtered = topics || [];
        if (currentFilters.search) {
            filtered = filtered.filter(t => {
                const name = (t.Name || t.name || '').toLowerCase();
                return name.includes(currentFilters.search.toLowerCase());
            });
        }
        if (currentFilters.isNew) {
            filtered = filtered.filter(t => t.is_new || t.isnew);
        }
        
        renderTopics(filtered);
    } catch (error) {
        container.innerHTML = `<p style="color:red; text-align:center">Ошибка загрузки данных: ${error.message}</p>`;
    }
}

function renderTopics(topics) {
    const container = document.querySelector('.cards-container');
    container.innerHTML = '';

    if (topics.length === 0) {
        container.innerHTML = '<p style="text-align:center">Нет тем для отображения</p>';
        return;
    }

    topics.forEach(topic => {
        const div = document.createElement('div');
        div.className = 'card';
        div.setAttribute('data-topic-id', topic.ID || topic.id);
        const badges = [];
        if (topic.is_new || topic.isnew) badges.push('<span class="badge new">Новая</span>');
        div.innerHTML = `
            <h3>${topic.Name || topic.name || 'Без названия'}</h3>
            ${badges.length > 0 ? `<div style="margin-top: 12px;">${badges.join('')}</div>` : ''}
        `;
        container.appendChild(div);
    });
}

document.getElementById('search').addEventListener('input', (e) => {
    currentFilters.search = e.target.value;
    loadCards();
});

