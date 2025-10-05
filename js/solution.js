// Создаёт элемент с указанным тегом, классом и текстом (опционально)
function createElem(tag, className, text) {
  const el = document.createElement(tag);
  if (className) el.className = className;
  if (text) el.textContent = text;
  return el;
}

// Создаёт блок с иконкой и числом (иконки можно заменить на SVG или картинки)
function createIconWithCount(iconHTML, count, title) {
  const wrapper = createElem('div', 'icon-item');
  wrapper.title = title;
  wrapper.innerHTML = iconHTML + `<span>${count}</span>`;
  return wrapper;
}

// Создаёт блок рейтинга с подписью и числовым значением справа
function createRatingBlock(label, rating, solutionID) {
  const block = createElem('div', 'rating-block');
  const labelElem = createElem('span', 'rating-label', label);
  const starsElem = createInteractiveStars(solutionID);
  const valueElem = createElem('span', 'rating-value', rating.toString());
  block.append(labelElem, starsElem, valueElem);
  return block;
}

// Создаёт комментарий с лайками/дизлайками
function createComment(comment) {
  const commentDiv = createElem('div', 'comment');

  const textDiv = createElem('div', 'comment-text');
  textDiv.innerHTML = `<b>${comment.Creator.User}</b> (${comment.CreatedDate}): ${comment.Text}`;

  const votesDiv = createElem('div', 'comment-votes');

  // Лайк и дизлайк иконки (простой текст вместо иконок, можно заменить SVG)
  const likeBtn = createElem('button', 'like-btn');
  likeBtn.innerHTML = `<img src="../assets/icons/like_5527412.png" alt="Лайки" class="icon" />${comment.LikeCount}`;

  const unlikeBtn = createElem('button', 'unlike-btn');
  unlikeBtn.innerHTML = `<img src="../assets/icons/down_13646455.png" alt="НеЛайки" class="icon" />${comment.NotLikeCount}`;

  votesDiv.append(likeBtn, unlikeBtn);
  commentDiv.append(textDiv, votesDiv);

  return commentDiv;
}

function getParameterByName(name) {
  const url = window.location.href;
  const regex = new RegExp('[?&]' + name + '(=([^&#]*)|&|#|$)');
  const results = regex.exec(url);
  if (!results) return null;
  if (!results[2]) return '';
  return decodeURIComponent(results[2].replace(/\+/g, ' '));
}

function createInteractiveStars(solutionID) {
  const container = createElem('div', 'interactive-stars');
  container.title = 'Ваш рейтинг';

  const stars = [];
  let savedRating = Number(localStorage.getItem(`rating-solution-${solutionID}`)) || 0;
  let hoverRating = 0;

  for (let i = 1; i <= 5; i++) {
    const star = createElem('span', 'star');
    star.textContent = '☆';
    star.style.cursor = 'pointer';
    star.style.fontSize = '24px';
    star.style.transition = 'color 0.3s, transform 0.3s';

    star.addEventListener('mouseenter', () => {
      hoverRating = i;
      updateStars();
    });

    star.addEventListener('click', () => {
      savedRating = i;
      localStorage.setItem(`rating-solution-${solutionID}`, savedRating);
      updateStars();
      alert(`Вы оценили решение на ${savedRating} ⭐`);
    });

    container.appendChild(star);
    stars.push(star);
  }

  container.addEventListener('mouseleave', () => {
    hoverRating = 0;
    updateStars();
  });

  function updateStars() {
    const activeRating = hoverRating || savedRating;
    stars.forEach((star, idx) => {
      if (idx < activeRating) {
        star.textContent = '★';
        star.style.color = 'red';
        star.style.transform = 'scale(1.2)';
      } else {
        star.textContent = '☆';
        star.style.color = 'lightgray';
        star.style.transform = 'scale(1)';
      }
    });
  }

  updateStars();

  return container;
}

async function renderSolutionPage() {
  const solutionID = getParameterByName("solutionId");
    if (!solutionID) {
    throw new Error("Отсутствует параметр solutionId в URL");
  }
    const response = await fetch(`http://127.0.0.1:8080/api/solution?id=${solutionID}`);
    if (!response.ok) throw new Error('Ошибка HTTP: ' + response.status);
    const solution = await response.json();

  const container = document.getElementById('solutionContainer');
  container.innerHTML = '';

  if (!solution) {
    container.textContent = 'Решение не найдено.';
    return;
  }

  // Верхний блок с заголовком и иконками - в одной строке
  const headerRow = createElem('div', 'header-row');

  const title = createElem('h1', 'solution-title', solution.Name);
  headerRow.appendChild(title);

  // Блок иконок (top-block)
  const topBlock = createElem('div', 'top-block');
  topBlock.style.margin = '0'; // убираем внешние отступы, если нужно

  topBlock.appendChild(createIconWithCount('<img src="../assets/icons/eye_8979989.png" alt="Просмотры" class="icon" />', solution.Show, 'Просмотры'));
  topBlock.appendChild(createIconWithCount('<img src="../assets/icons/love_9318199.png" alt="Фавориты" class="icon" />', solution.Favourite, 'Избранное'));
  topBlock.appendChild(createIconWithCount('<img src="../assets/icons/like_5527412.png" alt="Лайки" class="icon" />', solution.Like, 'Лайки'));
  topBlock.appendChild(createIconWithCount('<img src="../assets/icons/down_13646455.png" alt="НеЛайки" class="icon" />', solution.NotLike, 'Дизлайки'));
  topBlock.appendChild(createIconWithCount('<img src="../assets/icons/link_13925097.png" alt="Ссылки" class="icon" />', solution.Reply, 'Ссылки'));

  headerRow.appendChild(topBlock);
  container.appendChild(headerRow);

  // Основной блок с картинкой слева и описанием справа
  const mainBlock = createElem('div', 'main-block');

  const img = createElem('img');
  img.src = solution.Image;
  img.alt = solution.Name;
  img.className = 'solution-image';
  mainBlock.appendChild(img);

  // Описание + рейтинги в одном блоке справа от картинки
  const descAndRatings = createElem('div', 'desc-and-ratings');

  const desc = createElem('p', 'solution-description', solution.Describe);
  descAndRatings.appendChild(desc);

  const ratingsWrapper = createElem('div', 'ratings-wrapper');
  ratingsWrapper.appendChild(createRatingBlock('Цена', solution.Price, solutionID));
  ratingsWrapper.appendChild(createRatingBlock('Эффективность', solution.Efficiency, solutionID));
  ratingsWrapper.appendChild(createRatingBlock('Сложность', solution.Complexity, solutionID));
  ratingsWrapper.appendChild(createRatingBlock('Время', solution.Time, solutionID));
  descAndRatings.appendChild(ratingsWrapper);

  mainBlock.appendChild(descAndRatings);
  container.appendChild(mainBlock);

  // Комментарии
  const commentsTitle = createElem('h2', 'comments-title', 'Комментарии');
  container.appendChild(commentsTitle);

  if (Array.isArray(solution.CommentSolutions) && solution.CommentSolutions.length > 0) {
    solution.CommentSolutions.forEach(comment => {
      container.appendChild(createComment(comment));
    });
  } else {
    const noComments = createElem('p', null, 'Комментариев пока нет.');
    container.appendChild(noComments);
  }

  // Поле для нового комментария
  const commentForm = createElem('form', 'comment-form');

  const textarea = document.createElement('textarea');
  textarea.placeholder = 'Напишите свой комментарий';
  textarea.rows = 3;

  const submitBtn = createElem('button', null, 'Отправить');
  submitBtn.type = 'submit';

  commentForm.append(textarea, submitBtn);
  container.appendChild(commentForm);

  // Обработка отправки комментария
  commentForm.addEventListener('submit', e => {
    e.preventDefault();
    if (!textarea.value.trim()) return alert('Введите текст комментария');
    // Добавляем комментарий в объект и на страницу
    const newComment = {
      date: new Date().toLocaleDateString('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' }),
      author: 'Пользователь',
      text: textarea.value.trim(),
      likes: 0,
      unlikes: 0
    };
    if (!Array.isArray(solution.comments)) {
      solution.comments = [];
    }
    solution.comments.push(newComment);
    container.insertBefore(createComment(newComment), commentForm);
    textarea.value = '';
  });
}

renderSolutionPage();
