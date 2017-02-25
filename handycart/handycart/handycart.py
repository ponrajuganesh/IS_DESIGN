from __future__ import print_function
from sqlite3 import dbapi2 as sqlite3
from flask import Flask, request, session, url_for, redirect, render_template, abort, g, flash, _app_ctx_stack

import os
import sys

#configurations
DATABASE = 'data.db'
DEBUG = True
SECRET_KEY = 'development key'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, DATABASE)

app = Flask(__name__)
# app.config.from_object(__name__)
# app.config.from_envvar('HANDYCART_SETTINGS', silent=True)

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

@app.route('/')
def index():
	return redirect(url_for('get_products', category_id="2"))

@app.route('/products')
def get_products():
	products = query_db("select * from product where category_id = ?", [request.args.get('category_id')])
	print ("Full products " + str(len(products)), file=sys.stderr)
	categories = query_db("select * from category")
	print ("CATEGORIES " + str(categories), file=sys.stderr)
	return render_template('products.html', categories=categories, products=products)
