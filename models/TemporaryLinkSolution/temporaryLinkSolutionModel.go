package temporaryLinkSolution

import (
	"time"
	problemModel "vseProst/models/ProblemModel"
	solutionModel "vseProst/models/SolutionModel"
	userModel "vseProst/models/UserModel"
)


func (TemporaryLinkSolution) TableName() string {
    return "TemporaryLinkSolution"
}

// Модель для таблицы TemporaryLinkSolution
type TemporaryLinkSolution struct {
    ID           int       `gorm:"primaryKey;autoIncrement"`
    ProblemID    int       `gorm:"column:problem;not null"`
    Problem      problemModel.Problem   `gorm:"foreignKey:ProblemID;references:ID"`
    SolutionID   int       `gorm:"column:solution;not null"`
    Solution     solutionModel.Solution  `gorm:"foreignKey:SolutionID;references:ID"`
    CreatorID    int       `gorm:"column:creator;not null"`
    Creator      userModel.User      `gorm:"foreignKey:CreatorID;references:ID"`
    ModifiedDate time.Time `gorm:"column:modified_date;autoUpdateTime"`
    CreatedDate  time.Time `gorm:"column:created_date;autoCreateTime"`
}
