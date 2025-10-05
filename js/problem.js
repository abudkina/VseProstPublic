// Функция для получения параметра из URL
function getParameterByName(name) {
    const url = window.location.href;
    const regex = new RegExp('[?&]' + name + '(=([^&#]*)|&|#|$)');
    const results = regex.exec(url);
    if (!results) return null;
    if (!results[2]) return '';
    return decodeURIComponent(results[2].replace(/\+/g, ' '));
}

// Загружаем данные из JSON файлов
async function loadData() {
    const problemID = getParameterByName("problemId");
    if (!problemID) {
    throw new Error("Отсутствует параметр problemId в URL");
  }
    const response = await fetch(`http://127.0.0.1:8080/api/problem?id=${problemID}`);
    if (!response.ok) throw new Error('Ошибка HTTP: ' + response.status);
    const data = await response.json();
    return data.problem ?? data;
}

// Отображаем информацию о проблеме и её решениях
async function displaySolutions() {
    const problem = await loadData();
    console.log("Получена задача:", problem);
    const solutionContainer = document.getElementById('solutionContainer');

    if (!problem) {
        solutionContainer.innerHTML = '<p>Проблема не найдена.</p>';
        return;
    }

    // Очищаем контейнер
    solutionContainer.innerHTML = '';

    // --- Создаем блок с информацией о проблеме ---
    const problemInfoTemplate = document.getElementById('problem-info-template');
    const problemInfo = problemInfoTemplate.content.cloneNode(true);

    const img = problemInfo.querySelector('.problem-img');
    img.src = problem.Image;
    img.alt = problem.Name;

    const title = problemInfo.querySelector('.problem-title');
    title.textContent = problem.Name;

    solutionContainer.appendChild(problemInfo);

    // --- Добавляем теги ---
    if (problem.Hashtags && problem.Hashtags.length > 0) {
        const tagsContainer = document.createElement('div');
        tagsContainer.className = 'tags';

        const tagTemplate = document.getElementById('tag-template');
        problem.Hashtags.forEach(tagText => {
            const tagNode = tagTemplate.content.cloneNode(true);
            tagNode.querySelector('.tag').textContent = `#${tagText.Name}`;
            tagsContainer.appendChild(tagNode);
        });

        solutionContainer.appendChild(tagsContainer);
    }

    // --- Добавляем карточки решений ---
    const cardsWrapper = document.createElement('div');
    cardsWrapper.className = 'cards-container';

    const cardTemplate = document.getElementById('solution-card-template');

    for (solution of problem.Solutions) {

        const card = cardTemplate.content.cloneNode(true);

        const link = card.querySelector('.card-title-link');
        link.href = `../html/solution.html?solutionId=${encodeURIComponent(solution.ID)}`;

        const cardImg = card.querySelector('.card-image');
        cardImg.src = solution.Image;
        cardImg.alt = solution.Name;

        card.querySelector('.likes-number').textContent = solution.Favourite || 0;
        card.querySelector('.rating-number').textContent = solution.Rating || 0;
        card.querySelector('.card-title-overlay').textContent = solution.Name;

        card.querySelector('.stat-item.likes .stat').innerHTML = `<img src="../assets/icons/like_5527412.png" alt="Лайки" class="icon" />${solution.like || 0}`;
        card.querySelector('.stat-item.unlikes .stat').innerHTML = `<img src="../assets/icons/down_13646455.png" alt="НеЛайки" class="icon" />${solution.notlike || 0}`;
        card.querySelector('.stat-item.views .stat').innerHTML = `<img src="../assets/icons/eye_8979989.png" alt="Просмотры" class="icon" />${solution.show || 0}`;
        const commentsCount = Array.isArray(solution.Comments) ? solution.Comments.length : 0;
        card.querySelector('.stat-item.comments .stat').innerHTML = `<img src="../assets/icons/message_2629755.png" alt="Комментарии" class="icon" />${commentsCount}`;
        card.querySelector('.stat-item.links .stat').innerHTML = `<img src="../assets/icons/link_13925097.png" alt="Ссылки" class="icon" />${solution.reply || 0}`;

        cardsWrapper.appendChild(card);
    }

    solutionContainer.appendChild(cardsWrapper);
}

displaySolutions();


