package problem

import (
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"time"

	categoryModel "vseProst/models/CategoryModel"
	hashtagModel "vseProst/models/HashtagModel"
	problemModel "vseProst/models/ProblemModel"
	problemWithSolutionsModel "vseProst/models/ProblemWithSolutionsModel"
	topicModel "vseProst/models/TopicModel"

	"github.com/gin-gonic/gin"
	"gorm.io/gorm"
)

// Получение категорий
func GetCategories(db *gorm.DB) gin.HandlerFunc {
	return func(c *gin.Context) {
		var categories []categoryModel.Category
		if err := db.Find(&categories).Error; err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Cannot fetch categories"})
			return
		}
		c.JSON(http.StatusOK, categories)
	}
}

// Получение хэштегов с фильтрацией LIKE (длина запроса минимум 2 символа)
func GetHashtags(db *gorm.DB) gin.HandlerFunc {
	return func(c *gin.Context) {
		q := c.Query("q")
		if len(q) < 2 {
			c.JSON(http.StatusOK, []hashtagModel.Hashtag{})
			return
		}

		search := strings.ToLower(q) + "%"

		var hashtags []hashtagModel.Hashtag
		err := db.
			Where("LOWER(name) LIKE ?", search).
			Order("show DESC, modified_date DESC").
			Limit(20).
			Find(&hashtags).Error
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Ошибка базы данных: " + err.Error()})
			return
		}

		c.JSON(http.StatusOK, hashtags)
	}
}

// Получение списка проблем с фильтрацией по хэштегам (ищем проблемы с ВСЕМИ заданными хэштегами)
func GetProblems(db *gorm.DB) gin.HandlerFunc {
	return func(c *gin.Context) {
		search := c.Query("search")
		categoryParam := c.Query("category")
		hashtagsParam := c.Query("hashtags")
		limitParam := c.DefaultQuery("limit", "50")
		offsetParam := c.DefaultQuery("offset", "0")

		limit, _ := strconv.Atoi(limitParam)
		offset, _ := strconv.Atoi(offsetParam)

		var categoryID int
		if categoryParam != "" {
			categoryID, _ = strconv.Atoi(categoryParam)
		}

		var hashtagIDs []int
		if hashtagsParam != "" {
			for _, h := range strings.Split(hashtagsParam, ",") {
				if id, err := strconv.Atoi(strings.TrimSpace(h)); err == nil {
					hashtagIDs = append(hashtagIDs, id)
				}
			}
		}

		// Начинаем формировать запрос
		query := db.Model(&problemWithSolutionsModel.ProblemWithSolutions{}).
			Preload("Hashtags").
			Preload("Solutions").
			Preload("ProblemLinks")

		if search != "" {
			// По названию проблемы или тегам
			searchLower := "%" + strings.ToLower(search) + "%"
			subQuery := db.Table("hashtag_problems").
				Select("problem_id").
				Joins("JOIN public.\"Hashtag\" ON id = hashtag_problems.hashtag_id").
				Where("LOWER(public.\"Hashtag\".name) LIKE ?", searchLower)

			query = query.Where("(LOWER(name) LIKE ? OR id IN (?))", searchLower, subQuery)
		}

		if categoryID != 0 {
			query = query.Where("category = ?", categoryID)
		}

		if len(hashtagIDs) > 0 {
			// Отфильтровать проблемы по хештегам — при этом проблема должна содержать *все* выбранные теги
			subQuery := db.Table("hashtag_problems").
				Select("problem_id").
				Where("hashtag_id IN ?", hashtagIDs).
				Group("problem_id").
				Having("COUNT(DISTINCT hashtag_id) = ?", len(hashtagIDs))

			query = query.Where("id IN (?)", subQuery)
		}

		query = query.Order("created_date DESC").Limit(limit).Offset(offset)

		var problems []problemWithSolutionsModel.ProblemWithSolutions
		if err := query.Find(&problems).Error; err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Ошибка базы данных: " + err.Error()})
			return
		}

		c.JSON(http.StatusOK, problems)
	}
}

// Получение проблемы по ID с использованием GORM, включая связанные хэштеги и решения
func GetProblemByID(db *gorm.DB) gin.HandlerFunc {
	return func(c *gin.Context) {
		problemID := c.Query("id")
		id, err := strconv.Atoi(problemID)
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "Неверный формат ID"})
			return
		}

		var problem problemWithSolutionsModel.ProblemWithSolutions

		err = db.Preload("Hashtags").
			Preload("Solutions").
			First(&problem, id).Error
		if err != nil {
			if err == gorm.ErrRecordNotFound {
				c.JSON(http.StatusNotFound, gin.H{"error": "Проблема не найдена"})
			} else {
				c.JSON(http.StatusInternalServerError, gin.H{"error": "Ошибка базы данных: " + err.Error()})
			}
			return
		}

		c.JSON(http.StatusOK, problem)
	}
}

func GetFavouriteProblems(db *gorm.DB) gin.HandlerFunc {
	return func(c *gin.Context) {

		userIDVal, exists := c.Get("userID")
		if !exists {
			c.JSON(401, gin.H{"error": "userID не найден"})
			return
		}
		userID := userIDVal.(int)

		search := c.Query("search")
		categoryParam := c.Query("category")
		hashtagsParam := c.Query("hashtags")
		limitParam := c.DefaultQuery("limit", "50")
		offsetParam := c.DefaultQuery("offset", "0")

		limit, _ := strconv.Atoi(limitParam)
		offset, _ := strconv.Atoi(offsetParam)

		var categoryID int
		if categoryParam != "" {
			categoryID, _ = strconv.Atoi(categoryParam)
		}

		var hashtagIDs []int
		if hashtagsParam != "" {
			for _, h := range strings.Split(hashtagsParam, ",") {
				if id, err := strconv.Atoi(strings.TrimSpace(h)); err == nil {
					hashtagIDs = append(hashtagIDs, id)
				}
			}
		}

		// Начинаем формировать запрос с JOIN на favourite_problems для фильтрации по избранным
		query := db.Model(problemWithSolutionsModel.ProblemWithSolutions{}).
			Preload("Hashtags").
			Preload("Solutions").
			Preload("ProblemLinks").
			Preload("FavouriteUsers").
			Joins("JOIN public.favourite_problem ON favourite_problem.problem_id = public.\"Problem\".id").
			Where("favourite_problem.user_id = ?", userID)

		if search != "" {
			// По названию проблемы или тегам
			searchLower := "%" + strings.ToLower(search) + "%"
			subQuery := db.Table("hashtag_problems").
				Select("problem_id").
				Joins("JOIN public.\"Hashtag\" ON id = hashtag_problems.hashtag_id").
				Where("LOWER(public.\"Hashtag\".name) LIKE ?", searchLower)

			query = query.Where("(LOWER(name) LIKE ? OR id IN (?))", searchLower, subQuery)
		}

		if categoryID != 0 {
			query = query.Where("category = ?", categoryID)
		}

		if len(hashtagIDs) > 0 {
			// Отфильтровать проблемы по хештегам — при этом проблема должна содержать *все* выбранные теги
			subQuery := db.Table("hashtag_problems").
				Select("problem_id").
				Where("hashtag_id IN ?", hashtagIDs).
				Group("problem_id").
				Having("COUNT(DISTINCT hashtag_id) = ?", len(hashtagIDs))

			query = query.Where("id IN (?)", subQuery)
		}

		query = query.Order("created_date DESC").Limit(limit).Offset(offset)

		var problems []problemWithSolutionsModel.ProblemWithSolutions
		if err := query.Find(&problems).Error; err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Ошибка базы данных: " + err.Error()})
			return
		}

		c.JSON(http.StatusOK, problems)
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
func CreateProblem(db *gorm.DB) gin.HandlerFunc {
	return func(c *gin.Context) {

		userIDVal, exists := c.Get("userID")
		if !exists {
			c.JSON(401, gin.H{"error": "userID не найден"})
			return
		}
		userID := userIDVal.(int)

		// Получаем данные из формы
		name := c.PostForm("name")
		describe := c.PostForm("describe")
		categoryStr := c.PostForm("category")
		topicStr := c.PostForm("topicID")        // Изменено: читаем topicID
		hashtagsStr := c.PostForm("hashtagsIDs") // Изменено: читаем hashtagsIDs

		if name == "" {
			c.JSON(http.StatusBadRequest, gin.H{"error": "Название проблемы обязательно"})
			return
		}

		// Парсим category
		category, err := strconv.Atoi(categoryStr)
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "Неверная категория"})
			return
		}

		// Парсим topic (опционально)
		var topic *int
		if topicStr != "" {
			t, err := strconv.Atoi(topicStr)
			if err == nil {
				topic = &t
			}
		}

		// Парсим hashtags (опционально)
		var hashtags []hashtagModel.Hashtag
		if hashtagsStr != "" {
			ids := strings.Split(hashtagsStr, ",")
			for _, idStr := range ids {
				id, err := strconv.Atoi(strings.TrimSpace(idStr))
				if err == nil {
					hashtags = append(hashtags, hashtagModel.Hashtag{ID: id})
				}
			}
		}

		// Обработка файла изображения (опционально)
		var imagePath string
		file, header, err := c.Request.FormFile("image")
		if err == nil {
			defer file.Close()
			// Сохраняем файл (предполагаем папку uploads/)
			filename := strconv.Itoa(int(time.Now().Unix())) + filepath.Ext(header.Filename)
			imagePath = "uploads/" + filename
			out, err := os.Create(imagePath)
			if err != nil {
				c.JSON(http.StatusInternalServerError, gin.H{"error": "Ошибка сохранения изображения"})
				return
			}
			defer out.Close()
			io.Copy(out, file)
		}

		// Создаём проблему
		problem := problemModel.Problem{
			Name:         name,
			Describe:     describe,
			Category:     category,
			Topic:        topic,
			Image:        imagePath,
			Creator:      userID,
			CreatedDate:  time.Now(),
			ModifiedDate: time.Now(),
			IsNew:        true, // По умолчанию новая
			Show:         1,    // По умолчанию показывать
			Favourite:    0,
			FromAuthor:   false,
			Reply:        0,
		}

		// Сохраняем в БД
		if err := db.Create(&problem).Error; err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Ошибка сохранения проблемы: " + err.Error()})
			return
		}

		// Связываем хэштеги
		if len(hashtags) > 0 {
			db.Model(&problem).Association("Hashtags").Append(hashtags)
		}

		c.JSON(http.StatusOK, gin.H{"message": "Проблема сохранена", "id": problem.ID})
	}
}
