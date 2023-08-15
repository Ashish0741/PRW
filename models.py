from app import db
from datetime import datetime

class User(db.Model):
    user_id = db.Column(db.Integer,primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    first_name = db.Column(db.String(50),nullable=False)
    last_name = db.Column(db.String(50),nullable=False)
    mobile_number = db.Column(db.Integer,unique=True, nullable=True)
    email = db.Column(db.String(500),unique=True,nullable=False)
    is_renter = db.Column(db.Boolean,default=False)
    is_rentee = db.Column(db.Boolean,default=False)
    product_fk = db.relationship('Product', backref='products', lazy=True, cascade="all,delete")
    cart_fk = db.relationship('CartItem', backref='cartitem', lazy=True, cascade="all,delete")

    @staticmethod
    def convert_string_to_boolean(value):
        if value == 'true':
            return True

    def __init__(self, username,password,first_name,last_name,mobile_number,email,is_renter, is_rentee):
        self.username = username
        self.password = password
        self.first_name = first_name
        self.last_name = last_name
        self.mobile_number = mobile_number
        self.email = email
        self.is_renter = self.convert_string_to_boolean(is_renter)
        self.is_rentee = self.convert_string_to_boolean(is_rentee)


class Category(db.Model):
    category_id = db.Column(db.Integer,primary_key=True, autoincrement=True)
    category_name = db.Column(db.String(50),unique=True,nullable=False)
    category_fk = db.relationship('Product',backref='category', lazy=True, cascade="all,delete")

    def __repr__(self) -> str:
        return self.category_name

class Product(db.Model):
    product_id = db.Column(db.Integer,primary_key=True, autoincrement=True)
    product_name = db.Column(db.String(50),nullable=False)
    product_price = db.Column(db.Integer,nullable=True)
    product_image = db.Column(db.String(200),nullable=False)
    product_desc = db.Column(db.String(500),nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.category_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    cart_fk = db.relationship('CartItem', backref='product', lazy=True, cascade="all,delete")
    

    def __repr__(self) -> str:
        return self.product_name


class CartItem(db.Model):
    cart_id = db.Column(db.Integer,primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.product_id'), nullable=False) 
    quantity = db.Column(db.Integer, default=1)

order_product_association = db.Table('order_product_association',
    db.Column('order_id', db.Integer, db.ForeignKey('order.order_id'),primary_key=True),
    db.Column('product_id', db.Integer, db.ForeignKey('product.product_id'),primary_key=True)
)   

class Order(db.Model):
    order_id = db.Column(db.Integer,primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    full_name = db.Column(db.String(50),nullable=False)
    email = db.Column(db.String(500),nullable=False)
    mobile_number = db.Column(db.Integer,nullable=False)
    address = db.Column(db.String(1000),nullable=False)
    pincode = db.Column(db.String(50),nullable=False)
    total_rent = db.Column(db.Integer,nullable=False)
    total_deposit = db.Column(db.Integer,nullable=False)
    total_amount = db.Column(db.Integer,nullable=False)
    products = db.relationship('Product', secondary=order_product_association, backref='orders')
    payment = db.relationship('Payment', backref='payment', lazy=True, cascade="all,delete")



class Payment(db.Model):
    payment_id = db.Column(db.Integer,primary_key=True, autoincrement=True)
    razorpay_order_id = db.Column(db.String(50),nullable=False)
    amount = db.Column(db.Integer,nullable=False)
    payment_status = db.Column(db.String(50),nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('order.order_id'), nullable=False)


class Contact(db.Model):
    contact_id = db.Column(db.Integer,primary_key=True, autoincrement=True)
    name = db.Column(db.String(200),nullable=False)
    email = db.Column(db.String(200),nullable=False)
    mobile = db.Column(db.Integer,nullable=False)
    message = db.Column(db.Text,nullable=False)
