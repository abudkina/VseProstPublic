package category

import (
	"net/http"
	"strings"
	"time"
	categoryModel "vseProst/models/CategoryModel"

	"github.com/gin-gonic/gin"
	"gorm.io/gorm"
	// Предполагаю, что userModel.User импортирован
)

// Обработчик для добавления категории
func AddCategory(db *gorm.DB) gin.HandlerFunc {
	return func(c *gin.Context) {
		var req categoryModel.Category
		if err := c.ShouldBindJSON(&req); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "Неверный запрос: имя категории обязательно и не должно быть пустым"})
			return
		}

		// Убираем лишние пробелы по краям и проверяем на пустоту
		req.Name = strings.TrimSpace(req.Name)
		if req.Name == "" {
			c.JSON(http.StatusBadRequest, gin.H{"error": "Неверный запрос: имя категории обязательно и не должно быть пустым"})
			return
		}

		// Получаем userID из контекста (предполагая middleware для аутентификации)
		userIDInterface, exists := c.Get("userID")
		if !exists {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "Не авторизован"})
			return
		}
		userID, ok := userIDInterface.(int)
		if !ok {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Ошибка получения ID пользователя"})
			return
		}

		// Нормализуем имя запроса: убираем пробелы, приводим к нижнему регистру и заменяем ё/Ё на е (унификация к "е")
		normalizedReqName := strings.ToLower(strings.ReplaceAll(strings.ReplaceAll(req.Name, "ё", "е"), "Ё", "е"))

		// Проверяем, существует ли уже категория с таким нормализованным именем для этого пользователя
		// Используем TRIM в SQL, чтобы учесть возможные пробелы в существующих записях базы данных
		// Заменяем и маленькую, и заглавную ё на е
		var existingCategory categoryModel.Category
		if err := db.Where("LOWER(TRIM(REPLACE(REPLACE(name, 'ё', 'е'), 'Ё', 'е'))) = ?", normalizedReqName).First(&existingCategory).Error; err == nil {
			// Категория найдена — возвращаем ошибку
			c.JSON(http.StatusBadRequest, gin.H{"error": "Категория с таким именем уже существует"})
			return
		} else if err != gorm.ErrRecordNotFound {
			// Ошибка запроса (не "не найдено")
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Ошибка проверки уникальности"})
			return
		}

		// Если проверки пройдены, присваиваем CreatorID и создаем категорию
		req.CreatorID = userID
		req.CreatedDate = time.Now()
		req.ModifiedDate = time.Now()
		req.IsNew = true

		if err := db.Create(&req).Error; err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Ошибка создания категории"})
			return
		}

		// Возвращаем созданную категорию
		c.JSON(http.StatusOK, req)
	}
}

// Обработчик для добавления категории
func CountCategory(db *gorm.DB) gin.HandlerFunc {
	return func(c *gin.Context) {
		var req categoryModel.Category

		_, exists := c.Get("userID")
		if !exists {
			c.JSON(401, gin.H{"error": "userID не найден"})
			return
		}
		
		var count int64
		if err := db.Model(req).Where("IsNew = ?", true).Count(&count).Error; err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "DB error"})
			return
		}

		// Возвращаем созданную категорию
		c.JSON(http.StatusOK, gin.H{"count": count})
	}
}
