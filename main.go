package main

import (
	"fmt"
	"log"

	config "vseProst/const"
	authorization "vseProst/go/Authorization"
	category "vseProst/go/Category"
	commentSolution "vseProst/go/CommentSolution"
	hashtag "vseProst/go/Hashtag"
	notification "vseProst/go/Notification"
	problem "vseProst/go/Problem"
	registration "vseProst/go/Registration"
	solution "vseProst/go/Solution"
	temporaryLinkProblem "vseProst/go/TemporaryLinkProblem"
	temporaryLinkSolution "vseProst/go/TemporaryLinkSolution"
	temporaryProblemSolution "vseProst/go/TemporaryProblemSolution"
	topic "vseProst/go/Topic"
	user "vseProst/go/User"

	"github.com/gin-gonic/gin"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
)

// Функция для настройки соединения с базой данных
func setupDB() (*gorm.DB, error) {
	psqlInfo := fmt.Sprintf("host=%s port=%d user=%s password=%s dbname=%s sslmode=disable",
		config.Host, config.Port, config.User, config.Password, config.Dbname)
	return gorm.Open(postgres.Open(psqlInfo), &gorm.Config{
		PrepareStmt: true})
}

func main() {
	db, err := setupDB()
	if err != nil {
		log.Fatalf("Ошибка подключения к БД: %v", err)
	}

	// Создаем Gin роутер
	router := gin.Default()

	// Настройка CORS middleware для Gin
	router.Use(func(c *gin.Context) {
		c.Writer.Header().Set("Access-Control-Allow-Origin", "http://127.0.0.1:5500")
		c.Writer.Header().Set("Access-Control-Allow-Methods", "POST, GET, OPTIONS, PUT, DELETE, PATCH")
		c.Writer.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")
		c.Writer.Header().Set("Access-Control-Allow-Credentials", "true")

		if c.Request.Method == "OPTIONS" {
			c.AbortWithStatus(200)
			return
		}

		c.Next()
	})

	// Роуты API
	router.GET("/api/categories", problem.GetCategories(db))
	router.GET("/api/topics", topic.GetTopics(db))
	router.GET("/api/problems", problem.GetProblems(db))
	router.GET("/api/problem", problem.GetProblemByID(db))
	router.GET("/api/solution", solution.GetSolutionID(db))
	router.GET("/api/solutions", solution.GetSolutions(db))
	router.GET("/api/hashtags", problem.GetHashtags(db))
	router.POST("/api/login", authorization.LoginHandler(db))
	router.POST("/api/logout", authorization.LogoutHandler(db))
	router.POST("/api/register", registration.RegisterHandler(db))
	router.POST("/api/refreshToken", registration.RefreshTokenHandler(db))

	// Группа защищённых маршрутов
	authGroup := router.Group("/api")
	authGroup.Use(registration.AuthMiddleware(registration.SecretKey()))
	{
		authGroup.GET("/getUserId", authorization.GetUserId(db))
		authGroup.GET("/getFavouriteProblems", problem.GetFavouriteProblems(db))
		authGroup.GET("/getNotifications", notification.GetNotifications(db))
		authGroup.PATCH("/toggleRead", notification.ToggleRead(db))
		authGroup.POST("/createProblem", problem.CreateProblem(db))
		authGroup.GET("/countProblem", problem.CountProblem(db))
		authGroup.GET("/countTemporaryLinkProblem", temporaryLinkProblem.CountTemporaryLinkProblem(db))
		authGroup.GET("/countTemporaryLinkSolution", temporaryLinkSolution.CountTemporaryLinkSolution(db))
		authGroup.GET("/countTemporaryProblemSolution", temporaryProblemSolution.CountTemporaryProblemSolution(db))
		authGroup.POST("/createSolution", solution.CreateSolution(db))
		authGroup.POST("/addCategory", category.AddCategory(db))
		authGroup.GET("/countCategory", category.CountCategory(db))
		authGroup.POST("/addHashtag", hashtag.AddHashtag(db))
		authGroup.GET("/countHashtag", hashtag.CountHashtag(db))
		authGroup.POST("/addTopic", topic.AddTopic(db))
		authGroup.GET("/countTopic", topic.CountTopic(db))
		authGroup.GET("/countSolution", solution.CountSolution(db))
		authGroup.GET("/countUser", user.CountUser(db))
		authGroup.GET("/countCommentSolution", commentSolution.CountCommentSolution(db))
		// Добавляйте сюда другие защищённые маршруты
	}

	fmt.Println("Сервер запущен на порту 8080")
	if err := router.Run(":8080"); err != nil {
		log.Fatalf("Ошибка запуска сервера: %v", err)
	}
}
