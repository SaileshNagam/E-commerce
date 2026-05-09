from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Customer(db.Model):
    __tablename__ = 'Customer'
    CustomerID = db.Column(db.Integer, primary_key=True)
    FirstName = db.Column(db.String(50), nullable=False)
    MiddleName = db.Column(db.String(50))
    LastName = db.Column(db.String(50), nullable=False)
    CustomerName = db.Column(db.String(150))
    DateOfBirth = db.Column(db.Date)
    Email = db.Column(db.String(100), unique=True, nullable=False)
    PhoneNo = db.Column(db.String(20), unique=True)
    Age = db.Column(db.Integer)
    Password = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class Address(db.Model):
    __tablename__ = 'Address'
    AddressID = db.Column(db.Integer, primary_key=True)
    CustomerID = db.Column(db.Integer, db.ForeignKey('Customer.CustomerID'))
    StreetName = db.Column(db.String(100))
    Pincode = db.Column(db.String(10))
    DoorNumber = db.Column(db.String(10))
    ApartmentNumber = db.Column(db.String(10))
    City = db.Column(db.String(50))
    State = db.Column(db.String(50))

class Seller(db.Model):
    __tablename__ = 'Seller'
    SellerID = db.Column(db.Integer, primary_key=True)
    CompanyName = db.Column(db.String(100))
    SellerName = db.Column(db.String(100))
    Phone = db.Column(db.String(20))
    TotalSales = db.Column(db.Integer)

class Category(db.Model):
    __tablename__ = 'Category'
    CategoryID = db.Column(db.Integer, primary_key=True)
    CategoryName = db.Column(db.String(100))
    Description = db.Column(db.Text)

class Product(db.Model):
    __tablename__ = 'Product'
    ProductID = db.Column(db.Integer, primary_key=True)
    ProductName = db.Column(db.String(100))
    MRP = db.Column(db.Numeric(10, 2))
    Brand = db.Column(db.String(50))
    Stock = db.Column(db.Integer)
    SellerID = db.Column(db.Integer, db.ForeignKey('Seller.SellerID'))
    CategoryID = db.Column(db.Integer, db.ForeignKey('Category.CategoryID'))

class OrderTable(db.Model):
    __tablename__ = 'OrderTable'
    OrderID = db.Column(db.Integer, primary_key=True)
    CustomerID = db.Column(db.Integer, db.ForeignKey('Customer.CustomerID'))
    ShippingDate = db.Column(db.Date)
    OrderAmount = db.Column(db.Numeric(10, 2))
    OrderDate = db.Column(db.Date)
    OrderStatus = db.Column(db.String(50))

class OrderItem(db.Model):
    __tablename__ = 'OrderItem'
    OrderItemID = db.Column(db.Integer, primary_key=True)
    OrderID = db.Column(db.Integer, db.ForeignKey('OrderTable.OrderID'))
    ProductID = db.Column(db.Integer, db.ForeignKey('Product.ProductID'))
    Quantity = db.Column(db.Integer)
    Item_MRP = db.Column(db.Numeric(10, 2))

class Payment(db.Model):
    __tablename__ = 'Payment'
    PaymentID = db.Column(db.Integer, primary_key=True)
    OrderID = db.Column(db.Integer, db.ForeignKey('OrderTable.OrderID'))
    CustomerID = db.Column(db.Integer, db.ForeignKey('Customer.CustomerID'))
    PaymentMode = db.Column(db.String(50))
    PaymentDate = db.Column(db.Date)
    PaymentAmount = db.Column(db.Numeric(10, 2))

class Review(db.Model):
    __tablename__ = 'Review'
    ReviewID = db.Column(db.Integer, primary_key=True)
    CustomerID = db.Column(db.Integer, db.ForeignKey('Customer.CustomerID'))
    ProductID = db.Column(db.Integer, db.ForeignKey('Product.ProductID'))
    Description = db.Column(db.Text)
    Ratings = db.Column(db.Integer)

class Cart(db.Model):
    __tablename__ = 'Cart'
    CartID = db.Column(db.Integer, primary_key=True)
    CustomerID = db.Column(db.Integer, db.ForeignKey('Customer.CustomerID'))
    GrandTotal = db.Column(db.Numeric(10, 2))
    ItemsTotal = db.Column(db.Integer)

class Wishlist(db.Model):
    __tablename__ = 'Wishlist'
    WishlistID = db.Column(db.Integer, primary_key=True)
    CustomerID = db.Column(db.Integer, db.ForeignKey('Customer.CustomerID'))
    ProductID = db.Column(db.Integer, db.ForeignKey('Product.ProductID'))
    AddedDate = db.Column(db.Date)

class Shipment(db.Model):
    __tablename__ = 'Shipment'
    ShipmentID = db.Column(db.Integer, primary_key=True)
    OrderID = db.Column(db.Integer, db.ForeignKey('OrderTable.OrderID'))
    TrackingNumber = db.Column(db.String(50))
    Carrier = db.Column(db.String(50))
    EstimatedDeliveryDate = db.Column(db.Date)

class Discount(db.Model):
    __tablename__ = 'Discount'
    DiscountID = db.Column(db.Integer, primary_key=True)
    ProductID = db.Column(db.Integer, db.ForeignKey('Product.ProductID'))
    DiscountPercentage = db.Column(db.Numeric(5, 2))
    StartDate = db.Column(db.Date)
    EndDate = db.Column(db.Date)

class ReturnRequest(db.Model):
    __tablename__ = 'ReturnRequest'
    ReturnID = db.Column(db.Integer, primary_key=True)
    OrderID = db.Column(db.Integer, db.ForeignKey('OrderTable.OrderID'))
    ProductID = db.Column(db.Integer, db.ForeignKey('Product.ProductID'))
    Reason = db.Column(db.Text)
    Status = db.Column(db.String(50))

class CartItem(db.Model):
    __tablename__ = 'CartItem'
    CartItemID = db.Column(db.Integer, primary_key=True)
    CartID = db.Column(db.Integer, db.ForeignKey('Cart.CartID'))
    ProductID = db.Column(db.Integer, db.ForeignKey('Product.ProductID'))
    Quantity = db.Column(db.Integer, default=1)
    
    # Relationships
    Product = db.relationship('Product', backref='cart_items')
    Cart = db.relationship('Cart', backref='items') 