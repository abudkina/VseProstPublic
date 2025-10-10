package notificationModel

import (
	"time"
	userModel "vseProst/models/UserModel"
)

// Таблица в БД
func (Notification) TableName() string {
	return "Notification"
}


// Notification модель для таблицы public.Notifications
type Notification struct {
    ID           int       `gorm:"primaryKey;autoIncrement;column:id"` // Первичный ключ с автоинкрементом
    Description  string    `gorm:"not null;column:describe"`           // Описание (текст, не null)
    Name         string    `gorm:"not null;column:name"`               // Название (текст, не null)
    Read         bool      `gorm:"default:false;column:read"`          // Прочитано (булево, по умолчанию false)
    UserID       int       `gorm:"not null;column:user"`               // ID пользователя (foreign key)
    CreatorID    int       `gorm:"not null;column:creator"`            // ID создателя (foreign key)
    ModifiedDate time.Time `gorm:"autoUpdateTime;column:modified_date"` // Дата модификации (timestamp, auto update)
    CreatedDate  time.Time `gorm:"autoCreateTime;column:created_date"`  // Дата создания (timestamp, auto create)
	Creator      userModel.User `gorm:"foreignKey:CreatorID;references:ID"`
}

