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

#Check role of user
def role_required(role_name):
    def decorator(func):
        @wraps(func)
        def decorated_view(*args, **kwargs):
            if not current_user.is_authenticated or not current_user.has_role(role_name):
                abort(403)  # Forbidden
            return func(*args, **kwargs)
        return decorated_view
    return decorator


#Main page
@app.route('/')
@app.route('/home')
@login_required
def home():
    if current_user.is_authenticated:
        #getting list of ids [followed and user.authenticated]
        following_ids = [user.id for user in current_user.followed]
        following_ids.append(current_user.id)
        
        #fetch posts from all the ids
        posts = Post.query.filter(Post.author_id.in_(following_ids)).order_by(Post.create_at.desc()).all()

    return render_template('index.html', title='Home', posts=posts)

#Login user
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

#Profile
@app.route('/profile/<username>')
@login_required
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('profile.html', user=user, title='Profile')


#Register new users
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

#Asign role: Just user with Admin role is able to edit role
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

#Dasboard: endpoint able just for admin users
@app.route('/admin/dashboard')
@login_required
@role_required('Admin')
def admin_dashboard():
    if not current_user.has_role('Admin'):
        flash("You are not authorized to access this page.", 'danger')
        return redirect(url_for('home'))
    return render_template('dashboard.html')

#Create new post
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
            tags = form.tags.data,
            author_id = current_user.id
        )
        #Save in DB
        db.session.add(post)
        db.session.commit()
        
        flash('Post created successfully!', 'success')
        return redirect(url_for('home'))
    else:
        print(form.errors)
    return render_template('create_post.html', form=form)

#Read post by slug
@app.route('/post/<slug>')
@login_required
def read_post(slug):
    post = Post.query.filter_by(slug=slug).first_or_404()
    return render_template('_post.html', post=post)

#Read All posts
@app.route('/posts')
@login_required
def read_all_posts():
    posts = Post.query.all()
    return render_template('posts.html', posts=posts)

#Update post by slug
@app.route('/post/<slug>/edit', methods=['GET', 'POST'])
@login_required
def update_post(slug):
    post = Post.query.filter_by(slug=slug).first_or_404()
    form = PostForm(obj=post)
    
    if post.author_id != current_user.id and not current_user.has_role('Admin'):
        flash('You do not have permission to delete this post.', 'danger')
        return redirect(url_for('home'))
    
    form.category_id.choices = [(c.id, c.name) for c in Category.query.all()]
    
    form.tags.choices = [(t.id, t.name) for t in Tag.query.all()]
    
    if form.validate_on_submit():
        post.title = form.title.data
        post.body = form.body.data
        post.category_id = form.category_id.data
        post.tags = form.tags.data
        db.session.commit()
        flash('Post updated successfully!', 'success')
        return redirect(url_for('home', id=post.id))
    return render_template('edit_post.html', form=form)


#delete post
@app.route('/post/<slug>/delete')
@login_required
def delete_post(slug):
    post = Post.query.filter_by(slug=slug).first_or_404()
    
    if post.author_id != current_user.id and not current_user.has_role('Admin'):
        flash('You do not have permission to delete this post.', 'danger')
        return redirect(url_for('home'))
    
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for('home'))

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


#Follow route
@app.route('/follow/<username>')
@login_required
def follow(username):
    user_to_follow = User.query.filter_by(username=username).first_or_404()
    if user_to_follow == current_user:
        flash('You cannot follow yourself!')
        return redirect(url_for('profile', username=username))
    
    if not current_user.is_following(user_to_follow):
        current_user.follow(user_to_follow)
        db.session.commit()
        flash(f'You are now following {username}!')
    else:
         flash(f'You are already following {username}.')
         
    return redirect(url_for('profile', username=username))

#Unfollow route
@app.route('/route/<username>')
@login_required
def unfollow(username):
    user_to_unfollow = User.query.filter_by(username=username).first_or_404()
    if user_to_unfollow == current_user:
        flash("You cannot unfollow yourself!")
        return redirect(url_for('profile', username=username))
    if current_user.is_following(user_to_unfollow):
        current_user.unfollow(user_to_unfollow)
        db.session.commit()
        flash(f'You have unfollowed {username}')
    else:
        flash(f"You are not following {username}")
        
    return redirect(url_for("profile", username=username))




@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

