package problemLinkProblem

import problemModel "vseProst/models/ProblemModel"

// Таблица в БД
func (ProblemLinkProblem) TableName() string {
	return "problem_link_problem"
}

type ProblemLinkProblem struct {
	ProblemID     int `gorm:"primaryKey;column:problem_id"`
	ProblemLinkID int `gorm:"primaryKey;column:problem_link_id"`

	Problem     problemModel.Problem `gorm:"foreignKey:ProblemID;references:ID;constraint:OnUpdate:NO ACTION,OnDelete:CASCADE"`
	ProblemLink problemModel.Problem `gorm:"foreignKey:ProblemLinkID;references:ID;constraint:OnUpdate:NO ACTION,OnDelete:CASCADE"`
}
