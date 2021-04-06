# import os
from flask import Flask, render_template, session, flash, request, redirect, jsonify
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy 
from flask_migrate import Migrate
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import logged_in, redirect_logged_in, none_if_nexist, get_user_instance

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
  products = db.relationship('Product', backref='user', cascade='all, delete')
  cart = db.relationship('Cart', backref='cart_user', cascade='all, delete', uselist=False)

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=True)
    description = db.Column(db.String(), nullable=False, default='An item you can buy')
    price = db.Column(db.Float, nullable=False, default=5.0)
    total_stock = db.Column(db.Integer, nullable=False, default=1)
    image_link = db.Column(db.String(), nullable=False)
    userid = db.Column(db.Integer, db.ForeignKey('users.id'))

# association table for product and cart
cart_products = db.Table('cart_products', db.Column('cart_id', db.Integer, db.ForeignKey('cart.id')), db.Column('product_id', db.Integer, db.ForeignKey('products.id')))

class Cart(db.Model):
    __tablename__ = 'cart'
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Integer, nullable=False) 
    # creating a one to one relationship between a cart and parent
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    # creating a one to many relationship between cart (parent) and children (products)
    products = db.relationship('Product', secondary=cart_products, backref=db.backref('cart', lazy=True), cascade="all, delete")

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
    # adding to transaction in current session, INSERT
    db.session.add(temp)
    # creating a cart for the current user
    temp_cart = Cart(amount=0, user_id=temp.id)
    db.session.add(temp_cart)
    # flash user with success message, and redirect for user to sign in to acc
    # committing the transaction to be saved
    db.session.commit()
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

#----------------
# Account routes
#----------------
@app.route('/account')
@logged_in
def account():
    return render_template('/pages/account.html', userid=session.get('userid'))
@app.route('/account/<int:account_id>/delete', methods=['POST'])
def delete_submission(account_id):
    # find the account
    user = get_user_instance(db, User)
    print(user)
    if user.id != session.get('userid'):
        flash('You\'re are not allowed to delete other users accounts', 'error')
        # actually going to sign the particular person out
        return redirect('/signout')
    
    try:
        # delete the account
        db.session.delete(user)
        db.session.commit()
        flash('Account Deleted.', 'success')
        # clear the session
        session.clear()
        return redirect('/')
    except Exception as e:
        print(e)
        db.session.rollback()
        flash('Could not delete your account. Try again.', 'error')
        return redirect('/account')
    
#-----
# Cart Routes
#-----
# api route (make ajax fetch request and or XMLHTTP)
@app.route('/cart/amount')
@logged_in
def get_cart_amount():
    try:
        curr_user = get_user_instance(db, User)
        # TODO make logged_in decorator check for existing user, not just that the session contains a user
        return jsonify({'amount': curr_user.cart.amount})
    except Exception as e:
        print(e)
        flash('A problem occurred when attempting to get your cart amount', 'error')
        return redirect('/')
@app.route('/cart/add', methods=["POST"])
@logged_in
def cart_add_submission():
    id_ = request.get_json('id')
    # TODO: turn this process of getting id into a decorator (used for remove too)
    if not id_:
        return jsonify({'result': False})
    # add the id to the current users cart
    user = get_user_instance(db, User) 
    if not user:
        return jsonify({'result': False})

    product = db.session.query(Product).get(id_);
    if product.total_stock == 0:
        return jsonify({'result': False, 'message': f'Product "{product.name}" is out of STOCK!'})
    try:
        user.cart.products.append(db.session.query(Product).get(id_))
        user.cart.amount += 1
        db.session.commit()
        return jsonify({'result': True})
    except Exception as e:
        print(e)
        db.session.rollback()
        return jsonify({'result': False})
@app.route('/cart/remove', methods=['POST'])
@logged_in
def cart_remove_submission():
    id_ = request.get_json('id')
    if not id_:
        return jsonify({'result': False})
    user = get_user_instance(db, User)
    if not user:
        return jsonify({'result': False})
    try:
        # basically, we do not want to remove the product itself, because other users rely on it too. So intead, we want to remove the product from our assocation table called cart_products.
        # NOOOOOOOOOOOO
        total = user.cart.products.remove(db.session.query(Product).get(id_))
        user.cart.amount -= 1

        # TODO truly understand how you removed, like does remove take in instances of a query product class object? Also does remove() return the amoutns of items removed? 
        # TODO: say the user has multiple items of a thing, remove x amount of items only.
        db.session.commit()
        return jsonify({'result': True})
    except Exception as e:
        print(e)
        db.session.rollback()
        # vital
        db.session.close()
        return jsonify({'result': False})
    # TODO: think about relpacing removed / added into success, because it makes it more general, thus makes it easier to write decorator function

@app.route('/cart/<int:product_id>/exist')
@logged_in
def exist_in_cart(product_id):
    user = get_user_instance(db, User)
    for product in user.cart.products:
        if product.id == product_id:
            return jsonify({'result': True}) 
    return jsonify({'result': False})

@app.route("/cart/clear")
@logged_in
def clear_cart():
    try:
        user = get_user_instance(db, User) 
        products = user.cart.products
        length = len(products)
        # think about a pop() method but in a first in first out stack
        # popping out first item until length is 0
        while length > 0:
            products.remove(products[0])
            length-=1
        user.cart.amount = 0
        db.session.commit()
        flash('Cleared your cart', 'success')
        return redirect('/')
    except Exception as e:
        print(e)
        db.session.rollback()
        flash('Could not clear your cart', 'error')
        return redirect('/cart')

@app.route('/cart')
@logged_in
def cart():
    user = get_user_instance(db, User)
    return render_template('/pages/cart.html', products=user.cart.products, userid=session.get('userid'))
#----------
# Search Routes
#----------
@app.route('/search')
@logged_in
def search():
    query = request.args.get('query')
    products = None
    if query:
        query = query.split(' ')
        # related products when LIKE all the words in the query results in a none result.
        products_query = db.session.query(Product).filter(Product.name.ilike(f'%{query[0]}%'))
        if products_query:
            for word in query[1:]:
                word = f'%{word}%'
                temp = products_query.filter(Product.name.like(word))
                if temp.first():
                    products_query = temp;
            products = products_query.all()

        print(f'Products: {products}')
    return render_template('/pages/search.html', userid=session.get('userid'), products=products, query=query)
