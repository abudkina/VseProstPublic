package temporaryProblemSolution

import (
	"net/http"
	temporaryProblemSolution "vseProst/models/TemporaryProblemSolution"
	"github.com/gin-gonic/gin"
	"gorm.io/gorm"
)

// Обработчик для добавления категории
func CountTemporaryProblemSolution(db *gorm.DB) gin.HandlerFunc {
	return func(c *gin.Context) {
		var req temporaryProblemSolution.TemporaryProblemSolution

		_, exists := c.Get("userID")
		if !exists {
			c.JSON(401, gin.H{"error": "userID не найден"})
			return
		}
		
		var count int64
		if err := db.Model(req).Count(&count).Error; err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "DB error"})
			return
		}

		// Возвращаем созданную категорию
		c.JSON(http.StatusOK, gin.H{"count": count})
	}
}
