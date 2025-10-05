package refreshTokenModel

import "time"

func (RefreshToken) TableName() string {
	return "RefreshToken" // имя таблицы из базы
}

type RefreshToken struct {
	ID        int       `gorm:"primaryKey;column:id"`
	UserID    int       `gorm:"column:user_id;not null"`
	Token     string    `gorm:"column:token;size:255;not null;uniqueIndex"`
	CreatedAt time.Time `gorm:"column:created_at;default:CURRENT_TIMESTAMP"`
	ExpiresAt time.Time `gorm:"column:expires_at;not null"`
}
