from flask import Flask, request, session, redirect, url_for, render_template, flash, abort, Response
import psycopg2
import psycopg2.extras
import re 
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date
from models import User
 
app = Flask(__name__)
app.secret_key = 'secret'
app.config['SECRET_KEY'] = 'secret'
app.url_map.strict_slashes = False
 
DB_HOST = "localhost"
DB_NAME = "mydb"
DB_USER = "postgres"
DB_PASS = "admin"
 
conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
 
@app.route('/')
def home():
    # Check if user is loggedin
    if 'loggedin' in session:
   
        # User is loggedin show them the home page
        return render_template('home.html', username=session['username'])
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

@app.route('/login/', methods=['GET', 'POST'])
def login():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
   
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email= request.form['email']
        password = request.form['password']
        print(password)
 
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        # Fetch one record and return result
        account = cursor.fetchone()
 
        if account:
            password_rs = account['password']
            print(password_rs)
            # If account exists in users table in the database
            if check_password_hash(password_rs, password):
                # Create session data, we can access this data in other routes
                session['loggedin'] = True
                session['id'] = account['id']
                session['username'] = account['username']
                session['email'] = account['email']
                # Redirect to home page
                return redirect(url_for('home'))
            else:
                # Account doesnt exist or email/password incorrect
                flash('電子郵件或密碼錯誤！')
        else:
            # Account doesnt exist or email/password incorrect
            flash('電子郵件或密碼錯誤！')
 
    return render_template('login.html')
  
@app.route('/register', methods=['GET', 'POST'])
def register():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
 
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        # Create variables for easy access
        # fullname = request.form['fullname']
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        registered_date = date.today()
    
        _hashed_password = generate_password_hash(password)
 
        #Check if account exists using MySQL
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        account = cursor.fetchone()
        print(account)
        # If account exists show error and validation checks
        if account:
            flash('電子郵件帳號已存在!')
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            flash('電子郵件不合規則!')
        elif len(username) >= 30:
            flash('名字過長！')
        elif not username or not password or not email:
            flash('請填好每格資料，感恩!')
        else:
            # Account doesnt exists and the form data is valid, now insert new account into users table
            cursor.execute("INSERT INTO users (username, password, email, registered_date) VALUES (%s,%s,%s,%s)", (username, _hashed_password, email, registered_date))
            conn.commit()
            flash('You have successfully registered!')
    elif request.method == 'POST':
        # Form is empty... (no POST data)
        flash('請填好每格資料，感恩!')
    # Show registration form with message (if any)
    return render_template('register.html')
   
@app.route('/logout')
def logout():
   # Remove session data, this will log the user out
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)
   session.pop('email', None)
   # Redirect to login page
   return redirect(url_for('login'))
  
@app.route('/profile')
def profile(): 
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
   
    # Check if user is loggedin
    if 'loggedin' in session:
        cursor.execute('SELECT * FROM users WHERE id = %s', [session['id']])
        account = cursor.fetchone()
        # Show the profile page with account info
        return render_template('profile.html', account=account)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

@app.route('/api/users', methods=['POST'])
def create_user():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    # If the request is POST, then newbies can create users
    if request.is_json and request.method == 'POST':
        data = request.get_json()
        username = data.get('username', '')
        password = data.get('password', '')
        email = data.get('email', '')
        registered_date = date.today()
        print(username)
        _hashed_password = generate_password_hash(password)
 
        #Check if account exists using MySQL
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        account = cursor.fetchone()
        print(account)
        # If account exists show error and validation checks
        if account:
            return {"result":"電子郵件帳號已存在", \
                "HTTP status":403}
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            return {"result":"電子郵件不合規則!", \
                "HTTP status":403}
        elif len(username) >= 30:
            return {"result":"名字過長!", \
                "HTTP status":403}
        elif username == '' or password == '' or email == '':
            return {"result":"請填好每格資料!key:['username', 'password', 'email']", \
                "HTTP status":403}
        else:
            # Account doesnt exists and the form data is valid, now insert new account into users table
            cursor.execute("INSERT INTO users (username, password, email, registered_date) VALUES (%s,%s,%s,%s)", (username, _hashed_password, email, registered_date))
            conn.commit()
            return {"result":"您已成功創建用戶", \
                "HTTP status":200}
    else:
        return {"result":"Please input the correct JSON format", \
                "HTTP status":403}

@app.route("/api/users", methods=['GET'])
def get_all_users():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    if 'loggedin' in session:
        cursor.execute('SELECT id,username,email,registered_date FROM users')
        data = cursor.fetchall()
        if data:
            return {"result":data, "HTTP status":200}
        return {"result":"no users", "HTTP status":200}
    else:
        abort(Response('HTTP status:404, please login first!'))
        return {"result":"Please login first!", \
                "HTTP status":404}

@app.route("/api/users/<user_id>", methods=['GET'])
def get_the_user(user_id):
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    if 'loggedin' in session:
        cursor.execute('SELECT id,username,email,registered_date FROM users WHERE id = %s', (user_id,))
        data = cursor.fetchone()
        if data:
            return {"result":data, "HTTP status":200}
        return {"result":"This user id does not exist!", "HTTP status":200}
    else:
        abort(Response('HTTP status:404, please login first!'))
        return {"result":"Please login first!", \
                "HTTP status":404}

@app.route("/api/users/<user_id>", methods=['PUT'])
def update_user_data(user_id):
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    if 'loggedin' in session and request.is_json:
        data = request.get_json()
        cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))
        account_updating = cursor.fetchone()

        new_username = data.get('new_username', account_updating[1])
        new_password = data.get('new_password', account_updating[2])
        new_email = data.get('new_email', account_updating[3])

        # If account exists show error and validation checks
        if len(new_username) >= 30:
            return {"result":"名字過長!", \
                "HTTP status":403}
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', new_email):
            return {"result":"電子郵件不合規則!", \
                "HTTP status":403}
        else:
            _hashed_password = generate_password_hash(new_password)
            cursor.execute('UPDATE users SET username = %s, password = %s, email = %s WHERE id = %s', (new_username, _hashed_password, new_email, user_id))
            conn.commit()
            return {"result":"您已成功更新id是 {} 的用戶資料".format(str(user_id)), \
                "HTTP status":200}
        
    else:
        abort(Response('HTTP status:404, please login first!'))
        return {"result":"Please login first!", \
                "HTTP status":404}

@app.route('/api/login/', methods=['POST'])
def api_login():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
   
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and request.is_json:
        data = request.get_json()
        email= data.get('email', '')
        password = data.get('password', '')
        print(password)
 
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        # Fetch one record and return result
        account = cursor.fetchone()
 
        if account:
            
            user = User()
            user.email = email

            password_rs = account['password']
            print(password_rs)
            # If account exists in users table in the database
            if check_password_hash(password_rs, password):
                # Create session data, we can access this data in other routes
                session['loggedin'] = True
                session['id'] = account['id']
                session['username'] = account['username']
                session['email'] = account['email']
                # print jwt in the backend and the token should expire after 2 hours
                session['token'] = user.get_jwt()
                return {"result":"您已成功登入電子郵件{}".format(str(email)),\
                "HTTP status":200}
            else:
                # Account doesnt exist or email/password incorrect
                return {"result":"帳號密碼錯誤，請重新登入", \
                "HTTP status":403}
        else:
            # Account doesnt exist or email/password incorrect
            return {"result":"帳號密碼錯誤，請重新登入", \
                "HTTP status":404}
    else:
        return {"result":"Please input the correct JSON format", \
                "HTTP status":403}

@app.route("/api/users/<user_id>", methods=['DELETE'])
def delete_user_data(user_id):
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    if 'loggedin' in session and request.method == 'DELETE':
        cursor.execute("DELETE FROM users WHERE id = %s;", (user_id,))
        conn.commit()
        print("已刪除id是 {} 的資料".format(user_id))
        return {"result":"已刪除id是 {} 的資料".format(str(user_id)), \
                "HTTP status":200}
    else:
        abort(Response('HTTP status:404, please login first!'))
        return {"result":"Please login first!", \
                "HTTP status":404}



@app.route('/api/logout')
def api_logout():
   # Remove session data, this will log the user out
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)
   session.pop('token', None)
   session.pop('email', None)
   # Redirect to login page
   return {"result":"您已成功登出",\
           "HTTP status":200}

if __name__ == "__main__":
    app.run(debug=True)