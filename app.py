import os
from flask import Flask, render_template, redirect, url_for, request, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

import sqlite3

app = Flask(__name__, static_folder='static')
app.secret_key = 'your_secret_key'

UPLOAD_FOLDER = 'static/uploads/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Database setup
def init_sqlite_db():
    conn = sqlite3.connect('auth.db')
    print("Opened database successfully")
    
     # Create users table
    conn.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, email TEXT, password TEXT, balance REAL DEFAULT 0, address TEXT, phone_number TEXT)')
     # Create books table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            author TEXT,
            title TEXT,
            price REAL,
            image_url TEXT
        )
    ''')
     # Create admins table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            email TEXT,
            password TEXT
        )
    ''')

# Create wishlist table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS wishlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            book_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (book_id) REFERENCES books(id)
        )
    ''')

    # Create purchases table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            book_id INTEGER,
            purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (book_id) REFERENCES books(id)
        )
    ''')
    print('admin created')
    print('book table ctrated Successfully')
    print("Table created successfully")
    conn.close()

def add_image_url_column():
    with sqlite3.connect('auth.db') as con:
        cur = con.cursor()
        try:
            cur.execute("ALTER TABLE books ADD COLUMN image_url TEXT")
            con.commit()
            print("Column 'image_url' added successfully")
        except sqlite3.OperationalError as e:
            print(f"Error: {e}")
    con.close()

add_image_url_column()

def add_balance_column():
    with sqlite3.connect('auth.db') as con:
        cur = con.cursor()
        try:
            cur.execute("ALTER TABLE users ADD COLUMN balance REAL DEFAULT 0")
            con.commit()
            print("Column 'balance' added successfully")
        except sqlite3.OperationalError as e:
            print(f"Error: {e}")
    con.close()

add_balance_column()

def update_user_table():
    with sqlite3.connect('auth.db') as con:
        cur = con.cursor()
        try:
            cur.execute("ALTER TABLE users ADD COLUMN address TEXT")
            cur.execute("ALTER TABLE users ADD COLUMN phone_number TEXT")
            con.commit()
            print("Columns 'address' and 'phone_number' added successfully")
        except sqlite3.OperationalError as e:
            print(f"Error: {e}")

update_user_table()


init_sqlite_db()



# Index route
@app.route('/')
def index():
    # if 'username' in session:
    #     username = session['username']
    #     return f'Hello, {username}! <br><a href="/logout/">Logout</a>'
    # return 'You are not logged in. <br><a href="/login/">Login</a> <br><a href="/register/">Register</a>' 
    username = session.get('username')
    with sqlite3.connect('auth.db') as con:
        cur = con.cursor()
        cur.execute("SELECT id, author, title, price, image_url FROM books")
        books = cur.fetchall()
    return render_template('landingpage.html',books=books,username=username)

    
############################################################################################################################################
# Register route
@app.route('/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']
            address = request.form['address']
            phone_number = request.form['phone_number']
            hashed_password = generate_password_hash(password)

            with sqlite3.connect('auth.db') as con:
                cur = con.cursor()
                cur.execute("INSERT INTO users (username, email, password, address, phone_number) VALUES (?, ?, ?, ?, ?)",
                            (username, email, hashed_password, address, phone_number))
                con.commit()
                flash('User registered successfully', 'success')
        except Exception as e:
            con.rollback()
            print(f"Error: {e}")
            flash('Error occurred in registration', 'danger')
        finally:
            con.close()
            return redirect(url_for('login'))

    return render_template('register.html')

# Login route
@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        with sqlite3.connect('auth.db') as con:
            cur = con.cursor()
            cur.execute("SELECT * FROM users WHERE email = ?", (email,))
            user = cur.fetchone()

            if user:
                stored_password = user[3]
                print(f"Stored password: {stored_password}")
                print(f"Password provided: {password}")
                if check_password_hash(stored_password, password):
                    session['user_id'] = user[0]
                    session['username'] = user[1]
                    flash('Login successful', 'success')
                    return redirect(url_for('index'))
                    # return render_template('index.html')
                else:
                    flash('Invalid credentials', 'danger')
            else:
                flash('User not found', 'danger')

    return render_template('login.html')

# Logout route
@app.route('/logout/')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('You have successfully logged out', 'success')
    return redirect(url_for('index'))

@app.route('/update_profile/', methods=['GET', 'POST'])
def update_profile():
    if 'user_id' not in session:
        flash('Please log in first', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        address = request.form['address']
        phone_number = request.form['phone_number']

        with sqlite3.connect('auth.db') as con:
            cur = con.cursor()
            cur.execute("UPDATE users SET address = ?, phone_number = ? WHERE id = ?", (address, phone_number, session['user_id']))
            con.commit()
            flash('Profile updated successfully', 'success')
        return redirect(url_for('user_dashboard'))

    # Fetch the current user details
    with sqlite3.connect('auth.db') as con:
        cur = con.cursor()
        cur.execute("SELECT address, phone_number FROM users WHERE id = ?", (session['user_id'],))
        user_details = cur.fetchone()

    return render_template('update_profile.html', user_details=user_details)

################################################################################################################################################

################################################################################################################################################
@app.route('/admin_register/', methods=['GET', 'POST'])
def admin_register():
    if request.method == 'POST':
        try:
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']
            hashed_password = generate_password_hash(password)

            with sqlite3.connect('auth.db') as con:
                cur = con.cursor()
                cur.execute("INSERT INTO admins (username, email, password) VALUES (?, ?, ?)", (username, email, hashed_password))
                con.commit()
                flash('Admin registered successfully', 'success')
        except Exception as e:
            con.rollback()
            print(f"Error: {e}")
            flash('Error occurred in registration', 'danger')
        finally:
            con.close()
            return redirect(url_for('admin_login'))

    return render_template('admin_register.html')

@app.route('/admin_login/', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        with sqlite3.connect('auth.db') as con:
            cur = con.cursor()
            cur.execute("SELECT * FROM admins WHERE email = ?", (email,))
            admin = cur.fetchone()

            if admin:
                stored_password = admin[3]
                if check_password_hash(stored_password, password):
                    session['admin_id'] = admin[0]
                    session['admin_username'] = admin[1]
                    flash('Login successful', 'success')
                    return redirect(url_for('admin_dashboard'))
                else:
                    flash('Invalid credentials', 'danger')
            else:
                flash('Admin not found', 'danger')

    return render_template('admin_login.html')

@app.route('/admin_dashboard/')
def admin_dashboard():
    if 'admin_id' not in session:
        flash('Please log in as admin first', 'danger')
        return redirect(url_for('admin_login'))
    
    # Fetch books from the database
    with sqlite3.connect('auth.db') as con:
        cur = con.cursor()
        cur.execute("SELECT id, author, title, price, image_url FROM books")
        books = cur.fetchall()

          # Debug: Print book image URLs
    for book in books:
        print(f"Book Image URL: {url_for('static', filename='uploads/' + book[4])}")


    return render_template('admin_dashboard.html', books=books)

@app.route('/add_book/', methods=['GET', 'POST'])
def add_book():
    if 'admin_id' not in session:
        flash('Please log in as admin first', 'danger')
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        author = request.form['author']
        title = request.form['title']
        price = request.form['price']
        image = request.files.get('image')

        filename = None
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(file_path)
            print(f"Image saved to: {file_path}")
        
        with sqlite3.connect('auth.db') as con:
            cur = con.cursor()
            cur.execute("INSERT INTO books (author, title, price, image_url) VALUES (?, ?, ?, ?)", (author, title, price, filename))
            con.commit()
            flash('Book added successfully', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('add_book.html')



@app.route('/edit_book/<int:book_id>/', methods=['GET', 'POST'])
def edit_book(book_id):
    if 'admin_id' not in session:
        flash('Please log in as admin first', 'danger')
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        author = request.form['author']
        title = request.form['title']
        price = request.form['price']
        image = request.files.get('image')

        filename = None
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(file_path)
            print(f"Image saved to: {file_path}")

        with sqlite3.connect('auth.db') as con:
            cur = con.cursor()
            if filename:
                # Update book with new image URL
                cur.execute("UPDATE books SET author = ?, title = ?, price = ?, image_url = ? WHERE id = ?",
                            (author, title, price, filename, book_id))
            else:
                # Update book without changing image
                cur.execute("UPDATE books SET author = ?, title = ?, price = ? WHERE id = ?",
                            (author, title, price, book_id))
            con.commit()
            flash('Book updated successfully', 'success')
        return redirect(url_for('admin_dashboard'))
    
    # Fetch the current details of the book
    with sqlite3.connect('auth.db') as con:
        cur = con.cursor()
        cur.execute("SELECT author, title, price, image_url FROM books WHERE id = ?", (book_id,))
        book = cur.fetchone()

    if book:
        return render_template('edit_book.html', book=book)
    else:
        flash('Book not found', 'danger')
        return redirect(url_for('admin_dashboard'))



@app.route('/delete_book/<int:book_id>/')
def delete_book(book_id):
    if 'admin_id' not in session:
        flash('Please log in as admin first', 'danger')
        return redirect(url_for('admin_login'))

    with sqlite3.connect('auth.db') as con:
        cur = con.cursor()
        cur.execute("DELETE FROM books WHERE id = ?", (book_id,))
        con.commit()
        flash('Book deleted successfully', 'success')

    return redirect(url_for('admin_dashboard'))
################################################################################################################################################

################################################################################################################################################

@app.route('/add_money/', methods=['GET', 'POST'])
def add_money():
    if 'user_id' not in session:
        flash('Please log in first', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        amount = float(request.form['amount'])

        with sqlite3.connect('auth.db') as con:
            cur = con.cursor()
            cur.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (amount, session['user_id']))
            con.commit()
            flash(f'Added ${amount} to your account', 'success')
        return redirect(url_for('user_dashboard'))
    
    return render_template('add_money.html')

@app.route('/check_balance/')
def check_balance():
    if 'user_id' not in session:
        flash('Please log in first', 'danger')
        return redirect(url_for('login'))

    with sqlite3.connect('auth.db') as con:
        cur = con.cursor()
        cur.execute("SELECT balance FROM users WHERE id = ?", (session['user_id'],))
        balance = cur.fetchone()[0]

    return render_template('check_balance.html', balance=balance)

@app.route('/withdraw_money/', methods=['GET', 'POST'])
def withdraw_money():
    if 'user_id' not in session:
        flash('Please log in first', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        amount = float(request.form['amount'])

        with sqlite3.connect('auth.db') as con:
            cur = con.cursor()
            cur.execute("SELECT balance FROM users WHERE id = ?", (session['user_id'],))
            balance = cur.fetchone()[0]

            if balance >= amount:
                cur.execute("UPDATE users SET balance = balance - ? WHERE id = ?", (amount, session['user_id']))
                con.commit()
                flash(f'Withdrew ${amount} from your account', 'success')
            else:
                flash('Insufficient balance', 'danger')
        return redirect(url_for('user_dashboard'))
    
    return render_template('withdraw_money.html')

@app.route('/user_dashboard/')
def user_dashboard():
    if 'user_id' not in session:
        flash('Please log in first', 'danger')
        return redirect(url_for('login'))

    with sqlite3.connect('auth.db') as con:
        cur = con.cursor()
        cur.execute("SELECT username, email, address, phone_number, balance FROM users WHERE id = ?", (session['user_id'],))
        user_data = cur.fetchone()
    
    if user_data:
        username, email, address, phone_number, balance = user_data
    else:
        flash('User data not found', 'danger')
        return redirect(url_for('login'))

    return render_template('user_dashboard.html', username=username, email=email, address=address, phone_number=phone_number, balance=balance)



# Add to wishlist route
@app.route('/add_to_wishlist/<int:book_id>/')
def add_to_wishlist(book_id):
    if 'user_id' not in session:
        flash('Please log in first', 'danger')
        return redirect(url_for('login'))

    with sqlite3.connect('auth.db') as con:
        cur = con.cursor()
        cur.execute("INSERT INTO wishlist (user_id, book_id) VALUES (?, ?)", (session['user_id'], book_id))
        con.commit()
        flash('Book added to wishlist', 'success')
    return redirect(url_for('view_wishlist'))

@app.route('/buy_now/<int:book_id>/', methods=['GET', 'POST'])
def buy_now(book_id):
    if 'user_id' not in session:
        flash('Please log in first', 'danger')
        return redirect(url_for('login'))

    with sqlite3.connect('auth.db') as con:
        cur = con.cursor()
        
        # Fetch book details
        cur.execute("SELECT id, author, title, price, image_url FROM books WHERE id = ?", (book_id,))
        book = cur.fetchone()
        if not book:
            flash('Book not found', 'danger')
            return redirect(url_for('index'))
        
        book_details = {
            'id': book[0],
            'author': book[1],
            'title': book[2],
            'price': book[3],
            'image_url': book[4]
        }

        # Fetch user balance
        cur.execute("SELECT balance FROM users WHERE id = ?", (session['user_id'],))
        balance = cur.fetchone()[0]

        if request.method == 'POST':
            # Handle the purchase logic here
            if balance >= book_details['price']:
                new_balance = balance - book_details['price']
                cur.execute("UPDATE users SET balance = ? WHERE id = ?", (new_balance, session['user_id']))
                
                 # Record the purchase
                cur.execute("INSERT INTO purchases (user_id, book_id) VALUES (?, ?)", (session['user_id'], book_id))
                
                con.commit()
                flash('Book purchased successfully', 'success')
                return redirect(url_for('purchase', book_id=book_id))
            else:
                flash('Insufficient balance', 'danger')

    return render_template('buy_now.html', book=book_details, balance=balance)


@app.route('/purchase/<int:book_id>/')
def purchase(book_id):
    if 'user_id' not in session:
        flash('Please log in first', 'danger')
        return redirect(url_for('login'))

    with sqlite3.connect('auth.db') as con:
        cur = con.cursor()
        
        # Fetch book details
        cur.execute("SELECT id, author, title, price, image_url FROM books WHERE id = ?", (book_id,))
        book = cur.fetchone()
        if not book:
            flash('Book not found', 'danger')
            return redirect(url_for('index'))
        
        book_details = {
            'id': book[0],
            'author': book[1],
            'title': book[2],
            'price': book[3],
            'image_url': book[4]
        }

        # Fetch updated user balance, address, and phone number
        cur.execute("SELECT balance, address, phone_number FROM users WHERE id = ?", (session['user_id'],))
        user_data = cur.fetchone()
        if not user_data:
            flash('User data not found', 'danger')
            return redirect(url_for('login'))
        
        balance, address, phone_number = user_data

    return render_template('purchase.html', book=book_details, balance=balance, address=address, phone_number=phone_number)


@app.route('/my_purchases/')
def my_purchases():
    if 'user_id' not in session:
        flash('Please log in first', 'danger')
        return redirect(url_for('login'))

    with sqlite3.connect('auth.db') as con:
        cur = con.cursor()
        
        # Fetch purchased books
        cur.execute('''
            SELECT b.id, b.author, b.title, b.price, b.image_url, p.purchase_date
            FROM purchases p
            JOIN books b ON p.book_id = b.id
            WHERE p.user_id = ?
            ORDER BY p.purchase_date DESC
        ''', (session['user_id'],))
        purchases = cur.fetchall()

    return render_template('my_purchases.html', purchases=purchases)


# View wishlist route
@app.route('/wishlist/')
def view_wishlist():
    if 'user_id' not in session:
        flash('Please log in first', 'danger')
        return redirect(url_for('login'))

    with sqlite3.connect('auth.db') as con:
        cur = con.cursor()
        cur.execute('''
            SELECT books.id, books.author, books.title, books.price, books.image_url
            FROM books
            JOIN wishlist ON books.id = wishlist.book_id
            WHERE wishlist.user_id = ?
        ''', (session['user_id'],))
        wishlist_books = cur.fetchall()

    return render_template('wishlist.html', books=wishlist_books)




if __name__ == '__main__':
    app.run(debug=True)
