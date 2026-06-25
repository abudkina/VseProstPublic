// admin_comments.js
import * as auth from './authorizationFunctions.js';

let currentFilters = {
  search: '',
  isNew: false
};

(function() {
    const m = document.getElementById('editModal');
    if (m) { m.style.display = 'none'; m.classList.remove('active'); }
})();

window.addEventListener('load', async function() {
    const modal = document.getElementById('editModal');
    if (modal) { modal.style.display = 'none'; modal.classList.remove('active'); }
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
        sessionStorage.setItem('redirectAfterLogin', 'html/favourites.html');
        window.location.href = 'html/authorization.html';
        return;
    }
    auth.checkAuth(true).then(userID => {
        window.location.href = 'html/favourites.html';
    }).catch(() => {});
});

document.getElementById('profileBtn').addEventListener('click', () => {
    auth.checkAuth(false).then(userID => {
        window.location.href = 'html/profile.html';
    }).catch(() => {
        sessionStorage.setItem('redirectAfterLogin', window.location.href);
        window.location.href = 'html/authorization.html';
    });
});

document.addEventListener('click', (event) => {
    if (!event.isTrusted) return;
    const item = event.target.closest('[data-comment-id]');
    if (item) {
        const commentId = item.getAttribute('data-comment-id');
        if (commentId && commentId.trim()) {
            event.preventDefault();
            loadCommentById(commentId).then(comment => {
                fillEditForm(comment);
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
                        @media (min-width: 769px) {
                            #editModal .modal-content {
                                position: relative !important;
                                left: auto !important;
                                right: auto !important;
                                top: auto !important;
                                transform: none !important;
                                width: 75% !important;
                                max-width: 75% !important;
                                height: auto !important;
                                max-height: 90vh !important;
                                margin: auto !important;
                                padding: 20px !important;
                                background: linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%) !important;
                                border-radius: 20px !important;
                                box-shadow: 0 20px 60px rgba(0,0,0,0.3) !important;
                                overflow-y: auto !important;
                                display: flex !important;
                                flex-direction: column !important;
                            }
                        }
                        @media (max-width: 768px) {
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
                alert('Ошибка загрузки комментария: ' + err.message);
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
        const commentId = document.getElementById('commentId').value;
        if (confirm('Удалить комментарий?')) {
            deleteComment(commentId).then(() => {
                modal.style.display = 'none';
                modal.classList.remove('active');
                loadCards();
            }).catch(err => alert('Ошибка удаления: ' + err.message));
        }
    });

    document.getElementById('editForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const commentId = document.getElementById('commentId').value;
        if (!commentId) {
            alert('ID комментария не найден');
            return;
        }
        
        const data = {
            text: document.getElementById('editText').value.trim(),
            isnew: document.getElementById('editIsNew').checked
        };
        
        try {
            await updateComment(commentId, data);
            alert('Комментарий успешно обновлен');
            const modal = document.getElementById('editModal');
            modal.style.display = 'none';
            modal.classList.remove('active');
            loadCards();
        } catch (err) {
            alert('Ошибка сохранения: ' + err.message);
        }
    });
}

async function loadCommentById(commentId) {
    try {
        const token = localStorage.getItem('accessToken');
        const response = await fetch(API_CONFIG.buildURL('/comment-solutions'), {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const result = await response.json();
        const comment = result.comments ? result.comments.find(c => c.ID == commentId) : null;
        
        if (!comment) {
            throw new Error('Комментарий не найден');
        }
        
        return comment;
    } catch (err) {
        console.error('Error loading comment:', err);
        throw err;
    }
}

function fillEditForm(comment) {
    document.getElementById('commentId').value = comment.ID;
    document.getElementById('editText').value = comment.Text || '';
    document.getElementById('editIsNew').checked = comment.isnew || false;

    let relatedHtml = '';
    if (comment.Solution) {
        relatedHtml += `<p><strong>Решение:</strong> ${comment.Solution.Name}</p>`;
    }
    relatedHtml += `<p><strong>Лайков:</strong> ${comment.likecount || 0}</p>`;
    relatedHtml += `<p><strong>Дизлайков:</strong> ${comment.notlikecount || 0}</p>`;
    document.getElementById('relatedInfo').innerHTML = relatedHtml;
}

async function updateComment(id, data) {
    const token = localStorage.getItem('accessToken');
    const response = await fetch(API_CONFIG.buildURL(`/comment-solutions/${id}`), {
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

async function deleteComment(id) {
    const token = localStorage.getItem('accessToken');
    const response = await fetch(API_CONFIG.buildURL(`/comment-solutions/${id}`), {
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
        const response = await fetch(API_CONFIG.buildURL('/comment-solutions'), {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        if (!response.ok) throw new Error('Ошибка HTTP: ' + response.status);
        const result = await response.json();
        const comments = result.comments || [];
        
        let filtered = comments;
        if (currentFilters.search) {
            filtered = filtered.filter(c => 
                c.Text.toLowerCase().includes(currentFilters.search.toLowerCase())
            );
        }
        if (currentFilters.isNew) {
            filtered = filtered.filter(c => c.isnew);
        }
        
        renderComments(filtered);
    } catch (error) {
        container.innerHTML = `<p style="color:red; text-align:center">Ошибка загрузки данных: ${error.message}</p>`;
    }
}

function renderComments(comments) {
    const container = document.querySelector('.cards-container');
    container.innerHTML = '';

    if (comments.length === 0) {
        container.innerHTML = '<p style="text-align:center">Нет комментариев для отображения</p>';
        return;
    }

    comments.forEach(comment => {
        const div = document.createElement('div');
        div.className = 'card';
        div.setAttribute('data-comment-id', comment.ID);
        const badges = [];
        if (comment.isnew) badges.push('<span class="badge new">Новый</span>');
        const text = comment.Text || 'Без текста';
        const solutionName = comment.Solution ? comment.Solution.Name : 'Неизвестно';
        div.innerHTML = `
            <p>${text}</p>
            <div class="stats">
                <div class="stat-item"><strong>Решение:</strong> ${solutionName}</div>
                <div class="stat-item"><strong>👍</strong> ${comment.likecount || 0}</div>
                <div class="stat-item"><strong>👎</strong> ${comment.notlikecount || 0}</div>
            </div>
            ${badges.length > 0 ? `<div style="margin-top: 12px;">${badges.join('')}</div>` : ''}
        `;
        container.appendChild(div);
    });
}

document.getElementById('search').addEventListener('input', (e) => {
    currentFilters.search = e.target.value;
    loadCards();
});

