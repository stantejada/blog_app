from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectMultipleField, SelectField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo, Optional
import sqlalchemy as sa 
from app import db
from app.models import User, Post, Tag, Category
from slugify import slugify




class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Login')
    
class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')]
    )
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        user = db.session.scalar(sa.select(User).where(
            User.username == username.data
        ))
        if user is not None:
            raise ValidationError('Please use a different username')
    
    def validate_email(self, email):
        user = db.session.scalar(
            sa.select(User).where(
                User.email == email.data
            )
        )
        if user is not None:
            raise ValidationError('Please use a different email')


class PostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    body = TextAreaField('Body', validators=[DataRequired()])
    
    
    category_id = SelectField('Category', coerce=int, validators=[Optional()])
    
    tags = SelectMultipleField('Tags', coerce=int, validators=[Optional()])

    
    is_published = BooleanField('Publish?')
    submit = SubmitField('Publish')

    def validate_slug(self, slug):
        if Post.query.filter_by(slug=slug.data).first():
            raise ValidationError('Slug already in use')
        
        
class CategoryForm(FlaskForm):
    name = StringField('Category', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    submit = SubmitField('Add')
    
    def validate_category(self,name):
        category = db.session.scalar(
            sa.select(Category).where(
                Category.name == name.data
            )
        )
        if category is not None:
            raise ValidationError('Category already exist!')