package registration

import (
	"crypto/rand"
	"encoding/base64"
	"log"
	"net/http"
	"os"
	"regexp"
	"time"
	refreshTokenModel "vseProst/models/RefreshTokenModel"
	userModel "vseProst/models/UserModel"

	"github.com/dgrijalva/jwt-go"
	"github.com/gin-gonic/gin"
	"golang.org/x/crypto/bcrypt"
	"gorm.io/gorm"
)

// Секретный ключ для JWT (измените на ваш)
var secretKey []byte

// AuthResponse представляет ответ авторизации
type AuthResponse struct {
	Message      string `json:"message"`
	AccessExpiry string `json:"accessExpiry"` // Добавлено для refresh
}

func SecretKey() []byte {
	return secretKey
}

func init() {
	secret := os.Getenv("JWT_SECRET")
	if secret == "" {
		secret = "default_secret_key_change_me"
	}
	secretKey = []byte(secret)
}

func isProduction() bool {
	return os.Getenv("ENV") == "production"
}

// setCookie устанавливает куку с параметрами безопасности (аналогично authorization)
func setCookie(c *gin.Context, name, value string, maxAge int, secure, httpOnly bool) {
	cookie := http.Cookie{
		Name:     name,
		Value:    value,
		MaxAge:   maxAge,
		Path:     "/",
		Secure:   secure,
		HttpOnly: httpOnly,
		SameSite: http.SameSiteStrictMode,
	}
	http.SetCookie(c.Writer, &cookie)
}

func AuthMiddleware(secretKey []byte) gin.HandlerFunc {
	return func(c *gin.Context) {
		accessToken, err := c.Cookie("access_token")
		log.Println("accessToken", accessToken)
		if err != nil {
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "Access token отсутствует"})
			return
		}

		token, err := jwt.Parse(accessToken, func(token *jwt.Token) (interface{}, error) {
			if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
				return nil, jwt.ErrSignatureInvalid
			}
			return secretKey, nil
		})

		if err != nil || !token.Valid {
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "Неверный или просроченный токен"})
			return
		}

		claims, ok := token.Claims.(jwt.MapClaims)
		if !ok {
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "Некорректные данные токена"})
			return
		}

		userIDFloat, ok := claims["userID"].(float64)
		if !ok {
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "userID не найден в токене"})
			return
		}
		userID := int(userIDFloat)

		c.Set("userID", userID)
		c.Next()
	}
}

// ValidateEmail проверяет корректность email-адреса
func ValidateEmail(email string) bool {
	re := regexp.MustCompile(`^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$`)
	return re.MatchString(email)
}

// RegisterHandler обрабатывает регистрацию пользователя через GORM и Gin
func RegisterHandler(db *gorm.DB) gin.HandlerFunc {
	return func(c *gin.Context) {
		var requestData struct {
			Username string `json:"username" binding:"required"`
			Password string `json:"password" binding:"required"`
			Email    string `json:"email" binding:"required"`
		}

		if err := c.ShouldBindJSON(&requestData); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "Все поля должны быть заполнены в формате JSON"})
			return
		}

		username := requestData.Username
		password := requestData.Password
		email := requestData.Email

		if !ValidateEmail(email) {
			c.JSON(http.StatusBadRequest, gin.H{"error": "Неверный формат email"})
			return
		}

		// Проверка существования username
		var count int64
		if err := db.Model(&userModel.User{}).Where("username = ?", username).Count(&count).Error; err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Ошибка при проверке пользователя"})
			return
		}
		if count > 0 {
			c.JSON(http.StatusConflict, gin.H{"error": "Пользователь с таким username уже существует"})
			log.Println("Пользователь с таким username уже существует")
			return
		}

		// Проверка существования email
		if err := db.Model(&userModel.User{}).Where("email = ?", email).Count(&count).Error; err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Ошибка при проверке пользователя"})
			return
		}
		if count > 0 {
			c.JSON(http.StatusConflict, gin.H{"error": "Пользователь с таким email уже существует"})
			log.Println("Пользователь с таким email уже существует")
			return
		}

		// Хеширование пароля
		hashedPassword, err := hashPassword(password)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Ошибка хеширования пароля"})
			return
		}

		// Создаем пользователя
		user := userModel.User{
			Username:     username,
			PasswordHash: hashedPassword,
			Email:        email,
		}
		if err := db.Create(&user).Error; err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Ошибка при создании пользователя"})
			return
		}

		// Генерация токенов
		accessToken := GenerateAccessToken(user.ID, username)
		refreshToken, err := GenerateRefreshToken(int(user.ID))
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Ошибка при генерации refresh token"})
			return
		}

		// Сохраняем refresh token в БД
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

		c.JSON(http.StatusOK, AuthResponse{Message: "Регистрация успешна!"})
	}
}

// RefreshTokenHandler обновляет токены через GORM и Gin
func RefreshTokenHandler(db *gorm.DB) gin.HandlerFunc {
	return func(c *gin.Context) {
		// Получаем refresh_token из cookie
		refreshToken, err := c.Cookie("refresh_token")
		if err != nil {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "Невалидный refresh token"})
			return
		}

		var rt refreshTokenModel.RefreshToken
		err = db.Where("token = ?", refreshToken).First(&rt).Error
		if err != nil {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "Невалидный refresh token"})
			return
		}

		// Проверяем срок действия refresh token
		if time.Now().After(rt.ExpiresAt) {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "Refresh token истек"})
			return
		}

		// Получаем пользователя для генерации access token
		var user userModel.User
		if err := db.First(&user, rt.UserID).Error; err != nil {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "Пользователь не найден"})
			return
		}

		// Генерация новых токенов
		newAccessToken := GenerateAccessToken(user.ID, user.Username)
		newRefreshToken, err := GenerateRefreshToken(int(user.ID))
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Ошибка при генерации refresh token"})
			return
		}

		// Обновляем refresh token в БД
		rt.Token = newRefreshToken
		rt.ExpiresAt = time.Now().Add(30 * 24 * time.Hour)
		if err := db.Save(&rt).Error; err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Ошибка при обновлении refresh token"})
			return
		}

		// Установка новых токенов в cookies
		secure := isProduction()
		setCookie(c, "access_token", newAccessToken, 15*60, secure, true)
		setCookie(c, "refresh_token", newRefreshToken, 30*24*3600, secure, true)

		c.JSON(http.StatusOK, AuthResponse{Message: "Токены обновлены!"})
	}
}

// GenerateAccessToken создает JWT access token
func GenerateAccessToken(userID int, username string) string {
	claims := jwt.MapClaims{
		"username": username,
		"userID":   userID,
		"exp":      time.Now().Add(15 * time.Minute).Unix(),
	}
	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	tokenString, _ := token.SignedString(secretKey)
	return tokenString
}

// GenerateRefreshToken генерирует случайный refresh token
func GenerateRefreshToken(userID int) (string, error) {
	tokenBytes := make([]byte, 32)
	_, err := rand.Read(tokenBytes)
	if err != nil {
		return "", err
	}
	token := "refresh_token_" + base64.RawURLEncoding.EncodeToString(tokenBytes)
	return token, nil
}

// hashPassword хеширует пароль с помощью bcrypt
func hashPassword(password string) (string, error) {
	bytes, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
	return string(bytes), err
}
