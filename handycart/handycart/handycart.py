from __future__ import print_function
from sqlite3 import dbapi2 as sqlite3
from flask import Flask, request, session, url_for, redirect, render_template, jsonify, abort, g, flash, _app_ctx_stack
from werkzeug import check_password_hash, generate_password_hash

import os
import sys

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
	error = None
	if request.method == 'POST':
		user = query_db("select * from user where username = ?", [request.form['username']], one=True)
		if user is None:
			error = 'Invalid username'
		elif not check_password_hash(user['password'], request.form['password']):
			error = 'Invalid password'
		else:
			flash('You were logged in')
			session['user_id'] = user['id']

			if (int(user['is_seller'])):
				session['is_seller'] = True
			else:
				session['is_seller'] = False

			return redirect(url_for('get_products', category_id="3"))
	return render_template('login.html', error=error)

def check_user_exists(username):
	user = query_db("select * from user where username = ?", [username], one=True)

	if user:
		return True
	else:
		return False

@app.route('/register', methods=['GET', 'POST'])
def register():
	error = None
	if request.method == 'POST':
		if not request.form['email'] or '@' not in request.form['email']:
			error = 'You must enter an email'
		elif not request.form['username']:
			error = 'You must enter an username'
		elif not request.form['password']:
			error = 'You have to enter a password'
		elif request.form['password'] != request.form['password2']:
			error = 'Passwords should match'
		elif check_user_exists(request.form['username']):
			error = 'The username is already taken'
		else:
			is_seller = 0

			if request.args.get('is_seller') == '1':
				is_seller = 1

			db = get_db()
			db.execute("insert into user (email, password, username, is_seller) values (?, ?, ?, ?)", [request.form['username'], generate_password_hash(request.form['password']), request.form['username'], is_seller])
			db.commit()
			return redirect(url_for('login'))
	return render_template('register.html', error=error)

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

@app.route('/_add_numbers')
def add_numbers():
	frequency = request.args.get('frequency')
	print (frequency, file=sys.stderr)
	days = request.args.get('days')
	print (days, file=sys.stderr)
	price_id = request.args.get('price_id')
	print (price_id, file=sys.stderr)
	return "Working"

@app.route('/logout')
def logout():
	"""Logs the user out."""
	session.pop('user_id', None)
	return redirect(url_for('login'))
