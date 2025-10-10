package temporaryLinkProblem

import (
	"time"
	problemModel "vseProst/models/ProblemModel"
	userModel "vseProst/models/UserModel"
)


func (TemporaryLinkProblem) TableName() string {
    return "TemporaryLinkProblem"
}

// Модель для таблицы TemporaryLinkProblem

type TemporaryLinkProblem struct {
    ID              int       `gorm:"primaryKey;autoIncrement"`
    CurrentProblemID int      `gorm:"column:currentproblem;not null"`
    CurrentProblem  problemModel.Problem   `gorm:"foreignKey:CurrentProblemID;references:ID"`
    LinkProblemID   int       `gorm:"column:linkproblem;not null"`
    LinkProblem     problemModel.Problem   `gorm:"foreignKey:LinkProblemID;references:ID"`
    CreatorID       int       `gorm:"column:creator;not null"`
    Creator         userModel.User      `gorm:"foreignKey:CreatorID;references:ID"`
    ModifiedDate    time.Time `gorm:"column:modified_date;autoUpdateTime"`
    CreatedDate     time.Time `gorm:"column:created_date;autoCreateTime"`
}
