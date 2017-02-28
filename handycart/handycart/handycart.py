from __future__ import print_function
from sqlite3 import dbapi2 as sqlite3
from flask import Flask, request, session, url_for, redirect, render_template, abort, g, flash, _app_ctx_stack
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
		user = query_db("select * from user where email = ?", [request.form['email']], one=True)
		if user is None:
			error = 'Invalid username'
		elif not check_password_hash(user['password'], request.form['password']):
			error = 'Invalid password'
		else:
			flash('You were logged in')
			session['user_id'] = user['id']
			return redirect(url_for('get_products', category_id="3"))
	return render_template('login.html', error=error)

@app.before_request
def before_request():
	g.categories = None
	g.categories = query_db('select * from category order by name')

@app.route('/')
def index():
	return redirect(url_for('login'))

@app.route('/products')
def get_products():
	selected_category = query_db("select name from category where id = ?", [request.args.get('category_id')], one=True)
	products = query_db("select * from product where category_id = ?", [request.args.get('category_id')])
	categories = query_db("select * from category order by name")
	return render_template('products.html', categories=categories, products=products, category_id=request.args.get('category_id'), category_name=selected_category['name'])

@app.route('/subscribe')
def subscribe_product():
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

@app.route('/add_subscription', methods=['POST'])
def add_subscription():
	print ("COMING HERE", file=sys.stderr)
	frequency, days, price_id = request.form['frequency'], request.form['days'], request.form['price_id']
	print("frequency " + str(frequency), file=sys.stderr)
	print("days " + str(days), file=sys.stderr)
	print("price_id " + str(price_id), file=sys.stderr)
	print("user_id " + str(session["user_id"]), file=sys.stderr)
	db = get_db()
	db.execute("insert into subscription (user_id, price_id, days, frequency) values (?, ?, ?, ?)", [session['user_id'], price_id, days, frequency])
	db.commit()
	return redirect(url_for('get_subscriptions'))

@app.route('/get_subscriptions')
def get_subscriptions():
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
