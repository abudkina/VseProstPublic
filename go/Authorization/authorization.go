package authorization

import (
	"net/http"
	"os"
	"time"

	registration "vseProst/go/Registration"
	refreshTokenModel "vseProst/models/RefreshTokenModel"
	userModel "vseProst/models/UserModel"

	"github.com/gin-gonic/gin"
	"golang.org/x/crypto/bcrypt"
	"gorm.io/gorm"
)

// AuthResponse представляет ответ авторизации
type AuthResponse struct {
	Message      string `json:"message"`
	AccessExpiry string `json:"accessExpiry"` // Время истечения accessToken (ISO string)
}

// isProduction проверяет, является ли среда продакшеном
func isProduction() bool {
	return os.Getenv("ENV") == "production"
}

// setCookie устанавливает куку с параметрами безопасности
func setCookie(c *gin.Context, name, value string, maxAge int, secure, httpOnly bool) {
	cookie := http.Cookie{
		Name:     name,
		Value:    value,
		MaxAge:   maxAge,
		Path:     "/",
		Domain:   "127.0.0.1", // Установлено для совпадения с доменом фронтенда и запросов
		Secure:   secure,
		HttpOnly: httpOnly,
		SameSite: http.SameSiteStrictMode, // Защита от CSRF
	}
	http.SetCookie(c.Writer, &cookie)
}

func LoginHandler(db *gorm.DB) gin.HandlerFunc {
	return func(c *gin.Context) {
		var loginData struct {
			Username string `json:"login" binding:"required"`
			Password string `json:"password" binding:"required"`
		}

		if err := c.ShouldBindJSON(&loginData); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "Имя пользователя и пароль обязательны"})
			return
		}

		username := loginData.Username
		password := loginData.Password

		// Получаем пользователя из базы данных через GORM
		var user userModel.User
		err := db.Where("username = ?", username).Take(&user).Error
		if err != nil {
			if err == gorm.ErrRecordNotFound {
				c.JSON(http.StatusUnauthorized, gin.H{"error": "Неверное имя пользователя или пароль"})
			} else {
				c.JSON(http.StatusInternalServerError, gin.H{"error": "Ошибка базы данных"})
			}
			return
		}

		// Проверяем пароль
		if err := checkPassword(user.PasswordHash, password); err != nil {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "Неверное имя пользователя или пароль"})
			return
		}

		// Генерация токенов
		accessToken := registration.GenerateAccessToken(user.ID, username)
		accessExpiry := time.Now().Add(15 * time.Minute).Format(time.RFC3339) // ISO для фронта
		refreshToken, err := registration.GenerateRefreshToken(int(user.ID))
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Ошибка при генерации refresh token"})
			return
		}

		// Сохраняем refresh token в БД через GORM
		rt := refreshTokenModel.RefreshToken{
			UserID:    user.ID,
			Token:     refreshToken,
			ExpiresAt: time.Now().Add(30 * 24 * time.Hour),
		}

		if err := db.Create(&rt).Error; err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Ошибка при сохранении refresh token"})
			return
		}

		secure := isProduction()
		// Установка токенов в HttpOnly cookies
		setCookie(c, "access_token", accessToken, 15*60, secure, true)        // 15 минут
		setCookie(c, "refresh_token", refreshToken, 30*24*3600, secure, true) // 30 дней

		c.JSON(http.StatusOK, AuthResponse{
			Message:      "Вход выполнен успешно!",
			AccessExpiry: accessExpiry,
		})
	}
}

// LogoutHandler обрабатывает выход пользователя
func LogoutHandler(db *gorm.DB) gin.HandlerFunc {
	return func(c *gin.Context) {
		// Получить refresh_token из куки
		refreshCookie, err := c.Cookie("refresh_token")
		if err == nil && refreshCookie != "" {
			// Удалить из БД
			var rt refreshTokenModel.RefreshToken
			if err := db.Where("token = ?", refreshCookie).First(&rt).Error; err == nil {
				db.Delete(&rt)
			}
		}

		// Очистить куки (expires в прошлом)
		expired := time.Now().AddDate(0, 0, -1)
		clearCookie(c, "access_token", expired, isProduction())
		clearCookie(c, "refresh_token", expired, isProduction())

		c.JSON(http.StatusOK, gin.H{"message": "Выход выполнен успешно"})
	}
}

// clearCookie очищает куку, устанавливая expires в прошлое
func clearCookie(c *gin.Context, name string, expires time.Time, secure bool) {
	cookie := http.Cookie{
		Name:     name,
		Value:    "",
		Expires:  expires,
		Path:     "/",
		Secure:   secure,
		HttpOnly: true,
		SameSite: http.SameSiteStrictMode,
	}
	http.SetCookie(c.Writer, &cookie)
}

// Проверка пароля
func checkPassword(hashedPassword, password string) error {
	return bcrypt.CompareHashAndPassword([]byte(hashedPassword), []byte(password))
}

func GetUserId(db *gorm.DB) gin.HandlerFunc {
	return func(c *gin.Context) {
		userIDVal, exists := c.Get("userID")
		if !exists {
			c.JSON(401, gin.H{"error": "userID не найден"})
			return
		}
		userID := userIDVal.(int)
		c.JSON(200, gin.H{"message": "Доступ разрешён", "userID": userID})
	}
}
