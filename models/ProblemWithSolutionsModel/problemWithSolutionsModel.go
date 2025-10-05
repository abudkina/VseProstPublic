package problemWithSolutionsModel

import (
	"time"
	hashtagModel "vseProst/models/HashtagModel"
	problemModel "vseProst/models/ProblemModel"
	solutionModel "vseProst/models/SolutionModel"
	userModel "vseProst/models/UserModel"
)

func (ProblemWithSolutions) TableName() string {
	return "Problem" // имя таблицы из базы
}

type ProblemWithSolutions struct {
	ID             int                      `gorm:"primaryKey;column:id"`
	Category       int                      `gorm:"column:category"`
	Describe       string                   `gorm:"column:describe"`
	Favourite      int                      `gorm:"column:favourite"`
	FromAuthor     bool                     `gorm:"column:fromauthor"`
	IsNew          bool                     `gorm:"column:isnew"`
	Creator        int                      `gorm:"column:creator"`
	ModifiedDate   time.Time                `gorm:"column:modified_date"`
	CreatedDate    time.Time                `gorm:"column:created_date"`
	Image          string                   `gorm:"column:image"`
	Name           string                   `gorm:"column:name"`
	Reply          *int                     `gorm:"column:reply"`
	Show           int                      `gorm:"column:show"`
	Topic          *int                     `gorm:"column:topic"`
	Hashtags       []hashtagModel.Hashtag   `gorm:"many2many:hashtag_problems;joinForeignKey:ProblemID;joinReferences:HashtagID"`         // Исправлено
	Solutions      []solutionModel.Solution `gorm:"many2many:solution_problems;joinForeignKey:ProblemID;joinReferences:SolutionID"`       // Исправлено
	ProblemLinks   []problemModel.Problem   `gorm:"many2many:problem_link_problem;joinForeignKey:ProblemID;joinReferences:ProblemLinkID"` // Исправлено
	FavouriteUsers []userModel.User         `gorm:"many2many:favourite_problem;joinForeignKey:ProblemID;joinReferences:UserID"`           // Исправлено
}
