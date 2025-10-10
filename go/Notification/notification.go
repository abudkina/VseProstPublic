package notification

import (
	"errors"
	"net/http"
	"strconv"
	"time"
	notificationModel "vseProst/models/NotificationModel"

	"github.com/gin-gonic/gin"
	"gorm.io/gorm"
)

// Функция для получения уведомлений по userID
func GetNotifications(db *gorm.DB) gin.HandlerFunc {
	return func(c *gin.Context) {

		userIDVal, exists := c.Get("userID")
		if !exists {
			c.JSON(401, gin.H{"error": "userID не найден"})
			return
		}
		
		userID, ok := userIDVal.(int)
		if !ok {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Ошибка получения ID пользователя"})
			return
		}

		// Предполагаем, что db - это глобальная переменная подключения к БД
		var notifications []notificationModel.Notification
		if err := db.Where("\"user\" = ?", userID).Find(&notifications).Error; err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to fetch notifications"})
			return
		}

		// Преобразуем в формат для фронтенда
		var response []notificationModel.Notification
		for _, n := range notifications {
			response = append(response, notificationModel.Notification{
				ID:           n.ID,
				Name:         n.Name,
				Description:  n.Description,
				Read:         n.Read,
				ModifiedDate: n.ModifiedDate,
			})
		}

		c.JSON(http.StatusOK, response)
	}
}

func ToggleRead(db *gorm.DB) gin.HandlerFunc {
	return func(c *gin.Context) {

		// Получаем ID уведомления из URL (например, PATCH /api/toggleRead/1)
		idStr := c.Query("id")
		id, err := strconv.Atoi(idStr)
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "invalid notification id"})
			return
		}

		userIDVal, exists := c.Get("userID")
		if !exists {
			c.JSON(401, gin.H{"error": "userID не найден"})
			return
		}
		userID := userIDVal.(int)

		// Проверяем, что уведомление принадлежит пользователю
		var notification notificationModel.Notification
		if err := db.Where("id = ? AND \"user\" = ?", id, userID).First(&notification).Error; err != nil {
			if errors.Is(err, gorm.ErrRecordNotFound) {
				c.JSON(http.StatusNotFound, gin.H{"error": "notification not found"})
			} else {
				c.JSON(http.StatusInternalServerError, gin.H{"error": "database error"})
			}
			return
		}

		// Toggle read
		notification.Read = !notification.Read;
		notification.ModifiedDate = time.Now();
		
		if err := db.Save(&notification).Error; err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to update notification"})
			return
		}

		// Возвращаем обновленное состояние
		c.JSON(http.StatusOK, notification)
	}
}
