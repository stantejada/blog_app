from typing import Optional, List
import  sqlalchemy as sa 
import sqlalchemy.orm as so
from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime, timezone
from slugify import slugify
from sqlalchemy import event
from hashlib import md5


post_tags = sa.Table(
    'post_tags',
    db.Model.metadata,
    sa.Column('post_id', sa.Integer, sa.ForeignKey('posts.id'), primary_key=True),
    sa.Column('tag_id', sa.Integer, sa.ForeignKey('tags.id'), primary_key=True)
)

user_roles = sa.Table(
    'user_roles',
    db.Model.metadata,
    sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'), primary_key=True),
    sa.Column('role_id', sa.Integer, sa.ForeignKey('roles.id'), primary_key=True)
)

followers = sa.Table(
    'followers',
    db.Model.metadata,
    sa.Column('follower_id', sa.Integer, sa.ForeignKey('users.id'), primary_key=True),
    sa.Column('followed_id', sa.Integer, sa.ForeignKey('users.id'), primary_key=True)
)

#User models
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(150), index=True, unique=True)
    password_hash: so.Mapped[str] = so.mapped_column(sa.String(256))
    
    bio: so.Mapped[Optional[str]] = so.mapped_column(sa.Text)
    
    roles: so.Mapped[List['Role']] = so.relationship('Role',
                                                     secondary=user_roles,
                                                     back_populates='users')
    
    
    posts: so.Mapped[List['Post']] = so.relationship('Post', back_populates='author')
    
    followed = so.relationship(
        'User',
        secondary='followers',
        primaryjoin=id==followers.c.follower_id,
        secondaryjoin=id==followers.c.followed_id,
        backref='followers',
        lazy='dynamic'
    )
    
    notifications: so.Mapped[List['Notification']] = so.relationship('Notification', back_populates='user')

    
    
    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return f"https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}"
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password=password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password=password)
  
    def has_role(self, role_name):
        return any(role.name == role_name for role in self.roles)
    
    def add_role(self, role):
        if not self.has_role(role.name):
            self.roles.append(role)
    
    def remove_role(self, role):
        if self.has_role(role.name):
            self.roles.remove(role)
            
    #helper methods [follow, followed]
    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)
    
    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)
    
    def is_following(self, user):
        return self.followed.filter_by(id=user.id).first() is not None
    
    def followers_count(self):
        return len(self.followers)


#post Models  
class Post(db.Model):
    __tablename__ = 'posts'
    
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    title: so.Mapped[str] = so.mapped_column(sa.String(255), nullable=False)
    slug: so.Mapped[str] = so.mapped_column(sa.String(255), unique=True, nullable=False)
    body: so.Mapped[str] = so.mapped_column(sa.Text, nullable=False)
    create_at: so.Mapped[datetime] = so.mapped_column(sa.DateTime, default=lambda: datetime.now(timezone.utc))
    update_at: so.Mapped[datetime] = so.mapped_column(sa.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    published_at: so.Mapped[Optional[datetime]] = so.mapped_column(sa.DateTime)
    is_published: so.Mapped[bool] = so.mapped_column(sa.Boolean, default=False)
    
    author_id: so.Mapped[int] = so.mapped_column(sa.Integer, sa.ForeignKey('users.id'), nullable=False)
    
    author: so.Mapped['User'] = so.relationship('User', back_populates='posts')
    
    category_id: so.Mapped[Optional[int]] = so.mapped_column(sa.Integer, sa.ForeignKey('categories.id'))
    
    #relacion de muchos a muchos
    tags: so.Mapped[List['Tag']] = so.relationship('Tag', secondary=post_tags, back_populates='posts')
    
    notifications: so.Mapped[List['Notification']] = so.relationship('Notification', back_populates='post')


#Automatically generate slug before saving
@event.listens_for(Post, 'before_insert')
def generate_slug_before_insert(mapper, connection, target):
    if not target.slug:
        target.slug = slugify(target.title)
        
        
@event.listens_for(Post, 'before_update')
def generate_slug_before_insert(mapper, connection, target):
    if target.title:
        target.slug = slugify(target.title)

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

class Role(db.Model):
    __tablename__ ='roles'
    
    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key = True)
    name: so.Mapped[str] = so.mapped_column(sa.String(50), unique=True, nullable=False)
    description: so.Mapped[str] = so.mapped_column(sa.Text)
    
    #many to many
    users: so.Mapped[List['User']] = so.relationship('User', secondary=user_roles, back_populates='roles')
    
    
class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True)
    user_id: so.Mapped[int] = so.mapped_column(sa.Integer, sa.ForeignKey('users.id'))
    post_id: so.Mapped[Optional[int]] = so.mapped_column(sa.Integer, sa.ForeignKey('posts.id'))
    message: so.Mapped[str] = so.mapped_column(sa.String(255))
    is_read: so.Mapped[bool] = so.mapped_column(sa.Boolean, default=False)
    timestamp: so.Mapped[datetime] = so.mapped_column(sa.DateTime, default=lambda: datetime.now(timezone.utc))
    
    user: so.Mapped['User'] = so.relationship('User', back_populates='notifications')
    post: so.Mapped['Post'] = so.relationship('Post', back_populates='notifications')



@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))