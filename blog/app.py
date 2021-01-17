
from functools import wraps
from flask import Flask, render_template, request, session, redirect, url_for, g, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
# from werkzeug import secure_filename
from flask_mail import Mail
import json
import math
from datetime import datetime
from pathlib import Path
import os
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import hashlib


''' Basic config '''

UPLOAD_FOLDER = 'static/Blog_image/'
ALLOWED_EXTENSIONS = ['png', 'jpg', 'jpeg', 'gif']

local_server = True

app = Flask(__name__)

app.secret_key = '4^de1@w%^^r=_ofy(p8h2ylyl72%q_mipr9689c2ul2_l^08_8'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///blog.sqlite3"
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///blog.sqlite3"


db = SQLAlchemy(app)


''' Model config '''


class Contacts(db.Model):
    '''
    name,email,phone,msg
    '''
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(250), nullable=False)
    phone = db.Column(db.String(15), nullable=True)
    msg = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return '<Contacts %r>' % self.name


class Users(db.Model):
    '''
    first_name,last_name,email,password
    '''
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True, default=None)
    email = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(2500), nullable=False)
    phone = db.Column(db.String(15), nullable=True, default=None)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, nullable=False,
                           default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=True,
                           onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True, default=datetime.utcnow)

    def __repr__(self):
        return '<Users %r>' % self.first_name


class Blogs(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    users_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    users = db.relationship('Users', backref=db.backref('blogs', lazy=True))
    title = db.Column(db.String(250), nullable=False)
    slug = db.Column(db.String(250), nullable=True)
    content = db.Column(db.Text, nullable=False)
    tagline = db.Column(db.String(250), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False,
                           default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=True,
                           onupdate=datetime.utcnow)
    image = db.Column(db.String(1000), nullable=True, default=None)

    def __repr__(self):
        return '<Blogs %r>' % self.title


''' View Config '''


@app.route("/user/login", methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        try:
            email = request.form.get('email').strip()
            password = request.form.get('password')
            user = Users.query.filter_by(email=email).first()
            if user is None:
                flash('Please enter the correct email address and password for a login. Note that both fields may be case-sensitive.', 'danger')
                return redirect('/user/login')
            else:
                crpto_passowrd = str(user.password)
                password_state = check_password_hash(crpto_passowrd, password)
                if password_state:
                    session['user.first_name'] = str(user.first_name)
                    session['user.email'] = str(user.email)
                    session['user.is_authenticated'] = True
                    session['user.is_admin'] = user.is_admin
                    session['user.id'] = user.id
                    return redirect(url_for('home'))
                else:
                    flash(
                        'Please enter the correct email address and password for a login. Note that both fields may be case-sensitive.', 'danger')
                    return redirect('/user/login')

        except Exception as e:
            flash(e, 'error')
            return redirect('/user/login')

    return render_template('user/login.html')


@ app.route("/user/register", methods=['GET', 'POST'])
def user_register():

    if request.method == 'POST':
        try:
            first_name = request.form.get('first_name').strip()
            last_name = request.form.get('last_name').strip()
            email = request.form.get('email').strip()
            password = request.form.get('password').strip()
            # print(first_name, last_name, email, password)
            # result = hashlib.sha1(password)
            # password_hash =  str(result.hexdigest())
            password_hash = generate_password_hash(password)
            user = Users(first_name=first_name,
                         last_name=last_name,
                         email=email,
                         password=password_hash)
            db.session.add(user)
            db.session.commit()
            flash('Your Account is successfully created. Please Login!!', 'success')
            return redirect('/user/login')
        except IntegrityError as e:
            print(e)
            flash('Email is already used, please use new Email', 'danger')
            return redirect('/user/register')
        except Exception as e:
            flash(e, 'error')
            return redirect('/user/register')
    return render_template('user/register.html')


@ app.route('/user/logout')
def logout():
    # remove the username from the session if it is there
    session.pop('user.first_name', None)
    session.pop('user.email', None)
    session.pop('user.is_authenticated', None)
    session.pop('user.is_admin', None)
    session.pop('user.id', None)
    flash('Log Out Successfull', 'success')
    return redirect('/user/login')


def login_required(f):
    @ wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user.is_authenticated') is None:
            return redirect(url_for('user_login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def isadmin_required(f):
    @ wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user.is_admin') is False:
            return redirect('/user/dashboard')
        return f(*args, **kwargs)
    return decorated_function


@ app.route("/")
def home():
    blogs = Blogs.query.all()
    return render_template('blog/index.html', blogs=blogs)


@ app.route("/aboutus")
def aboutus():
    return render_template('blog/about.html')


@ app.route("/contactus", methods=['GET', 'POST'])
def contactus():
    if request.method == 'POST':
        try:
            name = request.form.get('name').strip()
            email = request.form.get('email')
            phone = request.form.get('phone').strip()
            msg = request.form.get('msg')
            # print(name, email, phone, msg)
            '''
            name,email,phone,msg
            '''
            contact = Contacts(name=name, email=email, phone=phone, msg=msg)
            db.session.add(contact)
            db.session.commit()

            flash('Your message is sucessfully sent', 'success')
            return redirect('/contactus')
        except Exception as e:
            flash(e, 'error')
            return redirect('/contactus')

    return render_template('blog/contact.html')


@ app.route("/blog/create", methods=['GET', 'POST'])
@ login_required
def blog_create():
    if request.method == 'POST':
        try:
            title = request.form.get('title').strip()
            slug = request.form.get('slug')
            tagline = request.form.get('tagline')
            content = request.form.get('content')
            file = request.files['image']
            if file:
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_location = filename
            # print(name, email, phone, msg)
            '''
            name,email,phone,msg
            '''
            # user = Users.query.get(session['user.id'])
            blog = Blogs(users_id=session['user.id'],
                         title=title,
                         slug=slug,
                         content=content,
                         tagline=tagline,
                         image=image_location)
            db.session.add(blog)
            db.session.commit()
#            flash('Your blog is sucessfully created', 'success')
            return redirect('/blog/'+str(blog.id))
        except Exception as e:
            print(e)
            flash(e, 'error')
            return redirect('/contactus')

    return render_template('blog/blog_create.html')


@ app.route("/blog/<int:blog_id>", methods=['GET'])
def post(blog_id):
    blog = Blogs.query.get(blog_id)
    return render_template('blog/post.html', blog=blog)


@ app.route("/user/dashboard")
@ login_required
def user_dashboard():
    dashboard_active = True
    user_count = len(Users.query.all())
    contacts_count = len(Contacts.query.all())
    blogs_count = len(Blogs.query.all())
    my_blogs_count = len(Blogs.query.filter_by(
        users_id=session['user.id']).all())
    return render_template('admin/index.html',
                           dashboard_active=dashboard_active,
                           user_count=user_count,
                           contacts_count=contacts_count,
                           blogs_count=blogs_count,
                           my_blogs_count=my_blogs_count
                           )


@ app.route("/user/profile", methods=['GET', 'POST'])
@ login_required
def user_profile():
    profile_active = True
    user = Users.query.get(session['user.id'])
    if request.method == 'POST':
        try:
            first_name = request.form.get('first_name').strip()
            last_name = request.form.get('last_name').strip()
            email = request.form.get('email').strip()
            phone = request.form.get('phone').strip()
            print(phone)
            if phone is None:
                phone = None
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.phone = phone
            db.session.commit()
            flash('Your Profile is successfully updated.!', 'success')
            return redirect('/user/profile')
        except IntegrityError as e:
            print(e)
            flash('Email is already used, please use new Email', 'danger')
            return redirect('/user/profile')
        except Exception as e:
            flash(e, 'error')
            return redirect('/user/profile')
    return render_template('admin/profile.html',
                           profile_active=profile_active,
                           user=user)


# @ app.route("/user/table")
# @ login_required
# def user_table():
#     return render_template('admin/table.html')


@ app.route("/user/blogs/my_blog")
@ login_required
def my_blogs():
    blogs = Blogs.query.filter_by(users_id=session['user.id']).all()
    blogs_counts = len(blogs)
    return render_template('admin/myblog.html', blogs=blogs, blogs_counts=blogs_counts)


@ app.route("/user/blogs/all")
@ login_required
@ isadmin_required
def all_blogs():
    blogs = Blogs.query.all()
    blogs_counts = len(blogs)
    return render_template('admin/allblogs.html', blogs=blogs, blogs_counts=blogs_counts)


@ app.route("/user/messages")
@ login_required
@ isadmin_required
def user_messages():
    contacts = Contacts.query.all()
    contacts_counts = len(contacts)
    return render_template('admin/message.html', contacts=contacts, contacts_counts=contacts_counts)


@ app.route("/user/users")
@ login_required
@ isadmin_required
def user_list():
    users = Users.query.all()
    users_counts = len(users)
    return render_template('admin/users.html', users=users, users_counts=users_counts)


''' Project main part '''
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000, debug=True, threaded=True)
