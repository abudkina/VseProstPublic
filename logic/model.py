from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
import jwt
from datetime import datetime, timedelta
import os

from logic.utils.file_utils import normalize_image_url

db = SQLAlchemy()

SECRET_KEY = os.getenv('JWT_SECRET', 'default_secret_key_change_me')

# Ассоциативные таблицы (точно как в БД)
problem_link_solutions = db.Table('problem_link_solutions',
    db.Column('problem_id', db.Integer, db.ForeignKey('problem.id'), primary_key=True),
    db.Column('solution_id', db.Integer, db.ForeignKey('solution.id'), primary_key=True),
    info={'bind_key': None}
)

solution_problems = db.Table('solution_problems',
    db.Column('problem_id', db.Integer, db.ForeignKey('problem.id'), primary_key=True),
    db.Column('solution_id', db.Integer, db.ForeignKey('solution.id'), primary_key=True),
    info={'bind_key': None}
)

problem_link_problem = db.Table('problem_link_problem',
    db.Column('problem_id', db.Integer, db.ForeignKey('problem.id'), primary_key=True),
    db.Column('problem_link_id', db.Integer, db.ForeignKey('problem.id'), primary_key=True),
    info={'bind_key': None}
)

solution_link_solution = db.Table('solution_link_solution',
    db.Column('solution_id', db.Integer, db.ForeignKey('solution.id'), primary_key=True),
    db.Column('solution_link_id', db.Integer, db.ForeignKey('solution.id'), primary_key=True),
    info={'bind_key': None}
)

hashtag_problem = db.Table('hashtag_problem',
    db.Column('problem_id', db.Integer, db.ForeignKey('problem.id'), primary_key=True),
    db.Column('hashtag_id', db.Integer, db.ForeignKey('hashtag.id'), primary_key=True),
    info={'bind_key': None}
)

hashtag_solution = db.Table('hashtag_solution',
    db.Column('solution_id', db.Integer, db.ForeignKey('solution.id'), primary_key=True),
    db.Column('hashtag_id', db.Integer, db.ForeignKey('hashtag.id'), primary_key=True),
    info={'bind_key': None}
)

favourite_problem = db.Table('favourite_problem',
    db.Column('problem_id', db.Integer, db.ForeignKey('problem.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    info={'bind_key': None}
)

favourite_solution = db.Table('favourite_solution',
    db.Column('solution_id', db.Integer, db.ForeignKey('solution.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    info={'bind_key': None}
)

comment_solution_likes = db.Table('comment_solution_likes',
    db.Column('commentid', db.Integer, db.ForeignKey('comment_solution.id'), primary_key=True),
    db.Column('userid', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    info={'bind_key': None}
)

comment_solution_dislikes = db.Table('comment_solution_dislikes',
    db.Column('commentid', db.Integer, db.ForeignKey('comment_solution.id'), primary_key=True),
    db.Column('userid', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    info={'bind_key': None}
)


show_users_problem = db.Table('show_users_problem',
    db.Column('problemid', db.Integer, db.ForeignKey('problem.id'), primary_key=True),
    db.Column('userid', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    info={'bind_key': None}
)

show_users_solution = db.Table('show_users_solution',
    db.Column('solutionid', db.Integer, db.ForeignKey('solution.id'), primary_key=True),
    db.Column('userid', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    info={'bind_key': None}
)

class TypeUser(db.Model):
    """Типы пользователей"""
    __tablename__ = 'type_user'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    modified_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Связи (если есть отношение один-ко-многим)
    # users = db.relationship('User', backref='type_rel', lazy=True)  # УДАЛИТЕ эту строку, если в таблице user есть колонка type
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'modified_date': self.modified_date.isoformat() if self.modified_date else None,
            'created_date': self.created_date.isoformat() if self.created_date else None
        }

class User(db.Model):
    """Пользователи системы"""
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    favproblem = db.Column(db.Boolean, default=True, nullable=True)
    favsolution = db.Column(db.Boolean, default=False, nullable=True)
    image = db.Column(db.Text, nullable=True)
    isactive = db.Column(db.Boolean, default=True, nullable=True)
    lastlogin = db.Column(db.DateTime, nullable=True)
    username = db.Column(db.Text, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    modified_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    notification = db.Column(db.JSON, nullable=True)
    type = db.Column(db.Integer, db.ForeignKey('type_user.id'), nullable=True)  # Внешний ключ на type_user
    password_hash = db.Column(db.String(255), nullable=False, default='')
    isnew = db.Column(db.Boolean, default=True, nullable=False)
    
    # Связи
    refresh_tokens = db.relationship('RefreshToken', backref='user', lazy=True, cascade='all, delete-orphan')
    created_categories = db.relationship('Category', backref='creator_user', lazy=True, foreign_keys='Category.creator')
    created_problems = db.relationship('Problem', backref='creator_user', lazy=True, foreign_keys='Problem.creator')
    created_solutions = db.relationship('Solution', backref='creator_user', lazy=True, foreign_keys='Solution.creator')
    created_hashtags = db.relationship('Hashtag', backref='creator_user', lazy=True, foreign_keys='Hashtag.creator')
    created_topics = db.relationship('Topic', backref='creator_user', lazy=True, foreign_keys='Topic.creator')
    
    # Добавьте отношение к TypeUser
    type_rel = db.relationship('TypeUser', backref='users', lazy=True)
    
    # Связи многие-ко-многим
    favourite_problems = db.relationship('Problem', 
                                        secondary=favourite_problem, 
                                        backref='favourite_users',
                                        lazy=True)
    favourite_solutions = db.relationship('Solution',
                                         secondary=favourite_solution,
                                         backref='favourite_users',
                                         lazy=True)
    
    def __repr__(self):
        return f'<User {self.id}: {self.username}>'
    
    def generate_access_token(self):
        """Генерация access token для пользователя"""
        exp_sec = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 86400))
        expiration = datetime.utcnow() + timedelta(seconds=exp_sec)
        payload = {
            'username': self.username,
            'userID': self.id,
            'exp': expiration,
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'image': self.image,
            'favproblem': self.favproblem,
            'favsolution': self.favsolution,
            'isactive': self.isactive,
            'lastlogin': self.lastlogin.isoformat() if self.lastlogin else None,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'type': self.type,
            'isnew': self.isnew
        }

class RefreshToken(db.Model):
    """Токены обновления для аутентификации"""
    __tablename__ = 'refresh_token'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    token = db.Column(db.String(255), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    
    def is_expired(self):
        """Проверка истечения срока действия"""
        return datetime.utcnow() > self.expires_at
    
    def __repr__(self):
        return f'<RefreshToken {self.id} for user {self.user_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }

class Category(db.Model):
    """Категории проблем"""
    __tablename__ = 'category'
    
    id = db.Column(db.Integer, primary_key=True)
    isnew = db.Column(db.Boolean, default=True, nullable=False)
    name = db.Column(db.Text, nullable=False)
    modified_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    creator = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Связи
    problems = db.relationship('Problem', backref='category_rel', lazy=True)
    
    def to_dict(self):
        return {
            'ID': self.id,
            'Name': self.name,
            'isnew': self.isnew,
            'creator': self.creator,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'modified_date': self.modified_date.isoformat() if self.modified_date else None
        }

class Hashtag(db.Model):
    """Хэштеги для тегов"""
    __tablename__ = 'hashtag'
    
    id = db.Column(db.Integer, primary_key=True)
    isnew = db.Column(db.Boolean, default=True, nullable=False)
    name = db.Column(db.Text, nullable=False)
    show = db.Column(db.Integer, default=0, nullable=False)
    creator = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    modified_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Отношение к проблемам
    problems = db.relationship('Problem', 
                              secondary=hashtag_problem, 
                              back_populates='hashtags',
                              lazy=True)
    
    def to_dict(self):
        return {
            'ID': self.id,
            'Name': self.name,
            'isnew': self.isnew,
            'show': self.show,
            'creator': self.creator,
            'created_date': self.created_date.isoformat(),
            'modified_date': self.modified_date.isoformat()
        }
        
class Topic(db.Model):
    """Темы обсуждений"""
    __tablename__ = 'topic'
    
    id = db.Column(db.Integer, primary_key=True)
    is_new = db.Column(db.Boolean, default=True, nullable=False)
    name = db.Column(db.Text, nullable=False)
    creator = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    modified_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Связи
    problems = db.relationship('Problem', backref='topic_rel', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'is_new': self.is_new,
            'creator': self.creator,
            'created_date': self.created_date.isoformat(),
            'modified_date': self.modified_date.isoformat()
        }

class Problem(db.Model):
    """Проблемы"""
    # Используем 'Problem' с заглавной, как в SQL файле, но SQLAlchemy будет работать с обоими вариантами
    __tablename__ = 'problem'  # MySQL не чувствителен к регистру на Windows, но лучше использовать нижний регистр
    
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    describe = db.Column(db.Text, nullable=True)
    favourite = db.Column(db.Integer, default=0, nullable=False)
    fromauthor = db.Column(db.Boolean, default=False, nullable=False)
    isnew = db.Column(db.Boolean, default=True, nullable=False)
    creator = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    modified_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    image = db.Column(db.Text, nullable=False)
    name = db.Column(db.Text, nullable=False)
    reply = db.Column(db.Integer, nullable=True)
    show = db.Column(db.Integer, nullable=True)
    topic = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=True)
    
    solutions = db.relationship('Solution',
                               secondary=solution_problems,
                               backref='problems',
                               lazy=True)
    
    linked_problems = db.relationship('Problem',
                                     secondary=problem_link_problem,
                                     primaryjoin=id==problem_link_problem.c.problem_id,
                                     secondaryjoin=id==problem_link_problem.c.problem_link_id,
                                     backref='linking_problems',
                                     lazy=True)
    
    hashtags = db.relationship('Hashtag',
                              secondary=hashtag_problem,
                              back_populates='problems',
                              lazy=True)
    
    def to_dict(self):
        return {
            'ID': self.id,
            'Name': self.name,
            'Describe': self.describe,
            'Image': normalize_image_url(self.image) or '../images/default.png',
            'category': self.category,
            'creator': self.creator,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'show': self.show or 0,
            'favourite': self.favourite or 0,
            'reply': self.reply or 0,
            'fromauthor': self.fromauthor,
            'isnew': self.isnew,
            'topic': self.topic,
            'Hashtags': [hashtag.to_dict() for hashtag in self.hashtags] if self.hashtags else [],
            'Solutions': [solution.to_dict() for solution in self.solutions] if self.solutions else [],
            'LinkedProblems': [problem.to_dict() for problem in self.linked_problems] if self.linked_problems else []
        }
        
class Solution(db.Model):
    """Решения проблем"""
    __tablename__ = 'solution'
    
    id = db.Column(db.Integer, primary_key=True)
    complexity = db.Column(db.Integer, nullable=True)
    describe = db.Column(db.Text, nullable=False)
    efficiency = db.Column(db.Integer, nullable=True)
    favourite = db.Column(db.Integer, default=0, nullable=False)
    fromauthor = db.Column(db.Boolean, default=False, nullable=False)
    image = db.Column(db.Text, nullable=False)
    isbought = db.Column(db.Boolean, default=False, nullable=False)
    isnew = db.Column(db.Boolean, default=True, nullable=False)
    israting = db.Column(db.Boolean, default=False, nullable=False)
    like = db.Column(db.Integer, default=0, nullable=False)
    name = db.Column(db.Text, nullable=False)
    notlike = db.Column(db.Integer, default=0, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=True)
    rating = db.Column(db.Integer, default=0, nullable=False)
    reply = db.Column(db.Integer, default=0, nullable=False)
    show = db.Column(db.Integer, default=0, nullable=False)
    time = db.Column(db.Integer, nullable=True)
    creator = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    modified_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    attach = db.Column(db.JSON, nullable=True)
    
    comments = db.relationship('CommentSolution', 
                               backref='solution_rel',
                               lazy=True, 
                               cascade='all, delete-orphan')
    
    linked_solutions = db.relationship('Solution',
                                      secondary=solution_link_solution,
                                      primaryjoin=id==solution_link_solution.c.solution_id,
                                      secondaryjoin=id==solution_link_solution.c.solution_link_id,
                                      backref='linking_solutions',
                                      lazy=True)
    
    hashtags = db.relationship('Hashtag',
                               secondary=hashtag_solution,
                               backref='solutions',
                               lazy=True)
    
    def to_dict(self):
        return {
            'ID': self.id,
            'Name': self.name,
            'Describe': self.describe,
            'Image': normalize_image_url(self.image) or '../images/default.png',
            'creator': self.creator,
            'created_date': self.created_date.isoformat() if self.created_date else '',
            'show': self.show,
            'favourite': self.favourite,
            'like': self.like,
            'notlike': self.notlike,
            'reply': self.reply,
            'price': float(self.price) if self.price else 0,
            'efficiency': self.efficiency,
            'complexity': self.complexity,
            'time': self.time,
            'rating': self.rating,
            'isbought': self.isbought,
            'israting': self.israting,
            'isnew': self.isnew,
            'fromauthor': self.fromauthor,
            'attach': self.attach,
            # Комментарии будут загружаться лениво
            'Comments': [comment.to_dict() for comment in self.comments] if self.comments else [],
            'LinkedProblems': [problem.to_dict() for problem in self.problems] if self.problems else []
        }
        
class CommentSolution(db.Model):
    """Комментарии к решениям"""
    __tablename__ = 'comment_solution'
    
    id = db.Column(db.Integer, primary_key=True)
    isnew = db.Column(db.Boolean, default=True, nullable=False)
    likecount = db.Column(db.Integer, default=0, nullable=False)
    notlikecount = db.Column(db.Integer, default=0, nullable=False)
    solution_id = db.Column(db.Integer, db.ForeignKey('solution.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    creator = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    modified_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Добавляем relationship к Solution с back_populates
    solution = db.relationship('Solution', 
                               back_populates='comments',
                               foreign_keys=[solution_id],
                               overlaps="solution_rel")
    
    # Relationship к User
    creator_user = db.relationship('User', 
                                  foreign_keys=[creator])
    
    def to_dict(self):
        return {
            'ID': self.id,
            'Text': self.text,
            'CreatedDate': self.created_date.isoformat() if self.created_date else '',
            'creator': self.creator,
            'creator_name': self.creator_user.username if self.creator_user else '',
            'likecount': self.likecount,
            'notlikecount': self.notlikecount,
            'isnew': self.isnew,
            'solution_id': self.solution_id
        }

class SolutionRating(db.Model):
    """Оценки пользователей решений по категориям (цена, эффективность, сложность, время)"""
    __tablename__ = 'solution_rating'
    
    id = db.Column(db.Integer, primary_key=True)
    solution_id = db.Column(db.Integer, db.ForeignKey('solution.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rating_type = db.Column(db.String(20), nullable=False)  # 'price', 'efficiency', 'complexity', 'time'
    rating_value = db.Column(db.Integer, nullable=False)  # 1-5
    created_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    modified_date = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    solution = db.relationship('Solution', backref='user_ratings', foreign_keys=[solution_id])
    user = db.relationship('User', backref='solution_ratings', foreign_keys=[user_id])
    
    # Уникальный индекс: один пользователь может оценить решение только один раз по каждой категории
    __table_args__ = (
        db.UniqueConstraint('solution_id', 'user_id', 'rating_type', name='unique_user_solution_rating_type'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'solution_id': self.solution_id,
            'user_id': self.user_id,
            'rating_type': self.rating_type,
            'rating_value': self.rating_value,
            'created_date': self.created_date.isoformat() if self.created_date else '',
            'modified_date': self.modified_date.isoformat() if self.modified_date else ''
        }
        
class Notification(db.Model):
    """Уведомления пользователей"""
    __tablename__ = 'Notification'
    
    id = db.Column(db.Integer, primary_key=True)
    describe = db.Column(db.Text, nullable=False)
    name = db.Column(db.Text, nullable=False)
    read = db.Column(db.Boolean, default=False, nullable=False)
    user = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    creator = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    modified_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        return {
            'ID': self.id,
            'Name': self.name,
            'Description': self.describe,
            'Read': self.read,
            'user': self.user,
            'creator': self.creator,
            'CreatedDate': self.created_date.isoformat() if self.created_date else None,
            'modified_date': self.modified_date.isoformat() if self.modified_date else None
        }

class News(db.Model):
    """Новости"""
    __tablename__ = 'news'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    read_status = db.Column(db.Boolean, default=False, nullable=False)
    text_content = db.Column(db.Text, nullable=True)
    user = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    creator = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    modified_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'text_content': self.text_content,
            'read_status': self.read_status,
            'user': self.user,
            'creator': self.creator,
            'created_date': self.created_date.isoformat(),
            'modified_date': self.modified_date.isoformat()
        }

class TemporaryLinkProblem(db.Model):
    """Временные ссылки на проблему"""
    __tablename__ = 'temporary_link_problem'
    
    id = db.Column(db.Integer, primary_key=True)
    currentproblem = db.Column(db.Integer, db.ForeignKey('problem.id'), nullable=False)
    linkproblem = db.Column(db.Integer, db.ForeignKey('problem.id'), nullable=False)
    creator = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    modified_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'currentproblem': self.currentproblem,
            'linkproblem': self.linkproblem,
            'creator': self.creator,
            'created_date': self.created_date.isoformat(),
            'modified_date': self.modified_date.isoformat()
        }

class TemporaryLinkSolution(db.Model):
    """Временные ссылки на решение"""
    __tablename__ = 'temporary_link_solution'
    
    id = db.Column(db.Integer, primary_key=True)
    problem = db.Column(db.Integer, db.ForeignKey('problem.id'), nullable=False)
    solution = db.Column(db.Integer, db.ForeignKey('solution.id'), nullable=False)
    creator = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    modified_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'problem': self.problem,
            'solution': self.solution,
            'creator': self.creator,
            'created_date': self.created_date.isoformat(),
            'modified_date': self.modified_date.isoformat()
        }

class TemporaryProblemSolution(db.Model):
    """Временные связи проблемы и решения"""
    __tablename__ = 'temporary_problem_solution'
    
    id = db.Column(db.Integer, primary_key=True)
    problem = db.Column(db.Integer, db.ForeignKey('problem.id'), nullable=False)
    solution = db.Column(db.Integer, db.ForeignKey('solution.id'), nullable=False)
    creator = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    modified_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'problem': self.problem,
            'solution': self.solution,
            'creator': self.creator,
            'created_date': self.created_date.isoformat(),
            'modified_date': self.modified_date.isoformat()
        }

class UserCartSolution(db.Model):
    """Корзина пользователя для решений"""
    __tablename__ = 'user_cart_solution'
    
    id = db.Column(db.Integer, primary_key=True)
    is_bought = db.Column(db.Boolean, default=False, nullable=False)
    solution = db.Column(db.Integer, db.ForeignKey('solution.id'), nullable=False)
    user = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    creator = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    modified_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    solution_rel = db.relationship('Solution', foreign_keys=[solution])
    user_rel = db.relationship('User', foreign_keys=[user])
    
    def to_dict(self):
        return {
            'id': self.id,
            'is_bought': self.is_bought,
            'solution': self.solution,
            'user': self.user,
            'creator': self.creator,
            'created_date': self.created_date.isoformat(),
            'modified_date': self.modified_date.isoformat()
        }

class UserSolutionCategories(db.Model):
    """Категории решений пользователя"""
    __tablename__ = 'user_solution_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    complexity = db.Column(db.SmallInteger, nullable=True)
    efficiency = db.Column(db.SmallInteger, nullable=True)
    price = db.Column(db.SmallInteger, nullable=True)
    solution = db.Column(db.Integer, db.ForeignKey('solution.id'), nullable=False)
    time = db.Column(db.SmallInteger, nullable=True)
    user = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    creator = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    modified_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'complexity': self.complexity,
            'efficiency': self.efficiency,
            'price': self.price,
            'solution': self.solution,
            'time': self.time,
            'user': self.user,
            'creator': self.creator,
            'created_date': self.created_date.isoformat(),
            'modified_date': self.modified_date.isoformat()
        }

class UserSolutionImages(db.Model):
    """Изображения решений пользователя"""
    __tablename__ = 'user_solution_images'
    
    id = db.Column(db.Integer, primary_key=True)
    images = db.Column(db.JSON, nullable=True)
    user = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    creator = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    modified_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'images': self.images,
            'user': self.user,
            'creator': self.creator,
            'created_date': self.created_date.isoformat(),
            'modified_date': self.modified_date.isoformat()
        }

class UserActivity(db.Model):
    """Активность пользователя для рекомендаций"""
    __tablename__ = 'user_activity'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    activity_type = db.Column(db.String(50), nullable=False)  # 'create', 'search', 'favorite', 'view'
    entity_type = db.Column(db.String(20), nullable=False)  # 'problem' or 'solution'
    entity_id = db.Column(db.Integer, nullable=True)  # ID проблемы или решения
    search_query = db.Column(db.Text, nullable=True)  # Для типа 'search'
    created_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = db.relationship('User', backref='activities', foreign_keys=[user_id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'activity_type': self.activity_type,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'search_query': self.search_query,
            'created_date': self.created_date.isoformat() if self.created_date else None
        }

class PasswordResetToken(db.Model):
    """Токены для сброса пароля"""
    __tablename__ = 'password_reset_token'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    token = db.Column(db.String(255), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False, nullable=False)
    
    # Relationship к User
    user = db.relationship('User', backref='password_reset_tokens', foreign_keys=[user_id])
    
    def is_expired(self):
        """Проверка истечения срока действия"""
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self):
        """Проверка валидности токена"""
        return not self.used and not self.is_expired()
    
    def __repr__(self):
        return f'<PasswordResetToken {self.id} for user {self.user_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'used': self.used
        }


class Embedding(db.Model):
    """Векторные представления проблем и решений для поиска похожих"""
    __tablename__ = 'embedding'
    
    id = db.Column(db.Integer, primary_key=True)
    entity_type = db.Column(db.String(20), nullable=False)  # 'problem' or 'solution'
    entity_id = db.Column(db.Integer, nullable=False)
    embedding_vector = db.Column(db.JSON, nullable=False)  # JSON массив чисел (вектор)
    text_content = db.Column(db.Text, nullable=False)  # Текст для которого создан вектор
    model_name = db.Column(db.String(100), nullable=False, default='all-MiniLM-L6-v2')
    created_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    modified_date = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Уникальный индекс: один вектор на одну сущность
    __table_args__ = (
        db.UniqueConstraint('entity_type', 'entity_id', name='unique_entity_embedding'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'model_name': self.model_name,
            'text_content': self.text_content[:100] + '...' if len(self.text_content) > 100 else self.text_content,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'modified_date': self.modified_date.isoformat() if self.modified_date else None
        }


class UserKnowledge(db.Model):
    """Персональные знания пользователя на основе поиска и просмотров"""
    __tablename__ = 'user_knowledge'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Агрегированные данные о интересах
    top_categories = db.Column(db.JSON, nullable=True)  # [{category_id: int, count: int, name: str}]
    top_hashtags = db.Column(db.JSON, nullable=True)  # [{hashtag_id: int, count: int, name: str}]
    top_topics = db.Column(db.JSON, nullable=True)  # [{topic_id: int, count: int, name: str}]
    search_keywords = db.Column(db.JSON, nullable=True)  # [{keyword: str, count: int}]
    viewed_problems = db.Column(db.Integer, default=0, nullable=False)  # Количество просмотренных проблем
    viewed_solutions = db.Column(db.Integer, default=0, nullable=False)  # Количество просмотренных решений
    favorite_problems = db.Column(db.Integer, default=0, nullable=False)  # Количество избранных проблем
    favorite_solutions = db.Column(db.Integer, default=0, nullable=False)  # Количество избранных решений
    
    # Метаданные
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = db.relationship('User', backref='knowledge', foreign_keys=[user_id])
    
    # Уникальный индекс: один профиль знаний на пользователя
    __table_args__ = (
        db.UniqueConstraint('user_id', name='unique_user_knowledge'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'top_categories': self.top_categories or [],
            'top_hashtags': self.top_hashtags or [],
            'top_topics': self.top_topics or [],
            'search_keywords': self.search_keywords or [],
            'viewed_problems': self.viewed_problems,
            'viewed_solutions': self.viewed_solutions,
            'favorite_problems': self.favorite_problems,
            'favorite_solutions': self.favorite_solutions,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'created_date': self.created_date.isoformat() if self.created_date else None
        }