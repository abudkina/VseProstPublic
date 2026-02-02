// admin_categories.js
import * as auth from './authorizationFunctions.js';

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
    const item = event.target.closest('[data-category-id]');
    if (item) {
        const categoryId = item.getAttribute('data-category-id');
        if (categoryId) {
            event.preventDefault();
            loadCategoryById(categoryId).then(category => {
                fillEditForm(category);
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
                setTimeout(centerModal, 10); setTimeout(centerModal, 50); setTimeout(centerModal, 100); setTimeout(centerModal, 200);
                window.addEventListener('resize', centerModal);
                window.addEventListener('scroll', centerModal);
            }).catch(err => {
                alert('Ошибка загрузки категории: ' + err.message);
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
        const categoryId = document.getElementById('categoryId').value;
        if (confirm('Удалить категорию?')) {
            deleteCategory(categoryId).then(() => {
                modal.style.display = 'none';
                modal.classList.remove('active');
                loadCards();
            }).catch(err => alert('Ошибка удаления: ' + err.message));
        }
    });

    document.getElementById('editForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const categoryId = document.getElementById('categoryId').value;
        if (!categoryId) {
            alert('ID категории не найден');
            return;
        }
        
        const data = {
            name: document.getElementById('editName').value.trim(),
            isnew: document.getElementById('editIsNew').checked
        };
        
        try {
            await updateCategory(categoryId, data);
            alert('Категория успешно обновлена');
            const modal = document.getElementById('editModal');
            modal.style.display = 'none';
            modal.classList.remove('active');
            loadCards();
        } catch (err) {
            alert('Ошибка сохранения: ' + err.message);
        }
    });
}

async function loadCategoryById(categoryId) {
    try {
        const token = localStorage.getItem('accessToken');
        const response = await fetch(API_CONFIG.buildURL(API_CONFIG.ENDPOINTS.CATEGORIES), {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const categories = await response.json();
        const category = categories.find(c => c.ID == categoryId);
        
        if (!category) {
            throw new Error('Категория не найдена');
        }
        
        return category;
    } catch (err) {
        console.error('Error loading category:', err);
        throw err;
    }
}

function fillEditForm(category) {
    document.getElementById('categoryId').value = category.ID || category.id;
    document.getElementById('editName').value = category.Name || category.name || '';
    document.getElementById('editIsNew').checked = category.isnew || category.is_new || false;
}

async function updateCategory(id, data) {
    const token = localStorage.getItem('accessToken');
    const response = await fetch(API_CONFIG.buildURL(`/categories/${id}`), {
        method: 'PUT',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    });
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'Неизвестная ошибка' }));
        throw new Error(errorData.error || 'Ошибка HTTP: ' + response.status);
    }
    return await response.json();
}

async function deleteCategory(id) {
    const token = localStorage.getItem('accessToken');
    const response = await fetch(API_CONFIG.buildURL(`/categories/${id}`), {
        method: 'DELETE',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        }
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
        const response = await fetch(API_CONFIG.buildURL(API_CONFIG.ENDPOINTS.CATEGORIES), {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        if (!response.ok) throw new Error('Ошибка HTTP: ' + response.status);
        const categories = await response.json();
        
        let filtered = categories;
        if (currentFilters.search) {
            filtered = filtered.filter(c => 
                c.Name.toLowerCase().includes(currentFilters.search.toLowerCase())
            );
        }
        if (currentFilters.isNew) {
            filtered = filtered.filter(c => c.isnew);
        }
        
        renderCategories(filtered);
    } catch (error) {
        container.innerHTML = `<p style="color:red; text-align:center">Ошибка загрузки данных: ${error.message}</p>`;
    }
}

function renderCategories(categories) {
    const container = document.querySelector('.cards-container');
    container.innerHTML = '';

    if (categories.length === 0) {
        container.innerHTML = '<p style="text-align:center">Нет категорий для отображения</p>';
        return;
    }

    categories.forEach(category => {
        const div = document.createElement('div');
        div.className = 'card';
        div.setAttribute('data-category-id', category.ID || category.id);
        const badges = [];
        if (category.isnew || category.is_new) badges.push('<span class="badge new">Новая</span>');
        div.innerHTML = `
            <h3>${category.Name || category.name || 'Без названия'}</h3>
            ${badges.length > 0 ? `<div style="margin-top: 12px;">${badges.join('')}</div>` : ''}
        `;
        container.appendChild(div);
    });
}

document.getElementById('search').addEventListener('input', (e) => {
    currentFilters.search = e.target.value;
    loadCards();
});

