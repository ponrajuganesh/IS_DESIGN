from __future__ import print_function
from sqlite3 import dbapi2 as sqlite3
from flask import Flask, request, session, url_for, redirect, render_template, abort, g, flash, _app_ctx_stack

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

CATEGORIES = []

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


@app.before_request
def before_request():
	g.categories = None
	g.categories = query_db('select * from category order by name')

@app.route('/')
def index():
	return redirect(url_for('get_products', category_id="3"))

@app.route('/products')
def get_products():
	selected_category = query_db("select name from category where id = ?", [request.args.get('category_id')], one=True)
	products = query_db("select * from product where category_id = ?", [request.args.get('category_id')])
	print ("Full products " + str(len(products)), file=sys.stderr)
	categories = query_db("select * from category order by name")
	print ("CATEGORIES " + str(categories), file=sys.stderr)
	return render_template('products.html', categories=categories, products=products, category_id=request.args.get('category_id'), category_name=selected_category['name'])

@app.route('/subscribe')
def subscribe_product():
	prices = query_db("select price.*, seller.* from price, seller where price.seller_id = seller.id and product_id = ?", [request.args.get('product_id')])
	product = query_db("select * from product where id = ?", [request.args.get('product_id')], one=True)
	unit = query_db("select name from units where id = ?", [product['units_id']], one=True)
	print ("Full prices " + str(len(prices)), file=sys.stderr)
	print ("Product " + str(product['name']))
	return render_template('subscribe.html', product=product, prices=prices, units_name=unit['name'], category_id=request.args.get('category_id'), category_name=request.args.get('category_name'), categories=g.categories)
