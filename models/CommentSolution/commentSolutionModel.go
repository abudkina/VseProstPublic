package commentSolutionModel

import (
	"time"
	userModel "vseProst/models/UserModel"
)

func (CommentSolution) TableName() string {
	return "CommentSolution"
}

type CommentSolution struct {
	ID           int                    `gorm:"column:id;primaryKey;autoIncrement;not null"`
	IsNew        bool                   `gorm:"column:isnew;default:true"`
	LikeCount    int                    `gorm:"column:likecount;default:0"`
	NotLikeCount int                    `gorm:"column:notlikecount;default:0"`
	SolutionID   int                    `gorm:"column:solution_id;not null"`
	Text         string                 `gorm:"column:text;type:text;not null"`
	CreatorID    int                    `gorm:"column:creator;not null"`
	ModifiedDate time.Time              `gorm:"column:modified_date;default:CURRENT_TIMESTAMP"`
	CreatedDate  time.Time              `gorm:"column:created_date;default:CURRENT_TIMESTAMP"`
	Creator      userModel.User         `gorm:"foreignKey:CreatorID;references:ID"`
}
