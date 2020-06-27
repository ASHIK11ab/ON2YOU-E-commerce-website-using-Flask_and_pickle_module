import pickle

from flask import Flask, render_template, request, redirect, url_for, flash
from myfunctions import*
from myfunctions import seller, customer
from jinja2.nativetypes import NativeEnvironment

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/seller')  # to redirect to login portal
def seller():
    return render_template('sellerlogin.html', access_granted=True)


@app.route('/sellernew')  # to redirect to register portal
def sellernew():
    return render_template('sellerregister.html', is_new_user=True, password_match=True)


@app.route('/sellerlogin', methods=["POST"])
def sellerlogin():
    username = request.form.get("username")
    password = request.form.get("password")
    access_granted = existingseller(username, password)
    if access_granted:
        return redirect(url_for('recent_product', username=username, register=False))
    else:
        return render_template('sellerlogin.html', access_granted=access_granted)


@app.route('/sellerregister', methods=["POST"])
def sellerregister():
    username = request.form.get("username")
    password = request.form.get("password")
    confirm_password = request.form.get("confirm_password")
    if password != confirm_password:
        password_match = False
        return render_template('sellerregister.html', is_new_user=True, password_match=password_match)
    else:
        password_match = True
        is_new_user = newseller(username, password)
        if is_new_user and password_match:
            return redirect(url_for('recent_product', username=username, register=True))
        else:
            return render_template('sellerregister.html', is_new_user=is_new_user, password_match=password_match)


@app.route('/add_item_render')
def add_item_render():
    username = request.args.get('username')
    return render_template('add_item.html', username=username, is_success=False)


@app.route('/dashboard_seller')
def recent_product():
    username = request.args.get('username')
    register = request.args.get('register')
    recent, count = recentproduct(username)
    return render_template("recent_product.html", username=username, register=register, count=count, recent=recent)


@app.route('/dashboard_seller/add_item', methods=["POST"])
def add_item():
    products = {}
    products["item_name"] = request.form.get('item_name')
    products["category"] = request.form.get('category')
    products["cost"] = request.form.get('cost')
    username = request.args.get('username')
    update_database(products, username)
    return render_template('add_item.html', username=username, is_success=True)


@app.route('/dashboard_seller/all_products')
def all_products():
    products = {}
    username = request.args.get('username')
    products, total = get_all_products(username)
    return render_template('all_products.html', products=products, total=total, username=username)


@app.route('/customer')  # to redirect to login portal
def customer():
    return render_template('customerlogin.html', access_granted=True)


@app.route('/customernew')  # to redirect to register portal
def customernew():
    return render_template('customerregister.html', is_new_user=True, password_match=True)


@app.route('/customerlogin', methods=["POST"])
def customerlogin():
    username = request.form.get("username")
    password = request.form.get("password")
    access_granted = existingcustomer(username, password)
    if access_granted:
        return redirect(url_for('recent_products_customer', message="none", is_message=False, username=username))
    else:
        return render_template('customerlogin.html', access_granted=access_granted)


@app.route('/customerregister', methods=["POST"])
def customerregister():
    username = request.form.get("username")
    password = request.form.get("password")
    confirm_password = request.form.get("confirm_password")
    if password != confirm_password:
        password_match = False
        return render_template('customerregister.html', is_new_user=True, password_match=password_match)
    else:
        password_match = True
        is_new_user = newcustomer(username, password)
        if is_new_user and password_match:
            return redirect(url_for('recent_products_customer', message="none", username=username, is_message=False))
        else:
            return render_template('customerregister.html', is_new_user=is_new_user, password_match=password_match)


@app.route('/dashboard_customer')
def recent_products_customer():
    is_message = request.args.get('is_message')
    message = request.args.get('message')
    username = request.args.get('username')
    results, total = recent_products_find()
    return render_template('recent_products_customer.html', products=results, total=total, username=username, is_message=is_message, message=message)


@app.route('/purchase')
def purchase():
    product = request.args.get('product')
    e = NativeEnvironment()
    t = e.from_string(product)
    product = t.render()
    username = request.args.get('username')
    return render_template('purchase.html', product=product, username=username)


@app.route('/Purchase/Purchase_tentative', methods=["POST"])
def purchase_tentative():
    username = request.args.get('username')
    product = request.args.get('product')
    qty = request.form.get('quantity')
    if qty == "" or qty == '0':
        qty = 1
    e = NativeEnvironment()
    t = e.from_string(product)
    product = t.render()
    product["total_cost"] = int(product["cost"])*int(qty)
    product["quantity"] = qty
    return render_template('purchase_confirmation.html', product=product, username=username)


@app.route('/Purchase/Purchase_Confirmation')
def purchase_confirmation():
    username = request.args.get('username')
    product = request.args.get('product')
    product_cnt = request.args.get('product_cnt')
    cart_cost = request.args.get('cart_cost')
    e = NativeEnvironment()
    t = e.from_string(product)
    product = t.render()
    product["customer_name"] = username
    product["no_of_items_in_cart"] = int(product_cnt)

    if product["no_of_items_in_cart"] > 1:
        product["cart_cost"] = cart_cost

    product["mode"] = request.args.get('mode')
    if product["mode"] == 'cart':
        product["cart_cost"] = request.args.get('cart_cost')
    
    generatebill(product, username)
    return redirect(url_for('recent_products_customer', is_message=True, message="buy", username=username))


@app.route('/My_Bills')
def mybills():
    username = request.args.get('username')
    bills, cnt = getmybill_ids(username)
    return render_template('mybills.html', bills=bills, cnt=cnt, username=username)


@app.route('/My_bills/Current_Bill')
def display_current_bill():
    bill_id = request.args.get('bill_id')
    username = request.args.get('username')
    bill = get_this_bill(bill_id, username)
    return render_template('current_bill.html', bill=bill)


@app.route('/cart_render_portal')
def cart_render_portal():
    product = request.args.get('product')
    e = NativeEnvironment()
    t = e.from_string(product)
    product = t.render()
    username = request.args.get('username')
    return render_template('cart.html', product=product, username=username)


@app.route('/add_to_cart', methods=["POST"])
def add_to_cart():
    username = request.args.get('username')
    product = request.args.get('product')
    qty = request.form.get('quantity')
    if qty == "" or qty == '0':
        qty = 1
    e = NativeEnvironment()
    t = e.from_string(product)
    product = t.render()
    product["customer_name"] = username
    product["total_cost"] = int(product["cost"])*int(qty)
    product["quantity"] = qty
    add_this_product_to_cart(product)
    return redirect(url_for('recent_products_customer', is_message=True, message="cart", username=username))


@app.route('/My_Cart')
def my_cart():
    username = request.args.get('username')
    products, cnt, cart_cost = my_items_in_cart(username)
    return render_template('mycart.html', products=products, cnt=cnt, username=username, cart_cost=cart_cost)

@app.route('/product_search', methods = ['GET', 'POST'])
def product_search():
    username = request.args.get('username')
    if request.method == 'GET':
        return render_template('product_search.html', username = username)
    
    query = request.form.get('query')
    if query != '':
        results, cnt = find_products(query)
    else:
        cnt = 0
        results = {}
    return render_template('search_results.html', results = results, cnt = cnt, query = query, username = username)









