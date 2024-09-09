from flask import render_template, redirect, flash, url_for, request, abort
from app import app, db
import sqlalchemy as sa
from app.forms import LoginForm, RegisterForm, PostForm, CategoryForm
from app.models import User, Role, Post, Category, Tag
from flask_login import current_user, login_user, logout_user, login_required
from urllib.parse import urlsplit
from functools import wraps
from slugify import slugify
import time

def role_required(role_name):
    def decorator(func):
        @wraps(func)
        def decorated_view(*args, **kwargs):
            if not current_user.is_authenticated or not current_user.has_role(role_name):
                abort(403)  # Forbidden
            return func(*args, **kwargs)
        return decorated_view
    return decorator


@app.route('/')
@app.route('/home')
@login_required
def home():
    return render_template('index.html', title='Home')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == form.username.data)
        )
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('home')
        return redirect(url_for('home'))
    return render_template('login.html', title='Sign In', form=form)



@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulation you\'re now registered')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/assign_role/<int:user_id>', methods=['GET', 'POST'])
@login_required
def assign_role(user_id):
    #just admins can assign roles to other users
    if not current_user.has_role('Admin'):
        flash('You do not have permission to assign roles', 'danger')
        return redirect(url_for('home'))
    
    user = User.query.get_or_404(user_id)
    roles = Role.query.all()
    
    if request.method == 'POST':
        selected_roles = request.form.getlist('roles')
        user.roles.clear() #clear existing roles
        for role_name in selected_roles:
            role = Role.query.filter_by(name=role_name).first()
            if role:
                user.add_role(role)
                
        db.session.commit()
        flash(f"Roles updated for {user.username}", 'success')
        return redirect(url_for('user_list'))
    return render_template('assign_role.html', title='Assign Roles' ,user=user, roles=roles)


@app.route('/admin/dashboard')
@login_required
@role_required('Admin')
def admin_dashboard():
    if not current_user.has_role('Admin'):
        flash("You are not authorized to access this page.", 'danger')
        return redirect(url_for('home'))
    return render_template('dashboard.html')

@app.route("/post/new", methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    
    form.category_id.choices = [(c.id, c.name) for c in Category.query.all()]
    
    form.tags.choices = [(t.id, t.name) for t in Tag.query.all()]
    
    if form.validate_on_submit():
        #generate slug from title
        slug = slugify(form.title.data)
        
        #check if exist slug and adjust if any
        existing_post = Post.query.filter_by(slug=slug).first()
        if existing_post:
            slug = f'{slug}-{int(time.time())}'
        
        #create post
        post = Post(
            title=form.title.data,
            slug=slug,
            body=form.body.data,
            category_id = form.category_id.data,
            author_id = current_user.id
        )
        #Save in DB
        db.session.add(post)
        db.session.commit()
        
        flash('Post created successfully!', 'success')
        return redirect(url_for('home'))
    return render_template('create_post.html', form=form)

@app.route('/category/new', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def new_category():
    form = CategoryForm()
    
    if form.validate_on_submit():
        category = Category(name=form.name.data, description=form.description.data)
        db.session.add(category)
        db.session.commit()
        flash("Category has been added successfully!","success")
        return redirect(url_for('home'))
    return render_template('create_category.html', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

