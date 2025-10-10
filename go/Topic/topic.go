package topic

import (
	"net/http"
	"strings"
	"time"
	topicModel "vseProst/models/TopicModel"

	"github.com/gin-gonic/gin"
	"gorm.io/gorm"
)

func AddTopic(db *gorm.DB) gin.HandlerFunc {
	return func(c *gin.Context) {
		var req topicModel.Topic
		if err := c.ShouldBindJSON(&req); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "Неверный JSON: " + err.Error()})
			return
		}

		// Получите userID из контекста (предполагаем, что middleware устанавливает его как int)
		userIDInterface, exists := c.Get("userID")
		if !exists {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "Пользователь не авторизован"})
			return
		}
		userID, ok := userIDInterface.(int)
		if !ok {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Неверный тип userID"})
			return
		}

		// Нормализация имени (как в истории чата)
		req.Name = strings.TrimSpace(req.Name)
		if len(req.Name) == 0 {
			c.JSON(http.StatusBadRequest, gin.H{"error": "Имя темы не может быть пустым"})
			return
		}
		req.Name = strings.Title(strings.ToLower(req.Name)) // Первая буква заглавная, остальные строчные

		// Проверка уникальности по имени (чтобы избежать дубликатов)
		var existing topicModel.Topic
		if err := db.Where("name = ?", req.Name).First(&existing).Error; err == nil {
			c.JSON(http.StatusConflict, gin.H{"error": "Тема с таким именем уже существует"})
			return
		} else if err != gorm.ErrRecordNotFound {
			// Обработка других ошибок базы (например, соединение)
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Ошибка проверки уникальности: " + err.Error()})
			return
		}

		// Установите CreatorID
		req.CreatorID = userID
		req.CreatedDate = time.Now()
		req.ModifiedDate = time.Now()
		req.IsNew = true

		// Создание записи
		if err := db.Create(&req).Error; err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Ошибка создания темы: " + err.Error()})
			return
		}

		// Возврат созданной темы (с сгенерированным ID и датами)
		c.JSON(http.StatusOK, req)
	}
}

func GetTopics(db *gorm.DB) gin.HandlerFunc {
	return func(c *gin.Context) {
		search := c.Query("search")
		if len(search) < 2 {
			// Чтобы не нагружать бд, вернем пустой массив, если меньше 3 символов
			c.JSON(http.StatusOK, []string{})
			return
		}

		var topics []topicModel.Topic
		// Поиск с учетом регистра в поле name (Или ilike для Postgres, если GORM поддерживает)
		err := db.Where("name ILIKE ?", "%"+strings.TrimSpace(search)+"%").Limit(10).Find(&topics).Error
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Ошибка поиска тем"})
			return
		}

		c.JSON(http.StatusOK, topics)
	}
}

// Обработчик для добавления категории
func CountTopic(db *gorm.DB) gin.HandlerFunc {
	return func(c *gin.Context) {
		var req topicModel.Topic

		_, exists := c.Get("userID")
		if !exists {
			c.JSON(401, gin.H{"error": "userID не найден"})
			return
		}
		
		var count int64
		if err := db.Model(req).Where("is_new = ?", true).Count(&count).Error; err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "DB error"})
			return
		}

		// Возвращаем созданную категорию
		c.JSON(http.StatusOK, gin.H{"count": count})
	}
}
