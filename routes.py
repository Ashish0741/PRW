from app import app,db,mail
from flask import render_template, redirect, url_for, request, flash, session
from models import *
from werkzeug.utils import secure_filename
import bcrypt
import re
import razorpay
from flask_mail import Message

# extensions for product images

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# ========================== Validations =======================================


class Validation:

    def validate_username(self, username):

        # pattern for username check
        pattern = r"^[A-Z][a-zA-Z0-9]{5,10}$"

        return bool(re.match(pattern, username))

    def validate_password(self, password):

        # pattern for password check
        pattern = r"^[a-zA-Z0-9#$@]{8,20}$"

        return bool(re.match(pattern, password))

    def validate_mobile_num(self, mobile_num):

        # pattern for password check
        pattern = r"^[0-9]{10}$"

        return bool(re.match(pattern, mobile_num))

    def validate_email(self, email):

        # pattern for email check
        pattern = r"^[a-zA-Z0-9\.]+@[a-zA-Z0-9]+\.[a-zA-Z]{2,}$"

        return bool(re.match(pattern, email))


# creating object of class Validation
validation = Validation()

# ============================================================================

# get all products of search query

def search_products(query):
    try:
        product_results = Product.query.filter(Product.product_name.ilike(f'%{query}%')).all()

        # filtering category of all search products
        products = []
        categories = []
        for product in product_results:
            products.append(product.product_id)
            categories.append(Category.query.filter_by(category_id = product.category_id).first())
            
        # get all products
        all_products = {}

        # creating dict of category and products as key value pair

        for cat in categories:
            cat_products = Product.query.filter(Product.category_id==cat.category_id, Product.product_id.in_(products)).all()
            all_products[cat.category_name] = cat_products

        return all_products

    except Exception as e:
        flash('Something went wrong. Please try again !','danger')
        return None


# Rentee home Page

@app.route('/')
def index():
    session.permanent = True
    try:
        category = Category.query.all()
        all_products = {}

        # creating dict of category and products as key value pair

        for cat in category:
            cat_products = Product.query.filter_by(category_id=cat.category_id).all()
            all_products[cat.category_name] = cat_products
        
        search = request.args.get('search')
        if search:
            all_products = search_products(search)

        return render_template('index.html', all_products=all_products)
    
    except Exception as e:
        flash('Something went wrong. Please try again !','danger')
        return redirect(url_for('index'))


# Renter home Page

@app.route('/renter')
def renter():
    session.permanent = True
    # check if user is in or not
    if 'username' in session:
        user = User.query.filter_by(username=session['username']).first()
        
        try:
            # if user is renter redirect it to renter home page
            if user.is_renter:
                products = Product.query.filter_by(user_id=user.user_id).all()
                categories = Category.query.all()
                orders = Order.query.all()
                return render_template('renter.html', products=products, categories=categories, orders = orders, user = user)
            else:
                # if user is not renter then redirect it to login page
                flash('Kindly login as renter !!', 'danger')
                return redirect(url_for('login'))
        
        except Exception as e:
            flash('Something went wrong. Please login again!', 'danger')
            return redirect(url_for('login'))

    else:
        # if user not in session redirect it to login page
        flash('Session expired ! Please login again.','danger')
        return redirect(url_for('login'))


# Renter (add category) session

@app.route('/add_category', methods=['GET', 'POST'])
def add_category():
    session.permanent = True
    if request.method == 'POST':
        category_name = request.form.get('category_name')

        try:
            category = Category.query.filter_by(category_name=category_name).first()

            # check if category already exists or not
            if not category:
                category = Category(category_name=category_name)
                db.session.add(category)
                db.session.commit()

                flash(f'Category "{category.category_name}" added successfully !!', 'success')
                return redirect(url_for('renter'))
            else:
                flash(f'{category.category_name} already exists !!', 'danger')
                return redirect(url_for('renter'))

        except Exception as e:
            flash('Something went wrong. Please try to add category again!', 'danger')
            return redirect(url_for('renter'))

    else:
        flash('Session expired ! Please login again.','danger')
        return redirect(url_for('login'))


# image file check

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# image validator


def image_validator(product_image):

    # check if the post request has the file
    if not product_image:
        return False

    # If the user does not select a file, the browser submits an
    # empty file without a filename.
    if product_image.filename == '':
        return False

    # check file format
    if product_image and not allowed_file(product_image.filename):
        return False

    return True


# Renter (add products) session

@app.route('/add_products', methods=['GET', 'POST'])
def add_products():
    session.permanent = True
    if 'username' in session:
        if request.method == 'POST':

            product_name = request.form.get('product_name')
            product_price = request.form.get('product_price')
            product_desc = request.form.get('product_desc')
            product_image = request.files['product_image']
            category_name = request.form.get('category_name')


            try:
                # valid image
                if image_validator(product_image):
                    img_filename = secure_filename(product_image.filename)
                    product_image.save('static/images/products/' + img_filename)
                else:
                    flash(
                        f"Please provide file in {ALLOWED_EXTENSIONS} format.", 'danger')
                    return redirect(url_for('renter'))

                category = Category.query.filter_by(
                    category_name=category_name).first()

                user = User.query.filter_by(username=session['username']).first()

                product = Product(product_name=product_name, product_price=product_price,
                                product_desc=product_desc, product_image=img_filename, category_id=category.category_id, user_id=user.user_id)
                db.session.add(product)
                db.session.commit()

                return redirect(url_for('renter'))
            
            except Exception as e:
                flash('Something went wrong. Please try to add product again!', 'danger')
                return redirect(url_for('renter'))

    else:
        flash('Please login for adding products', 'success')
        return redirect(url_for('login'))


# update existing product

@app.route('/update_product/<int:product_id>', methods=['POST', 'GET'])
def update_product(product_id):
    session.permanent = True
    try:
        # fetching product by id
        product = Product.query.filter_by(product_id=product_id).first()

        if request.method == 'POST':
            product.product_name = request.form.get('product_name')
            product.product_price = request.form.get('product_price')
            product.product_desc = request.form.get('product_desc')
            
            category_id = request.form.get('category_id')
            category = Category.query.get_or_404(category_id)
            product.category_id = category.category_id

            product_image = request.files['product_image']

            # valid image
            if image_validator(product_image):
                img_filename = secure_filename(product_image.filename)
                product_image.save('static/images/products/' + img_filename)
                product.product_image = img_filename
            else:
                flash(
                    f"Please provide file in {ALLOWED_EXTENSIONS} format.", 'danger')
                return redirect(url_for('renter'))

            db.session.commit()
            return redirect('/renter')

        categories = Category.query.all()
        return render_template('update_product.html', product=product, categories=categories)

    except Exception as e:
        flash('Something went wrong. Please try to update again!', 'danger')
        return redirect(url_for('renter'))


# delete product

@app.route('/delete_product/<int:product_id>', methods=['POST', 'GET'])
def delete_product(product_id):
    session.permanent = True
    if 'username' in session:
        try:
            product = Product.query.filter_by(product_id=product_id).first()
            db.session.delete(product)
            db.session.commit()
            return redirect('/renter')
        except Exception as e:
            flash('Something went wrong. Please try to delete again!', 'danger')
            return redirect(url_for('renter'))
    else:
        flash('Session expired ! Please login again.','danger')
        return redirect(url_for('login'))


# Registration session

@app.route('/register', methods=['GET', 'POST'])
def register():
    session.permanent = True
    if request.method == 'POST':

        # get all values of post request
        username = request.form.get('username')

        if not validation.validate_username(username):
            flash(
                'Please fill username in right format (User097) and length should be of 6 or more', 'danger')
            return redirect('register')

        password = request.form.get('password')

        if not validation.validate_password(password):
            flash('Please fill password in right format (Pass@097F)', 'danger')
            return redirect('register')

        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')

        mobile_number = request.form.get('mobile_number')

        if not validation.validate_mobile_num(mobile_number):
            flash('Please enter valid mobile number', 'danger')
            return redirect('register')

        email = request.form.get('email')

        if not validation.validate_email(email):
            flash('Please enter valid email id', 'danger')
            return redirect('register')

        is_renter = request.form.get('is_renter')
        is_rentee = request.form.get('is_rentee')

        if is_renter is None and is_rentee is None:
            flash('Please select one of the option (is_renter or is_rentee)', 'danger')
            return redirect('register')

        # check if username already taken
        if User.query.filter_by(username=username).first():
            flash("Username already exists !", 'danger')
            return redirect(url_for('register'))

        # Encrypt the password using bcrypt
        hashed_password = bcrypt.hashpw(
            password.encode('utf-8'), bcrypt.gensalt())

        try:

            # create new user
            new_user = User(
                username=username,
                password=hashed_password,
                first_name=first_name,
                last_name=last_name,
                mobile_number=mobile_number,
                email=email,
                is_renter=is_renter,
                is_rentee=is_rentee
            )

            # add user to database
            db.session.add(new_user)
            db.session.commit()

            flash('User registered successfully!', 'success')
            return redirect(url_for('login'))

        except Exception as e:
            flash('Something went wrong. Please fill proper details!', 'danger')
            return redirect(url_for('register'))

    return render_template('register.html')


# Login session

@app.route('/login', methods=['GET', 'POST'])
def login():
    session.permanent = True
    if request.method == 'POST':

        # Process the login form data
        username = request.form.get('username')
        password = request.form.get('password')

        try:
            # Retrieve the user from the database
            user = User.query.filter_by(username=username).first()

            if user and bcrypt.checkpw(password.encode('utf-8'), user.password):
                if user.is_renter == True:
                    session['username'] = username
                    flash('Login as renter sucessfully!', 'success')
                    return redirect(url_for('renter'))
                else:
                    session['username'] = username
                    flash('Login as rentee sucessfully!', 'success')
                    return redirect(url_for('index'))

            else:
                flash("Invalid username or password", 'danger')
                return redirect(url_for('login'))

        except Exception as e:
            flash('Something went wrong. Please login again!', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')


# Logout session

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))


# product view page

@app.route('/product_view_page/<int:product_id>')
def product_view_page(product_id):
    session.permanent = True
    try:
        product = Product.query.get_or_404(product_id)
        similar_products = Product.query.filter(
            Product.category_id == product.category_id, Product.product_id != product_id).all()
        return render_template('product_view_page.html', product=product, similar_products=similar_products)
    
    except Exception as e:
        flash('Something went wrong. Try again!', 'danger')
        return redirect(url_for('index'))


# cart page

@app.route('/cart')
def cart():
    session.permanent = True
    if 'username' in session:
        try:
            user = User.query.filter_by(username=session['username']).first()
            cart_items = CartItem.query.filter_by(user_id=user.user_id).all()

            # to get total cart amount
            total_cart_amount = 0
            for item in cart_items:
                total_rent = item.quantity * item.product.product_price
                total_deposit = 2 * item.quantity * item.product.product_price
                total_cart_amount += total_deposit + total_rent
            return render_template('cart.html', cart_items=cart_items, total_cart_amount=total_cart_amount)
        
        except Exception as e:
            flash('Something went wrong !', 'danger')
            return redirect(url_for('index'))

    else:
        flash('Please login to access cart !!', 'danger')
        return redirect(url_for('login'))

# cart item 

@app.context_processor
def cart_item_count():
    session.permanent = True
    if 'username' in session:
        try:
            user = User.query.filter_by(username=session['username']).first()
            cart_items = CartItem.query.filter_by(user_id=user.user_id).all()
            count = len(cart_items)
            return {'cart_item_count': count}

        except Exception as e:
            return {'cart_item_count': 0}
    else:
        return {'cart_item_count': 0}


# add to cart

@app.route('/add_to_cart/<int:product_id>')
def add_to_cart(product_id):
    session.permanent = True
    if 'username' in session:
        try:
            user = User.query.filter_by(username=session['username']).first()

            # Check if the user already has the product in their cart
            cart_item = CartItem.query.filter_by(
                user_id=user.user_id, product_id=product_id).first()

            if cart_item:
                # increment the quantity
                cart_item.quantity += 1
            else:
                # add product to cart
                cart_item = CartItem(user_id=user.user_id, product_id=product_id)

            # save to db
            db.session.add(cart_item)
            db.session.commit()

            return redirect('/cart')
        
        except Exception as e:
            flash('Something went wrong. Try to add to cart again!', 'danger')
            return redirect(url_for('index'))

    else:
        flash('Please login to add product to cart !!', 'danger')
        return redirect(url_for('login'))


#  increment quantity

@app.route('/add_quantity/<int:cart_id>')
def add_quantity(cart_id):
    session.permanent = True
    try:
        # get cart item
        cart_item = CartItem.query.get_or_404(cart_id)

        # update quantity
        cart_item.quantity += 1
        db.session.commit()

        return redirect('/cart')
    
    except Exception as e:
        flash('Please try to add quantity again!', 'danger')
        return redirect(url_for('cart'))


# decrement quantity

@app.route('/sub_quantity/<int:cart_id>')
def sub_quantity(cart_id):
    session.permanent = True
    try:

        # get cart item
        cart_item = CartItem.query.get_or_404(cart_id)

        # if quantity = 1 then delete product from cart
        if cart_item.quantity == 1:
            db.session.delete(cart_item)
            db.session.commit()
        else:
            cart_item.quantity -= 1
            db.session.commit()

        return redirect('/cart')
    
    except Exception as e:
        flash('Please try to decrease quantity again!', 'danger')
        return redirect(url_for('cart'))


# delete cart item

@app.route('/delete_cart_item/<int:cart_id>')
def delete_cart_item(cart_id):
    session.permanent = True
    try:
        cart = CartItem.query.get_or_404(cart_id)
        db.session.delete(cart)
        db.session.commit()
        return redirect('/cart')
    
    except Exception as e:
        flash('Something went wrong. Please try to delete again!', 'danger')
        return redirect(url_for('cart'))


# delete category
@app.route('/delete_category/<int:id>')
def delete_category(id):
    session.permanent = True
    try:
        category = Category.query.filter_by(category_id = id).first()
        db.session.delete(category)
        db.session.commit()
        return redirect('/renter')
    except Exception as e:
        flash("Something went wrong !!","danger")
        return redirect('/renter')


# checkout page

@app.route('/checkout/',methods=['POST','GET'])
def checkout():
    session.permanent = True
    if 'username' in session:
        try:
            user = User.query.filter_by(username = session['username']).first()
            cart = CartItem.query.filter_by(user_id = user.user_id).all()

            # to get total cart amount
            total_cart_amount = 0
            for item in cart:
                total_rent = item.quantity * item.product.product_price
                total_deposit = 2 * item.quantity * item.product.product_price
                total_cart_amount += total_deposit + total_rent

            if request.method == 'POST':
                full_name = request.form.get('full_name')
                email = request.form.get('email')
                mobile_number = request.form.get('mobile_number')
                address = request.form.get('address')
                pincode = request.form.get('pincode')
                total_rent = sum(item.quantity * item.product.product_price for item in cart)
                total_deposit = sum(2 * item.quantity * item.product.product_price for item in cart)
                total_amount = int(request.form.get('total_amount'))
                products = []
                
                for item in cart:
                    products.append(item.product)
                
                order = Order(
                    user_id = user.user_id,
                    full_name = full_name,
                    email = email,
                    mobile_number = mobile_number,
                    address = address,
                    pincode = pincode,
                    total_rent = total_rent,
                    total_deposit = total_deposit,
                    total_amount = total_amount,
                    products = products
                )

                # save order
                db.session.add(order)
                db.session.commit()

                # delete entire cart after order request
                for item in cart:
                    db.session.delete(item)
                db.session.commit()

                return redirect(url_for('payment'))


            return render_template('checkout.html', user = user, total_cart_amount = total_cart_amount, cart = cart)

        except Exception as e:
            flash('Something went wrong. Please try again to place order!', 'danger')
            return redirect(url_for('checkout'))

    else:
        flash('Session expired ! Please login again.','danger')
        return redirect(url_for('login'))


# payment section

@app.route('/payment',methods=['POST','GET'])
def payment():
    session.permanent = True
    if 'username' in session:
        try:
            user = User.query.filter_by(username = session['username']).first()
            order = Order.query.filter_by(user_id = user.user_id).first()

            # creating razorpay client object

            client = razorpay.Client(auth=('rzp_test_UjALlxSGoBRkey', 'HeStkBCqNkdeZ7JQEdCnDuqD'))

            DATA = {
                "amount": (int(order.total_amount) * 100),
                "currency": "INR",
                "payment_capture": "1"
            }

            payment = client.order.create(data=DATA)

            # store in database
            paymentStatus = Payment(
                user_id = user.user_id,
                order_id = order.order_id,
                razorpay_order_id = payment['id'],
                amount = payment['amount'],
                payment_status = payment['status']
            )

            db.session.add(paymentStatus)
            db.session.commit()

            return render_template('payment.html', payment = payment, user = user)

        except Exception as e:
            flash('Something went wrong. Please try again!', 'danger')
            return redirect(url_for('payment'))

    else:
        flash('Session expired ! Please login again.','danger')
        return redirect(url_for('login'))
        

@app.route('/success',methods=['POST','GET'])
def success():
    session.permanent = True
    if 'username' in session:

        try:

            user = User.query.filter_by(username = session['username']).first()
            payment = Payment.query.filter_by(user_id = user.user_id).first()
            payment.payment_status = 'Completed'
            db.session.commit()

            # send mail after payment

            subject = f'Your Order has been placed | Order ID : {payment.razorpay_order_id}'
            recipient = str(user.email)
            sender = app.config['MAIL_USERNAME']
            message_body = f'''
            Hi {user.first_name} {user.last_name},
            
            Your Order has been placed successfully !!
            Order ID : {payment.razorpay_order_id}
            Amount : {payment.amount//100}
            Payment Status : {payment.payment_status}

            Thanks & Regards,
            PRW
            '''

            message = Message(subject=subject, recipients=[recipient], body=message_body, sender = sender)

            mail.send(message)
            flash("Email sent successfully!",'success')
            return render_template('success.html', payment = payment)

        except Exception as e:
            flash("Something went wrong!",'danger')
            return redirect(url_for('success'))

    else:
        flash('Session expired ! Please login again.','danger')
        return redirect(url_for('login'))


# admin section

@app.route('/admin_panel')
def admin_panel():
    users = User.query.all()
    return render_template('admin_panel.html', users = users)


# delete user

@app.route('/delete_user/<int:id>')
def delete_user(id):
    session.permanent = True
    try:
        user = User.query.filter_by(user_id = id).first()
        db.session.delete(user)
        db.session.commit()
        return redirect('/admin_panel')
    except Exception as e:
        flash("Something went wrong !!","danger")
        return redirect('/admin_panel')


# testing code

@app.route('/delete_all')
def delete_all():
    Payment.query.delete()
    Order.query.delete() 
    db.session.query(order_product_association).filter_by(order_id=2).delete()
    db.session.commit()
    return redirect(url_for('login'))


# order section

@app.route('/order', methods=['POST','GET'])
def order():
    session.permanent = True
    if 'username' in session:
        try:
            user = User.query.filter_by(username = session['username']).first()
            if request.method == 'POST':
                razorpay_order_id = request.form.get('razorpay_order_id')
                payment = Payment.query.filter_by(razorpay_order_id = razorpay_order_id).first()
                order = Order.query.filter_by(order_id = payment.order_id).first()
                return render_template('order.html', order = order, payment = payment, user = user)

            return render_template('order.html', payment = None)
        
        except Exception as e:
            flash('Something went wrong. Please try again!', 'danger')
            return redirect(url_for('order'))

    else:
        flash('Session expired ! Please login again.','danger')
        return redirect(url_for('login'))


# about section
@app.route('/about')
def about():
    return render_template('about.html')


# contact section
@app.route('/contact', methods=['POST','GET'])
def contact():
    session.permanent = True
    if 'username' in session:
        if request.method == 'POST':
            name = request.form.get('name')
            email = request.form.get('email')
            mobile = request.form.get('mobile')
            message = request.form.get('message')

            try:
                contact = Contact(
                    name = name,
                    email = email,
                    mobile = mobile,
                    message = message
                )

                db.session.add(contact)
                db.session.commit()

                flash('Form has been submitted successfully!!','success')
                return redirect(url_for('contact'))
            
            except Exception as e:
                flash('Form not submitted. Please try again !','danger')
                return redirect(url_for('contact'))
        else:
            return render_template('contact.html')
    else:
        flash('Session expired ! Please login again.','danger')
        return redirect(url_for('login'))