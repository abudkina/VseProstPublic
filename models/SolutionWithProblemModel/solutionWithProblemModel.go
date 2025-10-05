package solutionWithProblemModel

import (
	"time"
	commentSolutionModel "vseProst/models/CommentSolution"
	problemModel "vseProst/models/ProblemModel"
	userModel "vseProst/models/UserModel"

	"github.com/lib/pq"
)

func (SolutionWithProblem) TableName() string {
	return "Solution" // имя таблицы из базы
}

type SolutionWithProblem struct {
	ID               int                                    `gorm:"primaryKey;column:id"`
	Complexity       *int                                   `gorm:"column:complexity"` // nullable integer
	Describe         string                                 `gorm:"column:describe;not null"`
	Efficiency       *int                                   `gorm:"column:efficiency"` // nullable integer
	Favourite        int                                    `gorm:"column:favourite;default:0"`
	FromAuthor       bool                                   `gorm:"column:fromauthor;default:false"`
	Image            string                                 `gorm:"column:image;not null"`
	IsBought         bool                                   `gorm:"column:isbought;default:false"`
	IsNew            bool                                   `gorm:"column:isnew;default:true"`
	IsRating         bool                                   `gorm:"column:israting;default:false"`
	Like             int                                    `gorm:"column:like;default:0"`
	Name             string                                 `gorm:"column:name;not null"`
	NotLike          int                                    `gorm:"column:notlike;default:0"`
	Price            *float64                               `gorm:"column:price;type:numeric(10,2)"` // тип numeric(10,2) -> float64 pointer для nullable
	Rating           int                                    `gorm:"column:rating;default:0"`
	Reply            *int                                   `gorm:"column:reply;default:0"` // nullable integer, в таблице DEFAULT 0
	Show             int                                    `gorm:"column:show;default:0"`  // integer, не nullable
	Time             *int                                   `gorm:"column:time"`            // nullable integer времени
	CreatorID        int                                    `gorm:"column:creator;not null"`
	ModifiedDate     time.Time                              `gorm:"column:modified_date;default:CURRENT_TIMESTAMP"`
	CreatedDate      time.Time                              `gorm:"column:created_date;default:CURRENT_TIMESTAMP"`
	Attach           pq.StringArray                         `gorm:"type:text[]"`
	Creator          userModel.User                         `gorm:"foreignKey:CreatorID;references:ID"`
	CommentSolutions []commentSolutionModel.CommentSolution `gorm:"foreignKey:SolutionID;references:ID"`
	Problems         []problemModel.Problem                 `gorm:"many2many:solution_problems;joinForeignKey:SolutionID;joinReferences:ProblemID"`
	FavouriteUsers   []userModel.User                       `gorm:"many2many:favourite_solutions;joinForeignKey:SolutionID;joinReferences:UserID"` // Исправлено
}
