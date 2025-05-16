from flask import Flask, render_template, redirect, url_for, request, flash, session
from functools import wraps
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secure_secret_key_here'  # Use a secure key in production

# Configure MySQL database connection
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://username:password@localhost/sdckl_library'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Define Models
class Book(db.Model):
    __tablename__ = 'books'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(255), nullable=False)
    year = db.Column(db.Integer, nullable=False)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    role = db.Column(db.String(50), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    transaction_type = db.Column(db.Enum('Borrow', 'Return'), nullable=False)
    transaction_date = db.Column(db.Date, nullable=False)

    user = db.relationship('User', backref=db.backref('transactions', lazy=True))
    book = db.relationship('Book', backref=db.backref('transactions', lazy=True))

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            flash("Please login first", "error")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session['logged_in'] = True
            session['user_id'] = user.id
            flash("Logged in successfully!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid credentials, please try again.", "error")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    book_count = Book.query.count()
    return render_template('dashboard.html', book_count=book_count)

@app.route('/books', methods=['GET', 'POST'])
@login_required
def book_list():
    if request.method == 'POST':
        title = request.form.get('title')
        author = request.form.get('author')
        year = request.form.get('year')
        if not (title and author and year):
            flash('All fields are required!', 'error')
        else:
            try:
                new_book = Book(title=title, author=author, year=int(year))
                db.session.add(new_book)
                db.session.commit()
                flash('Book added successfully!', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Error adding book: {str(e)}', 'error')
    books = Book.query.all()
    return render_template('books.html', books=books)

@app.route('/users', methods=['GET', 'POST'])
@login_required
def manage_users():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        role = request.form.get('role')
        password = request.form.get('password')
        if not (name and email and role and password):
            flash('All user fields are required!', 'error')
        else:
            try:
                new_user = User(name=name, email=email, role=role)
                new_user.set_password(password)
                db.session.add(new_user)
                db.session.commit()
                flash('User added successfully!', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Error adding user: {str(e)}', 'error')
    users = User.query.all()
    return render_template('users.html', users=users)

@app.route('/transactions', methods=['GET', 'POST'])
@login_required
def manage_transactions():
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        book_id = request.form.get('book_id')
        t_type = request.form.get('transaction_type')
        date = request.form.get('date')
        if not (user_id and book_id and t_type and date):
            flash('All transaction fields are required!', 'error')
        else:
            try:
                new_trans = Transaction(user_id=int(user_id), book_id=int(book_id), transaction_type=t_type, transaction_date=date)
                db.session.add(new_trans)
                db.session.commit()
                flash('Transaction recorded successfully!', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Error adding transaction: {str(e)}', 'error')
    transactions = Transaction.query.all()
    users = User.query.all()
    books = Book.query.all()
    return render_template('transactions.html', transactions=transactions, users=users, books=books)

# Error Handling
@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True)
