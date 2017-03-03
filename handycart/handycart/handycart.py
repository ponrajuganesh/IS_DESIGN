from __future__ import print_function
from sqlite3 import dbapi2 as sqlite3
from flask import Flask, request, session, url_for, redirect, render_template, jsonify, abort, g, flash, _app_ctx_stack
from werkzeug import check_password_hash, generate_password_hash

import os
import sys
import ast
import json

#configurations
DATABASE = 'data.db'
DEBUG = True
SECRET_KEY = 'isdesign1234'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, DATABASE)

app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar('HANDYCART_SETTINGS', silent=True)

DAYS = {
	0: 'M',
	1: 'T',
	2: 'W',
	3: 'T',
	4: 'F',
	5: 'Sa',
	6: 'Su'
}

FREQUENCY = {
	0: 'Weekly',
	1: 'Bi-Weekly',
	2: 'Monthly'
}

UNITS = {
	1: 'Oz',
	2: 'Count',
	3: 'lb'
}
def get_db():
	"""Opens a new database connection if there is none yet for the
	current application context.
	"""
	top = _app_ctx_stack.top
	if not hasattr(top, 'sqlite_db'):
		top.sqlite_db = sqlite3.connect(DATABASE_PATH)
		top.sqlite_db.row_factory = sqlite3.Row
	return top.sqlite_db


@app.teardown_appcontext
def close_database(exception):
	"""Closes the database again at the end of the request."""
	top = _app_ctx_stack.top
	if hasattr(top, 'sqlite_db'):
		top.sqlite_db.close()

def query_db(query, args=(), one=False):
	"""Queries the database and returns a list of dictionaries."""
	cur = get_db().execute(query, args)
	rv = cur.fetchall()
	return (rv[0] if rv else None) if one else rv

@app.route('/login', methods=['GET', 'POST'])
def login():
	errors = {}
	errors['username'] = None
	errors['passsword'] = None
	is_seller = False

	if request.method == 'POST':
		user = query_db("select * from user where username = ?", [request.form['username']], one=True)

		if user is None:
			user = query_db("select * from seller where username = ?", [request.form['username']], one=True)
			is_seller = True

		if user is None:
			errors['username'] = 'Invalid username'
		elif not check_password_hash(user['password'], request.form['password']):
			errors['password'] = 'Invalid password'
		else:
			session['user_id'] = user['id']
			session['is_seller'] = is_seller
			return redirect(url_for('get_products', category_id="3"))

	return render_template('login.html', errors=errors)

def check_user_exists(username, is_seller):
	table_name = ""

	if is_seller:
		table_name = "seller"
	else:
		table_name = "user"

	user = query_db("select * from " + table_name + " where username = ?", [username], one=True)

	if user:
		return True
	else:
		return False

@app.route('/register', methods=['GET', 'POST'])
def register():
	errors, error, is_seller = {}, False, False

	errors['enter_username'] = None
	errors['enter_password'] = None
	errors['password_mismatch'] = None
	errors['seller_taken'] = None
	errors['customer_taken'] = None
	errors['email'] = None

	if request.method == 'POST':
		if not request.form['email'] or '@' not in request.form['email']:
			errors['email'] = 'You must enter an email'
			error = True
		elif not request.form['username']:
			errors['enter_username'] = 'You must enter an username'
			error = True
		elif not request.form['password']:
			errors['enter_password'] = 'You have to enter a password'
			error = True
		elif request.form['password'] != request.form['password2']:
			errors['password_mismatch'] = 'Passwords should match'
			error = True
		elif request.args.get('is_seller') == '1':
			is_seller = True
			if check_user_exists(request.form['username'], is_seller=is_seller):
				errors['seller_taken'] = 'Seller username is already taken'
				error = True
		elif request.args.get('is_seller') == '0':
			is_seller = False
			if check_user_exists(request.form['username'], is_seller=is_seller):
				errors['customer_taken'] = 'Customer Username is already taken'
				error = True

		if not error:
			db = get_db()
			if is_seller:
				db.execute("insert into seller (email, password, username) values (?, ?, ?)", [request.form['username'], generate_password_hash(request.form['password']), request.form['username']])
			else:
				db.execute("insert into user (email, password, username) values (?, ?, ?)", [request.form['username'], generate_password_hash(request.form['password']), request.form['username']])
			db.commit()

			session['is_seller'] = is_seller
			return redirect(url_for('login'))

	return render_template('register.html', errors=errors)

@app.before_request
def before_request():
	g.categories = None
	g.categories = query_db('select * from category order by name')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('abort.html')

@app.route('/')
def index():
	return redirect(url_for('login'))

@app.route('/products')
def get_products():
	if 'user_id' not in session:
		return render_template('abort.html')

	selected_category = query_db("select name from category where id = ?", [request.args.get('category_id')], one=True)
	products = query_db("select * from product where category_id = ?", [request.args.get('category_id')])
	categories = query_db("select * from category order by name")
	return render_template('products.html', categories=categories, products=products, category_id=request.args.get('category_id'), category_name=selected_category['name'], is_seller=session['is_seller'])

@app.route('/subscribe')
def subscribe_product():
	if 'user_id' not in session:
		return render_template('abort.html')

	quantity, product_id = request.args.get('quantity'), request.args.get('product_id')
	prices, quantities = None, None

	if quantity and not quantity == "ALL":
		prices = query_db("select price.*, seller.* from price, seller where price.seller_id = seller.id and product_id = ? and price.quantity = ? order by price.cost", [product_id, quantity])
		quantities = query_db("select price.quantity from price, seller where price.seller_id = seller.id and product_id = ? order by price.cost", [product_id])
	else:
		quantity = "ALL"
		prices = query_db("select price.*, seller.* from price, seller where price.seller_id = seller.id and product_id = ? order by price.cost", [product_id])
		quantities = query_db("select price.quantity from price, seller where price.seller_id = seller.id and product_id = ? order by price.cost", [product_id])

	product = query_db("select * from product where id = ?", [product_id], one=True)
	unit = query_db("select name from units where id = ?", [product['units_id']], one=True)
	return render_template('subscribe.html', selected_quantity=quantity, quantities=quantities, product=product, prices=prices, units_name=unit['name'], category_id=request.args.get('category_id'), category_name=request.args.get('category_name'), categories=g.categories)

@app.route('/set_product_properties')
def set_product_properties():
	product_id, category_id = request.args.get('product_id'), request.args.get('category_id')
	product = query_db("select * from product where id = ?", [product_id], one=True)
	category_name = query_db("select name from category where id = ?", [category_id], one=True)
	return render_template('set-product-properties.html', categories=g.categories, product=product, category_name=category_name['name'], category_id=category_id, units_name=UNITS[int(product['units_id'])], is_seller=session['is_seller'])

# @app.route('/add_subscription', methods=['POST'])
@app.route('/add_subscription')
def add_subscription():
	if 'user_id' not in session:
		return render_template('abort.html')

	# frequency, days, price_id = request.form['frequency'], request.form['days'], request.form['price_id']
	frequency, days, price_id = request.args.get('frequency'), request.args.get('days'), request.args.get('price_id')
	db = get_db()
	db.execute("insert into subscription (user_id, price_id, days, frequency) values (?, ?, ?, ?)", [session['user_id'], price_id, days, frequency])
	db.commit()
	# return redirect(url_for('get_subscriptions'))
	return jsonify(result="Inserted")

@app.route('/get_subscriptions')
def get_subscriptions():
	if 'user_id' not in session:
		return render_template('abort.html')

	user_id = session['user_id']

	subscriptions_raw_data = query_db("select * from subscription where user_id = ?", [user_id])
	processed_subscriptions = []
	for subscription in subscriptions_raw_data:
		processed_subscription = {}

		price = query_db("select * from price where id = ?", [subscription['price_id']], one=True)
		seller = query_db("select * from seller where id = ?", [price['seller_id']], one=True)
		product = query_db("select * from product where id = ?", [price['product_id']], one=True)

		processed_subscription['product_name'] = None
		processed_subscription['product_name'] = product['name']

		processed_subscription['cost'] = None
		processed_subscription['cost'] = price['cost']

		processed_subscription['quantity'] = None
		processed_subscription['quantity'] = price['quantity']

		processed_subscription['units'] = None
		processed_subscription['units'] = UNITS[product['units_id']]

		processed_subscription['seller_name'] = None
		processed_subscription['seller_name'] = seller['name']

		day_numbers = []
		day_numbers = subscription['days'].split(',')
		days = []
		for day_number in day_numbers:
			days.append(DAYS[int(day_number)])

		processed_subscription['days'] = None
		processed_subscription['days'] = days

		processed_subscription['frequency'] = None
		processed_subscription['frequency'] = FREQUENCY[subscription['frequency']]

		processed_subscription['img_src'] = None
		processed_subscription['img_src'] = product['img_src']

		processed_subscriptions.append(processed_subscription)

	return render_template('subscription_list.html', subscriptions=processed_subscriptions)

@app.route('/add_product_properties')
def add_product_properties():
	if 'user_id' not in session:
		return render_template('abort.html')

	properties = eval(request.args.get('properties'))
	product_id = request.args.get('product_id')

	for product_property in properties:
		db = get_db()
		db.execute("insert into price (product_id, seller_id, quantity, cost) values (?, ?, ?, ?)", [int(product_id), session['user_id'], product_property['qty'], product_property['cost']])
		db.commit()

	return jsonify(result="Working!")

@app.route('/profile')
def get_profile():
	user = None

	if session['is_seller']:
		user = query_db("select * from seller where id = ?", [session['user_id']], one=True)
	else:
		user = query_db("select * from user where id = ?", [session['user_id']], one=True)

	address = query_db("select * from address where user_id = ?", [session['user_id']], one=True)
	return render_template('profile.html', is_seller=session['is_seller'], user=user, address=address)

@app.route('/update_profile')
def update_profile():
	user_address_data = eval(request.args.get('data'))
	db = get_db()

	if (session['is_seller']):
		db.execute("update seller set email = ? and phone = ? where id = ?", [user_address_data['email'], session['user_id']])
	else:
		db.execute("update user set email = ? and first_name = ? and last_name = ? and phone = ? where id = ?", [user_address_data['email'], user_address_data['first_name'], user_address_data['last_name'], session['user_id']])

	db.commit()

	has_address = query_db("select * from address where user_id = ?", [session['user_id']], one=True)

	if has_address:
		db.execute("update address set apt_number = ? and street = ? and city = ? and state = ? and zip = ? where user_id = ?", [user_address_data['apt_number'], user_address_data['street'], user_address_data['city'], user_address_data['state'], user_address_data['zip'], has_address['id'])
	else:
		db.execute("insert into address (apt_number, street, city, state, zip, user_id) values (?, ?, ?, ?, ?, ?)", [user_address_data['apt_number'], user_address_data['street'], user_address_data['city'], user_address_data['state'], user_address_data['zip'], session['user_id']])

	db.commit()
	

@app.route('/logout')
def logout():
	"""Logs the user out."""
	session.pop('user_id', None)
	session.pop('is_seller', None)
	return redirect(url_for('login'))
