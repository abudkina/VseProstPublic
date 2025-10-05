package categoryModel

import (
	"time"
	userModel "vseProst/models/UserModel"
)

func (Category) TableName() string {
	return "Category"
}

type Category struct {
	ID           int            `gorm:"primaryKey;column:id"`
	IsNew        bool           `gorm:"column:isnew;default:true"`
	Name         string         `gorm:"column:name;not null"`
	ModifiedDate time.Time      `gorm:"column:modified_date;default:CURRENT_TIMESTAMP"`
	CreatedDate  time.Time      `gorm:"column:created_date;default:CURRENT_TIMESTAMP"`
	CreatorID    int            `gorm:"column:creator;not null"`
	Creator      userModel.User `gorm:"foreignKey:CreatorID;references:ID"`
}
