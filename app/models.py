from typing import Optional, List
import  sqlalchemy as sa 
import sqlalchemy.orm as so
from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime, timezone



post_tags = sa.Table(
    'post_tags',
    db.Model.metadata,
    sa.Column('post_id', sa.Integer, sa.ForeignKey('posts.id'), primary_key=True),
    sa.Column('tag_id', sa.Integer, sa.ForeignKey('tags.id'), primary_key=True)
)

#User models
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(150), index=True, unique=True)
    password_hash: so.Mapped[str] = so.mapped_column(sa.String(256))
    
    bio: so.Mapped[Optional[str]] = so.mapped_column(sa.Text)
    
    posts: so.Mapped[List['Post']] = so.relationship('Post', backref='user', lazy=True)
    
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password=password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password=password)
  

#post Models  
class Post(db.Model):
    __tablename__ = 'posts'
    
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    title: so.Mapped[str] = so.mapped_column(sa.String(255), nullable=False)
    slug: so.Mapped[str] = so.mapped_column(sa.String(255), unique=True, nullable=False)
    body: so.Mapped[str] = so.mapped_column(sa.Text, nullable=False)
    create_at: so.Mapped[datetime] = so.mapped_column(sa.DateTime, default=lambda: datetime.now(timezone.utc))
    update_at: so.Mapped[datetime] = so.mapped_column(sa.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=timezone.utc)
    published_at: so.Mapped[Optional[datetime]] = so.mapped_column(sa.DateTime)
    is_published: so.Mapped[bool] = so.mapped_column(sa.Boolean, default=False)
    
    author_id: so.Mapped[int] = so.mapped_column(sa.Integer, sa.ForeignKey('users.id'), nullable=False)
    
    category_id: so.Mapped[Optional[int]] = so.mapped_column(sa.Integer, sa.ForeignKey('categories.id'))
    
    #relacion de muchos a muchos
    tags: so.Mapped[List['Tag']] = so.relationship('Tag', secondary=post_tags, back_populates='posts')


#category models
class Category(db.Model):
    __tablename__ = 'categories'
    
    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(100), nullable=False, unique=True)
    description: so.Mapped[Optional[str]] = so.mapped_column(sa.Text)
    
    #Relacion de muchos a muchos
    posts: so.Mapped[List['Post']] = so.relationship('Post', backref='category', lazy=True)
    
class Tag(db.Model):
    __tablename__ = 'tags'
    
    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(100), nullable=False, unique=True)
    
    posts: so.Mapped[List['Post']] = so.relationship('Post', secondary=post_tags, back_populates='tags')

@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))