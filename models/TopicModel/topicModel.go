package topicModel

import (
	"time"
	userModel "vseProst/models/UserModel"
)

func (Topic) TableName() string {
  return "Topic"
}

type Topic struct {
    ID           int       `gorm:"column:id;primaryKey;autoIncrement;not null"`
    IsNew        bool      `gorm:"column:is_new;default:true"`
    Name         string    `gorm:"column:name;type:text;not null"`
    CreatorID      int       `gorm:"column:creator;not null"`
    ModifiedDate time.Time `gorm:"column:modified_date;default:CURRENT_TIMESTAMP"`
    CreatedDate  time.Time `gorm:"column:created_date;default:CURRENT_TIMESTAMP"`
    Creator      userModel.User  `gorm:"foreignKey:CreatorID;references:ID"`
}


