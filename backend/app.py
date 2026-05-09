from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_cors import CORS
from datetime import datetime
import os
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Customer, Product, Category, OrderTable, OrderItem, Cart, Review, Wishlist, CartItem, Seller
from urllib.parse import quote_plus
from functools import wraps

app = Flask(__name__, template_folder='../templates', static_folder='../static')
CORS(app)

# Database configuration
DB_USER = os.environ.get('DB_USER', 'root')
DB_PASSWORD = quote_plus(os.environ.get('DB_PASSWORD', 'your_password_here'))  # URL encode the password
DB_HOST = os.environ.get('DB_HOST', '127.0.0.1')
DB_PORT = os.environ.get('DB_PORT', '3306')
DB_NAME = os.environ.get('DB_NAME', 'ecommerce')

app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default-dev-secret-key')  # Secure secret key for session management

# Initialize the database with the app
db.init_app(app)

# Context processor to make current_user available in all templates
@app.context_processor
def inject_user():
    if 'customer_id' in session:
        return {'current_user': Customer.query.get(session['customer_id'])}
    return {'current_user': None}

# Admin authentication decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'customer_id' not in session:
            flash('Please login first', 'warning')
            return redirect(url_for('login'))
        
        customer = Customer.query.get(session['customer_id'])
        if not customer or not customer.is_admin:  # You'll need to add is_admin field to Customer model
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    products = Product.query.all()
    categories = Category.query.all()
    return render_template('home.html', products=products, categories=categories)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        customer = Customer.query.filter_by(Email=email).first()
        
        # Special handling for admin login
        if email == 'admin@example.com' and password == 'admin123':
            session['customer_id'] = customer.CustomerID
            flash('Welcome back, Admin!', 'success')
            return redirect(url_for('home'))
            
        # Regular user login
        if customer and check_password_hash(customer.Password, password):
            session['customer_id'] = customer.CustomerID
            if customer.is_admin:
                flash('Welcome back, Admin!', 'success')
            else:
                flash('Login successful!', 'success')
            return redirect(url_for('home'))
            
        flash('Invalid email or password', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if Customer.query.filter_by(Email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('register'))
        
        new_customer = Customer(
            FirstName=first_name,
            LastName=last_name,
            Email=email,
            Password=generate_password_hash(password)
        )
        
        db.session.add(new_customer)
        db.session.commit()
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/products')
def products():
    # Get filter parameters
    category_id = request.args.get('category', type=int)
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    sort_by = request.args.get('sort', default='name')  # name, price_asc, price_desc
    page = request.args.get('page', 1, type=int)
    per_page = 12  # Products per page
    
    # Start with base query
    query = Product.query
    
    # Apply category filter if specified
    if category_id:
        query = query.filter_by(CategoryID=category_id)
    
    # Apply price range filter if specified
    if min_price is not None:
        query = query.filter(Product.MRP >= min_price)
    if max_price is not None:
        query = query.filter(Product.MRP <= max_price)
    
    # Apply sorting
    if sort_by == 'price_asc':
        query = query.order_by(Product.MRP.asc())
    elif sort_by == 'price_desc':
        query = query.order_by(Product.MRP.desc())
    else:  # default sort by name
        query = query.order_by(Product.ProductName.asc())
    
    # Get paginated results
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    products = pagination.items
    
    # Get all categories for the sidebar
    categories = Category.query.all()
    
    # Get price range for the filter
    price_range = db.session.query(
        db.func.min(Product.MRP).label('min_price'),
        db.func.max(Product.MRP).label('max_price')
    ).first()
    
    return render_template('products.html',
                         products=products,
                         categories=categories,
                         selected_category=category_id,
                         min_price=min_price,
                         max_price=max_price,
                         sort_by=sort_by,
                         pagination=pagination,
                         price_range=price_range)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    reviews = Review.query.filter_by(ProductID=product_id).all()
    # Calculate average rating
    avg_rating = db.session.query(db.func.avg(Review.Ratings)).filter_by(ProductID=product_id).scalar() or 0
    # Check if product is in user's wishlist
    in_wishlist = False
    if 'customer_id' in session:
        wishlist_item = Wishlist.query.filter_by(
            CustomerID=session['customer_id'],
            ProductID=product_id
        ).first()
        in_wishlist = wishlist_item is not None
    return render_template('product_detail.html', product=product, reviews=reviews, avg_rating=avg_rating, in_wishlist=in_wishlist)

@app.route('/add_review/<int:product_id>', methods=['POST'])
def add_review(product_id):
    if 'customer_id' not in session:
        flash('Please login to add a review', 'warning')
        return redirect(url_for('login'))
    
    rating = request.form.get('rating')
    description = request.form.get('description')
    
    if not rating or not description:
        flash('Please provide both rating and description', 'warning')
        return redirect(url_for('product_detail', product_id=product_id))
    
    review = Review(
        CustomerID=session['customer_id'],
        ProductID=product_id,
        Ratings=int(rating),
        Description=description
    )
    
    db.session.add(review)
    db.session.commit()
    
    flash('Review added successfully!', 'success')
    return redirect(url_for('product_detail', product_id=product_id))

@app.route('/wishlist')
def wishlist():
    if 'customer_id' not in session:
        flash('Please login to view your wishlist', 'warning')
        return redirect(url_for('login'))
    
    wishlist_items = Wishlist.query.filter_by(CustomerID=session['customer_id']).all()
    products = [Product.query.get(item.ProductID) for item in wishlist_items]
    return render_template('wishlist.html', products=products)

@app.route('/add_to_wishlist/<int:product_id>', methods=['POST'])
def add_to_wishlist(product_id):
    if 'customer_id' not in session:
        flash('Please login to add items to wishlist', 'warning')
        return redirect(url_for('login'))
    
    # Check if product is already in wishlist
    existing_item = Wishlist.query.filter_by(
        CustomerID=session['customer_id'],
        ProductID=product_id
    ).first()
    
    if existing_item:
        flash('Product is already in your wishlist', 'info')
    else:
        wishlist_item = Wishlist(
            CustomerID=session['customer_id'],
            ProductID=product_id,
            AddedDate=datetime.now().date()
        )
        db.session.add(wishlist_item)
        db.session.commit()
        flash('Product added to wishlist!', 'success')
    
    return redirect(url_for('product_detail', product_id=product_id))

@app.route('/remove_from_wishlist/<int:product_id>', methods=['POST'])
def remove_from_wishlist(product_id):
    if 'customer_id' not in session:
        flash('Please login to manage your wishlist', 'warning')
        return redirect(url_for('login'))
    
    wishlist_item = Wishlist.query.filter_by(
        CustomerID=session['customer_id'],
        ProductID=product_id
    ).first()
    
    if wishlist_item:
        db.session.delete(wishlist_item)
        db.session.commit()
        flash('Product removed from wishlist', 'success')
    
    return redirect(url_for('wishlist'))

@app.route('/cart')
def cart():
    if 'customer_id' not in session:
        flash('Please login to view your cart', 'warning')
        return redirect(url_for('login'))
    
    cart = Cart.query.filter_by(CustomerID=session['customer_id']).first()
    if not cart:
        cart = Cart(CustomerID=session['customer_id'], GrandTotal=0, ItemsTotal=0)
        db.session.add(cart)
        db.session.commit()
    
    # Calculate cart totals
    cart_items = CartItem.query.filter_by(CartID=cart.CartID).all()
    subtotal = sum(item.Quantity * item.Product.MRP for item in cart_items)
    cart.GrandTotal = subtotal
    cart.ItemsTotal = len(cart_items)
    db.session.commit()
    
    return render_template('cart.html', cart=cart, cart_items=cart_items)

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    if 'customer_id' not in session:
        flash('Please login to add items to cart', 'warning')
        return redirect(url_for('login'))
    
    quantity = int(request.form.get('quantity', 1))
    product = Product.query.get_or_404(product_id)
    
    if quantity > product.Stock:
        flash('Requested quantity exceeds available stock', 'error')
        return redirect(url_for('product_detail', product_id=product_id))
    
    cart = Cart.query.filter_by(CustomerID=session['customer_id']).first()
    if not cart:
        cart = Cart(CustomerID=session['customer_id'], GrandTotal=0, ItemsTotal=0)
        db.session.add(cart)
        db.session.commit()
    
    # Check if product is already in cart
    cart_item = CartItem.query.filter_by(CartID=cart.CartID, ProductID=product_id).first()
    if cart_item:
        cart_item.Quantity += quantity
    else:
        cart_item = CartItem(CartID=cart.CartID, ProductID=product_id, Quantity=quantity)
        db.session.add(cart_item)
    
    db.session.commit()
    flash('Product added to cart!', 'success')
    return redirect(url_for('cart'))

@app.route('/update_cart_item/<int:item_id>', methods=['POST'])
def update_cart_item(item_id):
    if 'customer_id' not in session:
        flash('Please login to update cart', 'warning')
        return redirect(url_for('login'))
    
    cart_item = CartItem.query.get_or_404(item_id)
    quantity = int(request.form.get('quantity', 1))
    
    if quantity > cart_item.Product.Stock:
        flash('Requested quantity exceeds available stock', 'error')
        return redirect(url_for('cart'))
    
    cart_item.Quantity = quantity
    db.session.commit()
    flash('Cart updated successfully!', 'success')
    return redirect(url_for('cart'))

@app.route('/remove_from_cart/<int:item_id>', methods=['POST'])
def remove_from_cart(item_id):
    if 'customer_id' not in session:
        flash('Please login to manage cart', 'warning')
        return redirect(url_for('login'))
    
    cart_item = CartItem.query.get_or_404(item_id)
    db.session.delete(cart_item)
    db.session.commit()
    flash('Item removed from cart', 'success')
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'customer_id' not in session:
        flash('Please login to checkout', 'warning')
        return redirect(url_for('login'))
    
    cart = Cart.query.filter_by(CustomerID=session['customer_id']).first()
    if not cart:
        flash('Your cart is empty', 'warning')
        return redirect(url_for('cart'))
    
    cart_items = CartItem.query.filter_by(CartID=cart.CartID).all()
    if not cart_items:
        flash('Your cart is empty', 'warning')
        return redirect(url_for('cart'))
    
    if request.method == 'POST':
        try:
            # Create new order
            order = OrderTable(
                CustomerID=session['customer_id'],
                OrderDate=datetime.now().date(),
                OrderAmount=cart.GrandTotal,
                OrderStatus='Pending'
            )
            db.session.add(order)
            db.session.flush()  # Get the order ID
            
            # Create order items
            for item in cart_items:
                order_item = OrderItem(
                    OrderID=order.OrderID,
                    ProductID=item.ProductID,
                    Quantity=item.Quantity,
                    Item_MRP=item.Product.MRP
                )
                db.session.add(order_item)
                
                # Update product stock
                product = Product.query.get(item.ProductID)
                product.Stock -= item.Quantity
            
            # Clear the cart
            CartItem.query.filter_by(CartID=cart.CartID).delete()
            cart.GrandTotal = 0
            cart.ItemsTotal = 0
            
            db.session.commit()
            flash('Order placed successfully!', 'success')
            return redirect(url_for('order_confirmation'))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while processing your order. Please try again.', 'error')
            return redirect(url_for('checkout'))
    
    return render_template('checkout.html', cart=cart, cart_items=cart_items)

@app.route('/logout')
def logout():
    session.pop('customer_id', None)
    flash('You have been logged out', 'success')
    return redirect(url_for('home'))

@app.route('/admin/add-product', methods=['GET', 'POST'])
@admin_required
def add_product():
    if request.method == 'POST':
        try:
            # Get form data
            product_name = request.form.get('product_name')
            mrp = float(request.form.get('mrp'))
            brand = request.form.get('brand')
            stock = int(request.form.get('stock'))
            seller_id = int(request.form.get('seller_id'))
            category_id = int(request.form.get('category_id'))
            
            # Create new product
            new_product = Product(
                ProductName=product_name,
                MRP=mrp,
                Brand=brand,
                Stock=stock,
                SellerID=seller_id,
                CategoryID=category_id
            )
            
            db.session.add(new_product)
            db.session.commit()
            
            flash('Product added successfully!', 'success')
            return redirect(url_for('products'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding product: {str(e)}', 'error')
    
    # Get all sellers and categories for the form
    sellers = Seller.query.all()
    categories = Category.query.all()
    
    return render_template('admin/add_product.html', sellers=sellers, categories=categories)

@app.route('/admin/delete-product/<int:product_id>', methods=['POST'])
@admin_required
def delete_product(product_id):
    try:
        product = Product.query.get_or_404(product_id)
        
        # Delete related records first
        CartItem.query.filter_by(ProductID=product_id).delete()
        OrderItem.query.filter_by(ProductID=product_id).delete()
        Review.query.filter_by(ProductID=product_id).delete()
        Wishlist.query.filter_by(ProductID=product_id).delete()
        
        # Delete the product
        db.session.delete(product)
        db.session.commit()
        
        flash('Product deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting product: {str(e)}', 'error')
    
    return redirect(url_for('products'))

@app.route('/debug/user')
def debug_user():
    if 'customer_id' in session:
        user = Customer.query.get(session['customer_id'])
        return f"""
        Logged in: Yes
        User ID: {user.CustomerID}
        Email: {user.Email}
        Is Admin: {user.is_admin}
        """
    return "Not logged in"

@app.route('/order_confirmation')
def order_confirmation():
    return render_template('order_confirmation.html')

if __name__ == '__main__':
    app.run(debug=True) 