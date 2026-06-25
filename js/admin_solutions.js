// admin_solutions.js
import * as auth from './authorizationFunctions.js';

// Теперь используем градиентный фон вместо внешних изображений

let editProblemsTomSelect; // Для связанных проблем в модале

let currentFilters = {
  search: '',
  category: null,
  isNew: false,
  limit: 50,
  offset: 0
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
    loadCategories();
    loadCards();
    initModal();
    await loadProblemsForModal();
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
    if (event.target.closest('.favorite-icon')) return;
    const card = event.target.closest('.card');
    if (card) {
        const solutionId = card.getAttribute('data-solution-id');
        if (solutionId && solutionId.trim()) {
            event.preventDefault();
            event.stopPropagation();
            loadSolutionById(solutionId).then(solution => {
                fillEditForm(solution);
                const modal = document.getElementById('editModal');
                const content = modal.querySelector('.modal-content');
                
                // Создаем или получаем style элемент для принудительных стилей
                let forceStyle = document.getElementById('force-editModal-style');
                if (!forceStyle) {
                    forceStyle = document.createElement('style');
                    forceStyle.id = 'force-editModal-style';
                    document.head.appendChild(forceStyle);
                }
                
                // Функция для полноэкранного модального окна
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
                alert('Ошибка загрузки решения: ' + err.message);
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
        if (editProblemsTomSelect) editProblemsTomSelect.clear();
        document.getElementById('relatedInfo').innerHTML = '';
        document.getElementById('currentImagePreview').innerHTML = '';
    });

    deleteBtn.addEventListener('click', () => {
        const solutionId = document.getElementById('solutionId').value;
        if (confirm('Удалить решение?')) {
            deleteSolution(solutionId).then(() => {
                modal.style.display = 'none';
                loadCards();
            }).catch(err => alert('Ошибка удаления: ' + err.message));
        }
    });

    document.getElementById('editForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const solutionId = document.getElementById('solutionId').value;
        if (!solutionId) {
            alert('ID решения не найден');
            return;
        }
        
        const formData = new FormData();
        formData.append('name', document.getElementById('editName').value.trim());
        formData.append('describe', document.getElementById('editDescribe').value.trim());
        
        const problemValues = editProblemsTomSelect ? (editProblemsTomSelect.getValue() || []) : [];
        formData.append('relatedProblems', Array.isArray(problemValues) ? problemValues.join(',') : '');
        
        const imageFile = document.getElementById('editImage').files[0];
        if (imageFile) {
            formData.append('image', imageFile);
        }
        
        const price = document.getElementById('editPrice').value;
        if (price) formData.append('price', price);
        
        const efficiency = document.getElementById('editEfficiency').value;
        if (efficiency) formData.append('efficiency', efficiency);
        
        const complexity = document.getElementById('editComplexity').value;
        if (complexity) formData.append('complexity', complexity);
        
        const time = document.getElementById('editTime').value;
        if (time) formData.append('time', time);
        
        formData.append('isNew', document.getElementById('editIsNew').checked ? 'true' : 'false');
        formData.append('fromAuthor', document.getElementById('editFromAuthor').checked ? 'true' : 'false');
        formData.append('canBuy', document.getElementById('editIsBought').checked ? 'on' : '');
        formData.append('canEvaluate', document.getElementById('editIsRating').checked ? 'on' : '');
        
        try {
            await updateSolution(solutionId, formData);
            alert('Решение успешно обновлено');
            const modal = document.getElementById('editModal');
            modal.style.display = 'none';
            modal.classList.remove('active');
            loadCards();
        } catch (err) {
            alert('Ошибка сохранения: ' + err.message);
        }
    });
}

async function loadSolutionById(solutionId) {
    try {
        const token = localStorage.getItem('accessToken');
        const response = await fetch(API_CONFIG.buildURL(`/solutions/${solutionId}`), {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const solution = await response.json();
        
        if (!solution) {
            throw new Error('Решение не найдено');
        }
        
        return solution;
    } catch (err) {
        console.error('Error loading solution:', err);
        throw err;
    }
}

function fillEditForm(solution) {
    document.getElementById('solutionId').value = solution.ID;
    document.getElementById('editName').value = solution.Name || '';
    document.getElementById('editDescribe').value = solution.Describe || '';
    
    if (editProblemsTomSelect) {
        const problemIds = (solution.Problems && solution.Problems.length)
            ? solution.Problems.map(p => (p.ID ?? p.id).toString())
            : [];
        editProblemsTomSelect.setValue(problemIds);
    }
    
    const num = (v) => (v !== undefined && v !== null && v !== '') ? v : '';
    document.getElementById('editPrice').value = num(solution.Price ?? solution.price);
    document.getElementById('editEfficiency').value = num(solution.Efficiency ?? solution.efficiency);
    document.getElementById('editComplexity').value = num(solution.Complexity ?? solution.complexity);
    document.getElementById('editTime').value = num(solution.Time ?? solution.time);
    
    const bool = (v) => !!v;
    document.getElementById('editIsNew').checked = bool(solution.IsNew ?? solution.isnew);
    document.getElementById('editFromAuthor').checked = bool(solution.FromAuthor ?? solution.fromauthor);
    document.getElementById('editIsBought').checked = bool(solution.IsBought ?? solution.isbought);
    document.getElementById('editIsRating').checked = bool(solution.IsRating ?? solution.israting);

    let relatedHtml = '';
    if (solution.Comments && solution.Comments.length > 0) {
        relatedHtml += `<p><strong>Комментарии:</strong> ${solution.Comments.length}</p>`;
    }
    document.getElementById('relatedInfo').innerHTML = relatedHtml;

    const previewDiv = document.getElementById('currentImagePreview');
    previewDiv.innerHTML = '';
    if (solution.Image) {
        const imgPreview = document.createElement('img');
        imgPreview.src = solution.Image.startsWith('http') ? solution.Image : `${solution.Image}`;
        imgPreview.style.maxWidth = '200px';
        imgPreview.style.maxHeight = '200px';
        imgPreview.style.borderRadius = '4px';
        imgPreview.style.marginTop = '10px';
        const label = document.createElement('p');
        label.textContent = 'Текущее изображение:';
        label.style.margin = '0 0 5px 0';
        previewDiv.appendChild(label);
        previewDiv.appendChild(imgPreview);
    }
}

async function updateSolution(id, formData) {
    const token = localStorage.getItem('accessToken');
    const response = await fetch(API_CONFIG.buildURL(`/solutions/${id}`), {
        method: 'PUT',
        headers: {
            'Authorization': `Bearer ${token}`
        },
        body: formData
    });
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'Неизвестная ошибка' }));
        throw new Error(errorData.error || 'Ошибка HTTP: ' + response.status);
    }
    return await response.json();
}

async function deleteSolution(id) {
    const token = localStorage.getItem('accessToken');
    const response = await fetch(API_CONFIG.buildURL(`/solutions/${id}`), {
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

async function loadProblemsForModal() {
    try {
        const token = localStorage.getItem('accessToken');
        editProblemsTomSelect = new TomSelect('#editProblems', {
            // Меняем дефолтный wrapperClass="ts-wrapper" на свой
            wrapperClass: 'vs-wrapper',
            controlClass: 'ts-control vs-control',
            plugins: ['remove_button'],
            multiple: true,
            placeholder: 'Выберите связанные проблемы',
            searchField: ['text'],
            valueField: 'value',
            labelField: 'text',
            load: function (query, callback) {
                if (query.length < 2) return callback();
                
                fetch(API_CONFIG.buildURLWithParams(API_CONFIG.ENDPOINTS.PROBLEMS, {search: query, limit: 20}), {
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    }
                })
                    .then(res => {
                        if (!res.ok) throw new Error('Ошибка загрузки проблем');
                        return res.json();
                    })
                    .then(data => {
                        const options = data.map(item => ({
                            value: item.ID.toString(),
                            text: item.Name
                        }));
                        callback(options);
                    })
                    .catch(err => {
                        console.error('Ошибка загрузки проблем:', err);
                        callback();
                    });
            },
            render: {
                option: function (item, escape) {
                    return `<div>${escape(item.text)}</div>`;
                },
                item: function (item, escape) {
                    return `<div>${escape(item.text)}</div>`;
                }
            }
        });
    } catch (error) {
        console.error('Ошибка инициализации TomSelect для проблем:', error);
    }
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

    const params = new URLSearchParams();
    if (currentFilters.search) params.append('search', currentFilters.search);
    if (currentFilters.category != null) params.append('category', currentFilters.category);
    if (currentFilters.isNew) params.append('isnew', 'true');
    params.append('limit', currentFilters.limit);
    params.append('offset', currentFilters.offset);

    try {
        const response = await fetch(API_CONFIG.buildURL(`/solutions?${params.toString()}`), { cache: 'no-store' });
        if (!response.ok) throw new Error('Ошибка HTTP: ' + response.status);
        const data = await response.json();
        const list = (data && data.solutions !== undefined) ? data.solutions : (Array.isArray(data) ? data : []);
        sortAndRender(list);
    } catch (error) {
        container.innerHTML = `<p style="color:red; text-align:center">Ошибка загрузки данных: ${error.message}</p>`;
    }
}

async function loadCategories() {
    try {
        const response = await fetch(API_CONFIG.buildURL(API_CONFIG.ENDPOINTS.CATEGORIES));
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

document.getElementById('search').addEventListener('input', (e) => {
    currentFilters.search = e.target.value;
    currentFilters.offset = 0;
    loadCards();
});

document.getElementById('category').addEventListener('change', (e) => {
    currentFilters.category = e.target.value || null;
    currentFilters.offset = 0;
    loadCards();
});

function sortAndRender(data) {
    const container = document.querySelector('.cards-container');
    container.innerHTML = '';

    if (data.length === 0) {
        container.innerHTML = '<p style="text-align:center">Нет решений для отображения</p>';
        return;
    }

    data.forEach(solution => {
        const template = document.getElementById('card-template');
        const clone = template.content.cloneNode(true);
        const card = clone.querySelector('.card');
        card.setAttribute('data-solution-id', solution.ID);
        card.style.cursor = 'pointer';

        const img = clone.querySelector('.card-image');
        const cardImageWrapper = clone.querySelector('.card-image-wrapper');
        
        // Функция для fallback-изображения по названию (SVG)
        function getImageFromInternet(solutionName) {
            if (!solutionName || solutionName.trim() === '') {
                return null;
            }
            
            // Создаем хеш от названия для получения стабильного изображения
            let hash = 0;
            for (let i = 0; i < solutionName.length; i++) {
                const char = solutionName.charCodeAt(i);
                hash = ((hash << 5) - hash) + char;
                hash = hash & hash;
            }
            
            const imageId = Math.abs(hash) % 1000;
            
            // Цвета для градиента на основе хеша
            const colors = [
                ['#667eea', '#764ba2'], ['#f093fb', '#f5576c'], ['#4facfe', '#00f2fe'],
                ['#43e97b', '#38f9d7'], ['#fa709a', '#fee140'], ['#30cfd0', '#330867'],
                ['#a8edea', '#fed6e3'], ['#d299c2', '#fef9d7'], ['#ff9a9e', '#fecfef'],
                ['#ffecd2', '#fcb69f'],
            ];
            
            const colorPair = colors[imageId % colors.length];
            const displayText = solutionName.trim().replace(/[<>]/g, '').substring(0, 30);
            
            const svg = `
                <svg xmlns="http://www.w3.org/2000/svg" width="400" height="300" viewBox="0 0 400 300">
                    <defs>
                        <linearGradient id="grad${imageId}" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" style="stop-color:${colorPair[0]};stop-opacity:1" />
                            <stop offset="100%" style="stop-color:${colorPair[1]};stop-opacity:1" />
                        </linearGradient>
                    </defs>
                    <rect width="400" height="300" fill="url(#grad${imageId})"/>
                    <text x="50%" y="50%" text-anchor="middle" fill="white" font-family="Arial, sans-serif" 
                          font-size="24" font-weight="bold" dy=".3em">
                        ${displayText}
                    </text>
                </svg>
            `;
            
            return 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg);
        }
        
        const imgUrl = (solution.Image || solution.image || '').trim() || null;
        const normalizedSrc = imgUrl
            ? (imgUrl.startsWith('/') ? imgUrl : (imgUrl.startsWith('http') ? imgUrl : '/' + imgUrl.replace(/^\//, '')))
            : null;
        if (normalizedSrc) {
            img.src = normalizedSrc;
            img.style.display = 'block';
            if (cardImageWrapper) cardImageWrapper.style.background = 'none';
            img.onerror = function() {
                const fallback = getImageFromInternet(solution.Name);
                if (fallback) {
                    this.src = fallback;
                    if (cardImageWrapper) cardImageWrapper.style.background = 'none';
                } else {
                    this.style.display = 'none';
                    if (cardImageWrapper) cardImageWrapper.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
                }
            };
        } else {
            const fallback = getImageFromInternet(solution.Name);
            if (fallback) {
                img.src = fallback;
                img.style.display = 'block';
                if (cardImageWrapper) cardImageWrapper.style.background = 'none';
                img.onerror = function() {
                    this.style.display = 'none';
                    if (cardImageWrapper) cardImageWrapper.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
                };
            } else {
                img.style.display = 'none';
                if (cardImageWrapper) cardImageWrapper.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
            }
        }
        img.alt = solution.Name;

        const titleText = clone.querySelector('.card-title-text');
        titleText.textContent = solution.Name;

        const favoriteCount = clone.querySelector('.favorite-count');
        favoriteCount.textContent = solution.Favourite || 0;

        const viewsStat = clone.querySelector('.views .stat-value');
        viewsStat.textContent = solution.Show || 0;
        const commentsStat = clone.querySelector('.comments .stat-value');
        commentsStat.textContent = solution.Comments ? solution.Comments.length : 0;
        const linksStat = clone.querySelector('.links .stat-value');
        linksStat.textContent = solution.Problems ? solution.Problems.length : 0;
        container.appendChild(clone);
    });
}

// Обработчик "Добавить решение" - теперь открывает модальное окно
// Логика перенесена в modalSolution.js

