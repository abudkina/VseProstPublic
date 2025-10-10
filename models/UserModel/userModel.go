package userModel

import "time"

func (User) TableName() string {
	return "User" // имя таблицы из базы
}

type User struct {
	ID           int        `gorm:"primaryKey;column:id"`
	IsNew        bool      `gorm:"column:is_new;default:true"`
	FavProblem   bool       `gorm:"column:favproblem;default:true"`
	FavSolution  bool       `gorm:"column:favsolution;default:false"`
	Image        *string    `gorm:"column:image"` // nullable text
	IsActive     bool       `gorm:"column:isactive;default:true"`
	LastLogin    *time.Time `gorm:"column:lastlogin"` // nullable timestamp
	Username     string     `gorm:"column:username;not null;uniqueIndex"`
	Email        string     `gorm:"column:email;not null;uniqueIndex"`
	ModifiedDate time.Time  `gorm:"column:modified_date;default:CURRENT_TIMESTAMP"`
	CreatedDate  time.Time  `gorm:"column:created_date;default:CURRENT_TIMESTAMP"`
	Notification []int      `gorm:"column:notification;type:integer[]"` // integer array
	Type         *int       `gorm:"column:type"`                        // foreign key, nullable int
	PasswordHash string     `gorm:"column:password_hash;not null;default:''"`
}
