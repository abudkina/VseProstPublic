import * as auth from './authorizationFunctions.js';

   document.getElementById('authorizationBtn').addEventListener('click', function() {
        // Переход на страницу авторизации
        window.location.href = '../html/authorization.html';
    });

  document.addEventListener('DOMContentLoaded', () => {
    const registerBtn = document.getElementById('registerBtn');
        registerBtn.addEventListener('click', (e) => {
            e.preventDefault();  // Предотвращает отправку формы
            auth.register();
        });
});
  
