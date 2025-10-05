package hashtagModel

import (
	"time"
	userModel "vseProst/models/UserModel"
)

func (Hashtag) TableName() string {
	return "Hashtag" // имя таблицы из базы
}

type Hashtag struct {
	ID           int            `gorm:"primaryKey;column:id"`
	IsNew        bool           `gorm:"column:isnew"`
	Name         string         `gorm:"column:name"`
	Show         int            `gorm:"column:show"`
	CreatorID    int            `gorm:"column:creator"`
	ModifiedDate time.Time      `gorm:"column:modified_date"`
	CreatedDate  time.Time      `gorm:"column:created_date"`
	Creator      userModel.User `gorm:"foreignKey:CreatorID;references:ID"`
}
