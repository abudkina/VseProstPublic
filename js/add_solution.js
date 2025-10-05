const hideBtn1 = document.getElementById('hideBtn1');
  const hideBtn2 = document.getElementById('hideBtn2');
  const form = document.getElementById('solutionForm');
  const clearBtn = document.getElementById('clearBtn');

  hideBtn1.addEventListener('click', () => {
    form.style.display = form.style.display === 'none' ? 'block' : 'none';
  });

  hideBtn2.addEventListener('click', () => {
    form.style.display = form.style.display === 'none' ? 'block' : 'none';
  });

  clearBtn.addEventListener('click', () => {
    form.reset();
  });

 // Новый обработчик для отправки формы
form.addEventListener('submit', async (e) => {
  e.preventDefault();

  // Собрать данные в FormData
  const formData = new FormData();
  formData.append('solution', document.getElementById('solution').value);
  formData.append('details', document.getElementById('details').value);
  formData.append('relatedProblems', document.getElementById('relatedProblems').value);
  formData.append('canBuy', document.getElementById('canBuy').checked ? 'on' : 'off');
  formData.append('canEvaluate', document.getElementById('canEvaluate').checked ? 'on' : 'off');

  // Добавить файлы
  const mainImage = document.getElementById('mainImage').files[0];
  const additionalImage = document.getElementById('additionalImage').files[0];
  if (mainImage) formData.append('mainImage', mainImage);
  if (additionalImage) formData.append('additionalImage', additionalImage);

  try {
    // Отправить на сервер
    const response = await fetch('http://127.0.0.1:8080/api/createSolution', {
      method: 'POST',
      body: formData,
    });

    if (response.ok) {
      const result = await response.json();
      alert('Решение добавлено успешно! ID: ' + result.id);
      form.reset(); // Очистить форму после успеха
    } else {
      const error = await response.json();
      alert('Ошибка: ' + error.error);
    }
  } catch (error) {
    alert('Ошибка сети: ' + error.message);
  }
});
