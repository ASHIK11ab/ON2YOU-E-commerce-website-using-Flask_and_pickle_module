import pickle

from flask import Flask, render_template, request, redirect, url_for, flash
from myfunctions import*
from myfunctions import seller, customer
from jinja2.nativetypes import NativeEnvironment

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/seller')  # to render to seller login portal
def seller():
    return render_template('sellerlogin.html', access_granted=True)


@app.route('/sellernew')  # to render to seller register portal
def sellernew():
    return render_template('sellerregister.html', is_new_user=True, password_match=True)

#checking for existing account
@app.route('/sellerlogin', methods=["POST"])
def sellerlogin():
    username = request.form.get("username")
    password = request.form.get("password")
    access_granted = existingseller(username, password)
    if access_granted:
        if username == "admin":
            return redirect(url_for('admin', username = username))
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
        is_new_user = newseller(username, password) #checking whether a username aldready exists.
        if is_new_user and password_match:
            return redirect(url_for('recent_product', username=username, register=True))
        else:
            #to display error message
            return render_template('sellerregister.html', is_new_user=is_new_user, password_match=password_match)

#renders add item portal
@app.route('/add_item_render')
def add_item_render():
    username = request.args.get('username')
    return render_template('add_item.html', username=username, is_success=False)


@app.route('/dashboard_seller')
def recent_product(): 
    username = request.args.get('username')
    register = request.args.get('register')
    recent, count = recentproduct(username) #finds the recent product of this seller
    return render_template("recent_product.html", username=username, register=register, count=count, recent=recent)


@app.route('/dashboard_seller/add_item', methods=["POST"])
def add_item():
    products = {}
    products["item_name"] = request.form.get('item_name')
    products["category"] = request.form.get('category')
    products["cost"] = request.form.get('cost')
    username = request.args.get('username')
    update_database(products, username) #adds product to database
    return render_template('add_item.html', username=username, is_success=True)


@app.route('/dashboard_seller/all_products')
def all_products():
    products = {}
    username = request.args.get('username')
    products, total = get_all_products(username) #gets all products added by this current seller
    return render_template('all_products.html', products=products, total=total, username=username)


@app.route('/customer')  # to render to customer login portal
def customer():
    return render_template('customerlogin.html', access_granted=True)


@app.route('/customernew')  # to render to customer register portal
def customernew():
    return render_template('customerregister.html', is_new_user=True, password_match=True)

# checking for existing customer
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
    if password != confirm_password: # checks the two fields for matching password
        password_match = False
        return render_template('customerregister.html', is_new_user=True, password_match=password_match)
    else:
        password_match = True
        is_new_user = newcustomer(username, password)
        if is_new_user and password_match:
            return redirect(url_for('recent_products_customer', message="none", username=username, is_message=False))
        else: # to display error message
            return render_template('customerregister.html', is_new_user=is_new_user, password_match=password_match)


@app.route('/dashboard_customer')
def recent_products_customer():
    is_message = request.args.get('is_message') #is_message checks whether do we need to display error message
    message = request.args.get('message') # error message
    username = request.args.get('username')
    results, total = recent_products_find()
    return render_template('recent_products_customer.html', products=results, total=total, username=username, is_message=is_message, message=message)


@app.route('/purchase')
def purchase():
    product = request.args.get('product')
    e = NativeEnvironment()
    t = e.from_string(product)
    product = t.render()  # converting the string to native python type (dictionary)
    username = request.args.get('username')
    return render_template('purchase.html', product=product, error = False, username=username)


@app.route('/Purchase/Purchase_tentative', methods=["POST"])
def purchase_tentative():
    username = request.args.get('username')
    product = request.args.get('product')
    qty = request.form.get('quantity')
    if qty == "":
        qty = 1
    if qty == '0':
        return render_template('purchase.html', username = username, product = product, error = True)
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

    if product["no_of_items_in_cart"] > 1: # this condition is used since items checked out from cart are stored as single nested dictionary
        product["cart_cost"] = cart_cost

    product["mode"] = request.args.get('mode')
    if product["mode"] == 'cart':
        product["cart_cost"] = request.args.get('cart_cost')
    
    generatebill(product, username) # generate bill
    return redirect(url_for('recent_products_customer', is_message=True, message="buy", username=username))


@app.route('/My_Bills')
def mybills(): 
    username = request.args.get('username')
    bills, cnt = getmybill_ids(username) # gets all bills of the current customer
    return render_template('mybills.html', bills=bills, cnt=cnt, username=username)


@app.route('/My_bills/Current_Bill')
def display_current_bill():
    bill_id = request.args.get('bill_id')
    username = request.args.get('username')
    bill = get_this_bill(bill_id, username) # gets the current bill with this bill_id
    return render_template('current_bill.html', bill=bill)


@app.route('/cart_render_portal')
def cart_render_portal():
    product = request.args.get('product')
    e = NativeEnvironment()
    t = e.from_string(product)
    product = t.render() # product is product added to cart by the customer
    username = request.args.get('username')
    return render_template('cart.html', product=product, username=username, error = False)


@app.route('/add_to_cart', methods=["POST"])
def add_to_cart(): # getting the quantity of items required and calculating the total cost
    username = request.args.get('username')
    product = request.args.get('product')
    qty = request.form.get('quantity')
    if qty == "":
        qty = 1
    if qty == '0':
        return render_template('cart.html', product=product, username=username, error = True)
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
    products, cnt, cart_cost = my_items_in_cart(username) # gets all the products in cart of this current customer
    return render_template('mycart.html', products=products, cnt=cnt, username=username, cart_cost=cart_cost)

@app.route('/My_Cart/Empty_Cart')
def empty_cart():
    username = request.args.get('username')
    emptycart(username)
    return render_template('mycart.html', cnt=0, username = username)

@app.route('/product_search', methods = ['GET', 'POST'])
def product_search():
    username = request.args.get('username')
    if request.method == 'GET':
        return render_template('product_search.html', username = username)
    
    query = request.form.get('query')
    if query != '':
        results, cnt = find_products(query) # finds matching products for this query
    else:
        cnt = 0
        results = {}
    return render_template('search_results.html', results = results, cnt = cnt, query = query, username = username)

@app.route('/Admin')
def admin():
    username = request.args.get('username')
    s_cnt = allsellers(True) # s_cnt -> total seller count in database
    c_cnt = allcustomers(True) # c_cnt -> total customers count in database
    b_cnt = allbills(True) # b_cnt -> total bill count in database
    p_cnt = allproducts(True) # p_cnt -> total products count in database
    return render_template('admin.html',username = username, s_cnt = s_cnt, c_cnt = c_cnt, b_cnt = b_cnt, p_cnt = p_cnt )

@app.route('/Admin/all_seller')
def all_sellers():
    username = request.args.get('username')
    sellers = allsellers(False) # gets all sellers details
    p_cnt = request.args.get('p_cnt')
    s_cnt = request.args.get('s_cnt')
    c_cnt = request.args.get('c_cnt')
    b_cnt = request.args.get('b_cnt')
    return render_template('allsellers.html', sellers = sellers, s_cnt = s_cnt, c_cnt = c_cnt, b_cnt = b_cnt, p_cnt = p_cnt,  username = username)

@app.route('/Admin/all_customer')
def all_customers():
    username = request.args.get('username')
    customers = allcustomers(False) # gets all customers details
    p_cnt = request.args.get('p_cnt')
    s_cnt = request.args.get('s_cnt')
    c_cnt = request.args.get('c_cnt')
    b_cnt = request.args.get('b_cnt')
    return render_template('allcustomers.html', customers = customers, s_cnt = s_cnt,  c_cnt = c_cnt, b_cnt = b_cnt, p_cnt = p_cnt, username = username)

@app.route('/Admin/all_bills')
def all_bills():
    username = request.args.get('username')
    bill_ids = allbills(False) # gets all bill ids
    p_cnt = request.args.get('p_cnt')
    s_cnt = request.args.get('s_cnt')
    c_cnt = request.args.get('c_cnt')
    b_cnt = request.args.get('b_cnt')
    return render_template('allbills.html', bill_ids = bill_ids, s_cnt = s_cnt, c_cnt = c_cnt, b_cnt = b_cnt, p_cnt = p_cnt, username = username)

@app.route('/Admin/all_products')
def all_products_admin():
    username = request.args.get('username')
    products = allproducts(False) # gets all products details
    p_cnt = request.args.get('p_cnt')
    s_cnt = request.args.get('s_cnt')
    c_cnt = request.args.get('c_cnt')
    b_cnt = request.args.get('b_cnt')
    return render_template('allproducts.html', products = products, s_cnt = s_cnt, c_cnt = c_cnt, b_cnt = b_cnt, p_cnt = p_cnt, username = username)












