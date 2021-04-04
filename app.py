import os
from flask import Flask, render_template, session, flash, request, redirect
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy 
from flask_migrate import Migrate
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import logged_in, redirect_logged_in, none_if_nexist

# init our flask application 
app = Flask(__name__)
# from_object allows for configuration from files (config.py).
app.config.from_object('config')
# connect SQLAlchemy to app
db = SQLAlchemy(app)
# connect app and db to migration library
migration = Migrate(app, db)

# setting up session with our app
Session(app)

#------------
# Models
#------------
class User(db.Model):
  __tablename__ = 'users'
  id = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String(), nullable=False)
  password = db.Column(db.String(), nullable=False)
  # creating a one to many relationship here.
  # - cascade all delete, means that when a User is deleted, then delete all of the products associated with the user.
  children = db.relationship('Product', backref='user', cascade='all, delete')

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=True)
    description = db.Column(db.String(), nullable=False)
    price = db.Column(db.Float, nullable=False)
    total_stock = db.Column(db.Integer, nullable=False)
    userid = db.Column(db.Integer, db.ForeignKey('users.id'))

# for ajax requests (have to be logged in)
    
@app.route('/')
def index():
  session['userid'] = 1
  session['username'] = 'mario'
  if session.get('userid'):
    products = none_if_nexist(db.session.query(Product).all())
    return render_template('/pages/home.html', userid=session.get('userid'), products=products)
  else:
      return render_template('/layouts/main.html', userid=None)

@app.route("/signup")
@redirect_logged_in
def signup():
  return render_template('/forms/signup.html', userid=None)

def username_exists(username):
    return db.session.query(User).filter_by(username=username).first()

@app.route('/signup', methods=['POST'])
@redirect_logged_in
def signup_submission():
  username = request.form.get('username')
  password = request.form.get('password')
  confirmation = request.form.get('confirmation')

  # if user exist
  if username_exists(username):
    flash(f'A user with \'{username}\' already exists.', 'error')
    return redirect('/signup')

  # if password did not match confirmation
  if password != confirmation:
    flash("Password and confirmation do not match", "error")  
# next template is in signup route handler (/forms/signup.html) since flash appears there
    return redirect('/signup')

  # everything passed, create the user
  password = generate_password_hash(password)
  temp = User(username=username, password=password)
  try:
    # adding to transaction in current session, INSERT
    db.session.add(temp)
    # committing the transaction to be saved
    db.session.commit()
    # flash user with success message, and redirect for user to sign in to acc
    flash('User created!', 'success')
    return redirect('/signin')
  except Exception as e:
    print(e)
    # clearing the transaction, to keep balanced state of db
    db.session.rollback()
    # flash user, redirect to sign up page, so that flash next is called (revealing error)
    flash('Oh no, could not create user. Try again please.', 'error')
    return redirect('/signup')

@app.route('/signin')
@redirect_logged_in
def signin():
  return render_template('/forms/signin.html', userid=None)

@app.route('/signin', methods=['POST'])
@redirect_logged_in
def signin_submission():
  username = request.form.get('username')
  password = request.form.get('password')

  user = username_exists(username) 

  # check that the username does exist
  if not user:
      flash(f'{username} does not exist. Please try again.', 'error')
      return redirect('/signin')
  # check that password equals password in database
  if not check_password_hash(user.password, password):
      flash(f'Invalid password given for {username}. Please try again', 'error')
      return redirect('/signin')

  # if successful flash user ;)
  flash(f'You\'re now logged in. Welcome {username} :)', 'success')
  # - sign in the user, redirect to home page
  session['userid'] = user.id
  session['username'] = username
  #redirect the user back to home page
  return redirect('/')

@app.route('/signout')
@logged_in
def signout():
    # removing the user info from session "signed out"
    session.pop('userid')
    session.pop('username')
    flash('You\'re now signed out', 'info')
    return redirect('/')

################################### Products route controllers 
@app.route('/products')
@logged_in
def getProducts():
    """ Shows all the users products / options """
    products = none_if_nexist(db.session.query(Product).filter_by(userid=session.get('userid')).all())
    return render_template('/pages/user_products.html', products=products)
@app.route('/products/new')
@logged_in
def new_product():
    return render_template('/pages/new_product.html', userid=session.get('userid'))
@app.route('/products/new', methods=['POST'])
@logged_in
def new_product_submission():
    name = request.form.get('name')
    description = request.form.get('name')
    total_stock = request.form.get('total_stock')
    print(name, description, total_stock)
    flash('lasjkdf', 'info')
    return redirect('/products')
