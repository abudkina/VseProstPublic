package problemModel

import (
	"time"
	hashtagModel "vseProst/models/HashtagModel"
)

func (Problem) TableName() string {
	return "Problem" // имя таблицы из базы
}

type Problem struct {
	ID           int                    `gorm:"primaryKey;column:id"`
	Category     int                    `gorm:"column:category"`
	Describe     string                 `gorm:"column:describe"`
	Favourite    int                    `gorm:"column:favourite"`
	FromAuthor   bool                   `gorm:"column:fromauthor"`
	IsNew        bool                   `gorm:"column:isnew"`
	Creator      int                    `gorm:"column:creator"`
	ModifiedDate time.Time              `gorm:"column:modified_date"`
	CreatedDate  time.Time              `gorm:"column:created_date"`
	Image        string                 `gorm:"column:image"`
	Name         string                 `gorm:"column:name"`
	Reply        int                    `gorm:"column:reply"`
	Show         int                    `gorm:"column:show"`
	Topic        *int                   `gorm:"column:topic"`
	Hashtags     []hashtagModel.Hashtag `gorm:"many2many:hashtag_problems;joinForeignKey:ProblemID;joinReferences:HashtagID"`
}
