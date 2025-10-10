package user

import (
	"net/http"
	userModel "vseProst/models/UserModel"
	"github.com/gin-gonic/gin"
	"gorm.io/gorm"
)

// Обработчик для добавления категории
func CountUser(db *gorm.DB) gin.HandlerFunc {
	return func(c *gin.Context) {
		var req userModel.User

		_, exists := c.Get("userID")
		if !exists {
			c.JSON(401, gin.H{"error": "userID не найден"})
			return
		}
		
		var count int64
		if err := db.Model(req).Where("isnew = ?", true).Count(&count).Error; err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "DB error"})
			return
		}

		// Возвращаем созданную категорию
		c.JSON(http.StatusOK, gin.H{"count": count})
	}
}
