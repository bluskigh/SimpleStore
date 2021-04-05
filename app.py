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
  cart = db.relationship('Cart', backref='cart_user', cascade='all, delete')

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=True)
    description = db.Column(db.String(), nullable=False, default='An item you can buy')
    price = db.Column(db.Float, nullable=False, default=5.0)
    total_stock = db.Column(db.Integer, nullable=False, default=1)
    image_link = db.Column(db.String(), nullable=False)
    userid = db.Column(db.Integer, db.ForeignKey('users.id'))

cart_products = db.Table('cart_products', db.Column('cart_id', db.Integer, db.ForeignKey('cart.id')), db.Column('product_id', db.Integer, db.ForeignKey('products.id')))

class Cart(db.Model):
    __tablename__ = 'cart'
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Integer, nullable=False) 
    # creating a one to one relationship between a cart and parent
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    # creating a one to many relationship between cart (parent) and children (products)
    products = db.relationship('Product', secondary=cart_products, backref=db.backref('cart', lazy=True))

#-----------
# Routes
#-----------
@app.route('/')
def index():
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
    # creating a cart for the current user
    temp_cart = Cart(amount=0, user_id=session.get('userid'))
    db.session.add(temp_cart)
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
    if session.get('userid'):
        # removing the user info from session "signed out"
        session.clear()
        flash('You\'re now signed out', 'success')
        return redirect('/')
    else:
        flash('You are not signed in.', 'info')
        return redirect('/') 

################################### Products route controllers 
@app.route('/products')
@logged_in
def getProducts():
    """ Shows all the users products / options """
    products = none_if_nexist(db.session.query(Product).filter_by(userid=session.get('userid')).all())
    return render_template('/pages/user_products.html', products=products, userid=session.get('userid'))
@app.route('/products/new')
@logged_in
def new_product():
    return render_template('/pages/new_product.html', userid=session.get('userid'))
@app.route('/products/new', methods=['POST'])
@logged_in
def new_product_submission():
    name = request.form.get('name')
    description = request.form.get('description')
    price = request.form.get('price')
    total_stock = request.form.get('total_stock')
    image_link = request.form.get('image_link')

    if not name or not description or not price or not total_stock or not image_link:
        flash('Missing required field\'s. Try again.', 'error')
        return redirect('/products/new')

    # product cannot have duplicate name
    result = db.session.query(Product).filter((Product.name.like(f'%{name}%')) & (Product.userid==session.get('userid'))).first()
    if result:
        flash('A product with that name already exist', 'error')
        return redirect('/products/new')

    try:
        # add the product to the page
        temp = Product(name=name, description=description, price=price, total_stock=total_stock, image_link=image_link, userid=session.get('userid')) 
        db.session.add(temp)
        db.session.commit()
    except Exception as e:
        print(e)
        db.session.rollback()
        flash('Could not add the product to the database...Please try again', 'error')
        return redirect('/products/new')

    flash('Added the prodct to the database!', 'success')
    return redirect('/products')
@app.route('/products/<int:product_id>')
def get_product_info(product_id):
    """ Runs when \"see more \" is clicked displays more options for the item """
    product = db.session.query(Product).get(product_id)

    # check if product exist
    if not product:
        flash('Hmm...Product does not exist anymore.', 'info')
        return redirect('/')

    # send back information about the product
    return render_template('/pages/view_product.html', products=[product], userid=session.get('userid'))
@app.route('/products/<int:product_id>/put')
@logged_in
def update_product(product_id):
    """ Edit product page (only available fo the owner """
    product = db.session.query(Product).get(product_id)
    if product.userid != session.get('userid'):
        flash('You\'re not the owner of this product.', 'error')
        return redirect('/')
    return render_template('/pages/update_product.html', product=product)

@app.route('/products/<int:product_id>/put', methods=['POST'])
@logged_in
def update_product_submission(product_id):
    product = db.session.query(Product).get(product_id)

    # check that the product exists
    if not product:
        flash('Could not find this product in our database.', 'info')
        return redirect(f'/products/{{product_id}}')

    # check that the product contains the same userid as currently in session
    if product.userid != session.get('userid'):
        flash('You cannnot edit a product that does not belong to you.', 'error')
        return redirect('/')
    
    name = request.form.get('name')
    description = request.form.get('description')
    price = request.form.get('price')
    total_stock = request.form.get('total_stock')
    image_link = request.form.get('image_link')

    # only update the necessary things that need to be updated
    if name != product.name:
        product.name = name
    if description != product.description:
        product.description = description
    if price != product.price:
        product.price = price
    if total_stock != product.total_stock:
        product.total_stock = total_stock
    if image_link != product.image_link:
        product.image_link = image_link

    try:
        # commit transactions (updates)
        db.session.commit()
        flash('Updated your product!', 'success')
        return redirect('/products')
    except Exception as e:
        print(e)
        db.session.rollback()
        flash('Could not updated your product. Try again.', 'error')
        return redirect('/products/{{product_id}}/put')
