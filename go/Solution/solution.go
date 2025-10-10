package solution

import (
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"time"
	problemModel "vseProst/models/ProblemModel"
	solutionModel "vseProst/models/SolutionModel"
	solutionWithProblemModel "vseProst/models/SolutionWithProblemModel"

	"github.com/gin-gonic/gin"
	"gorm.io/gorm"
)

// Получение проблемы по ID с использованием GORM, включая связанные хэштеги и решения
func GetSolutionID(db *gorm.DB) gin.HandlerFunc {
	return func(c *gin.Context) {
		solutionID := c.Query("id")
		id, err := strconv.Atoi(solutionID)
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "Неверный формат ID"})
			return
		}

		var solution solutionModel.Solution

		err = db.Preload("Creator").
			Preload("CommentSolutions.Creator").
			First(&solution, id).Error
		if err != nil {
			if err == gorm.ErrRecordNotFound {
				c.JSON(http.StatusNotFound, gin.H{"error": "Решение не найдено"})
			} else {
				c.JSON(http.StatusInternalServerError, gin.H{"error": "Ошибка базы данных: " + err.Error()})
			}
			return
		}

		c.JSON(http.StatusOK, solution)
	}
}

// Получение проблемы по ID с использованием GORM, включая связанные хэштеги и решения
func GetSolutions(db *gorm.DB) gin.HandlerFunc {
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

		// Начинаем с модели (без алиаса для базовой таблицы)
		query := db.Model(&solutionWithProblemModel.SolutionWithProblem{}).
			Joins(`LEFT JOIN solution_problems sp ON "Solution".id = sp.solution_id`).
			Joins(`LEFT JOIN public."Problem" p ON sp.problem_id = p.id`).
			Preload("Creator").
			Preload("CommentSolutions").
			Preload("Problems").
			Preload("Problems.Hashtags")

		if search != "" {
			searchLower := "%" + strings.ToLower(search) + "%"
			subQuery := db.Table("hashtag_problems").
				Select("problem_id").
				Joins(`JOIN public."Hashtag" ON id = hashtag_problems.hashtag_id`).
				Where("LOWER(public.\"Hashtag\".name) LIKE ?", searchLower)

			query = query.Where("(LOWER(\"Solution\".name) LIKE ? OR p.id IN (?))", searchLower, subQuery)
		}

		if categoryID != 0 {
			query = query.Where("p.category = ?", categoryID)
		}

		if len(hashtagIDs) > 0 {
			subQuery := db.Table("hashtag_problems").
				Select("problem_id").
				Where("hashtag_id IN ?", hashtagIDs).
				Group("problem_id").
				Having("COUNT(DISTINCT hashtag_id) = ?", len(hashtagIDs))

			query = query.Where("p.id IN (?)", subQuery)
		}

		// ORDER по created_date из "Solution"
		query = query.Order(`"Solution".created_date DESC`).Limit(limit).Offset(offset)

		var solutions []solutionWithProblemModel.SolutionWithProblem
		if err := query.Find(&solutions).Error; err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Ошибка базы данных: " + err.Error()})
			return
		}

		c.JSON(http.StatusOK, solutions)
	}
}

func CreateSolution(db *gorm.DB) gin.HandlerFunc {
	return func(c *gin.Context) {
		name := c.PostForm("solution")
		describe := c.PostForm("details")
		relatedProblemsStr := c.PostForm("relatedProblems") // Предполагаем, что это строка IDs через запятую, например "1,2,3"
		canBuy := c.PostForm("canBuy") == "on"
		canEvaluate := c.PostForm("canEvaluate") == "on"

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

		// Разбор связанных проблем
		var problems []problemModel.Problem
		if relatedProblemsStr != "" {
			ids := strings.Split(relatedProblemsStr, ",")
			for _, idStr := range ids {
				id, err := strconv.Atoi(strings.TrimSpace(idStr))
				if err == nil {
					problems = append(problems, problemModel.Problem{ID: id})
				}
			}
		}

		// Создать решение
		solution := solutionWithProblemModel.SolutionWithProblem{
			Name:      name,
			Describe:  describe,
			Image:     imagePath,
			IsBought:  canBuy,
			IsRating:  canEvaluate,
			Problems:  problems,
			CreatorID: 1, // Захардкодено; получите из JWT/сессии
			// Остальные поля по умолчанию
		}

		// Сохранить в БД
		if err := db.Create(&solution).Error; err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to save solution"})
			return
		}

		c.JSON(http.StatusOK, gin.H{"message": "Solution added successfully", "id": solution.ID})
	}
}

// Обработчик для добавления категории
func CountSolution(db *gorm.DB) gin.HandlerFunc {
	return func(c *gin.Context) {
		var req solutionModel.Solution

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
