from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from data import Articles
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

app = Flask(__name__)

# Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '1256'
app.config['MYSQL_DB'] = 'myflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
# init MYSQL
mysql = MySQL(app)

#Articles = Articles()

#index
@app.route('/home')
def index():
    return render_template('home.html')

#About
@app.route('/about')
def about():
    return render_template('about.html')

# Articles
@app.route('/articles')
def articles():
    # create cursor
    cur = mysql.connection.cursor()

    # get articles
    result = cur.execute("SELECT * FROM articles")

    articles = cur.fetchall()

    if result > 0:
        return render_template('articles.html', articles=articles)
    else:
        msg = 'NO ARTICLES FOUND'
    return render_template('articles.html', msg=msg)
    # close connection
    cur.close()

#single article
@app.route('/article/<string:id>')
def article(id):
    # create cursor
    cur = mysql.connection.cursor()

    # get articles
    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    article = cur.fetchone()

    return render_template('article.html', article=article)

# register form class
class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')

# User Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        #Create Cursor
        cur = mysql.connection.cursor()
        
        # Execute query
        cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))

        # commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('you are now register and can log in', 'success')

        return redirect(url_for('login'))
    return render_template('register.html', form=form)

# USER login
@app.route('/login', methods=['GET', 'POST'])
def login():
     if request.method == 'POST':
          #Get Form Fields
          username = request.form['username']
          password_candidate = request.form['password']

          #Create cursor
          cur = mysql.connection.cursor()

          # Get user by username
          result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

          if result > 0:
              # Get stored hash
              data = cur.fetchone()
              password = data['password']

              #compare password
              if sha256_crypt.verify(password_candidate, password):
                  #Passed
                  session['logged_in'] = True
                  session['username'] = username

                  flash('YOU ARE NOW LOGGED IN', 'success')
                  return redirect(url_for('dashboard'))
              else:
                  error = 'INVALID LOGIN'
              return render_template('login.html', error=error)
            # close connection
              cur.close()
          else:
              error = 'NO USER FOUND'
              return render_template('login.html', error=error)

     return render_template('login.html')            

# check if user is logged in 
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('UNAUTHORISED, PLEASE LOGIN', 'danger')
            return redirect(url_for('login'))
    return wrap
                
# Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('YOU ARE NOW LOGGED OUT', 'success')
    return redirect(url_for('login'))

#dashboard        
@app.route('/dashboard')
@is_logged_in
def dashboard():
    # create cursor
    cur = mysql.connection.cursor()

    # get articles
    result = cur.execute("SELECT * FROM articles")

    articles = cur.fetchall()

    if result > 0:
        return render_template('dashboard.html', articles=articles)
    else:
        msg = 'NO ARTICLES FOUND'
    return render_template('dashboard.html', msg=msg)
    # close connection
    cur.close()

# Article form class
class ArticleForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=20)])
    body = TextAreaField('Body', [validators.Length(min=30)])

# Add Article
@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        # Create Cursor
        cur = mysql.connection.cursor()

        # Execute
        cur.execute("INSERT INTO articles(title, body, author) VALUES(%s, %s, %s)",(title, body, session['username']))

        # commit to DB 
        mysql.connection.commit()

        # close connection
        cur.close()
        
        flash('ARTICLE CREATED', 'success')

        return redirect(url_for('dashboard'))

    return render_template('add_article.html', form=form)
    

# Edit Article
@app.route('/edit_article/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_article(id):
    # create cursor
    cur = mysql.connection.cursor()

    # get article by id 
    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    article = cur.fetchone()
    cur.close()

    # get form
    form = ArticleForm(request.form)

    # populate article from fields
    form.title.data = article['title']
    form.body.data = article['body']


    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']

        # Create Cursor
        cur = mysql.connection.cursor()
        app.logger.info(title)

        # Execute
        cur.execute("UPDATE articles SET title=%s, body=%s WHERE id=%s",(title, body, id))

        # commit to DB 
        mysql.connection.commit()

        # close connection
        cur.close()
        
        flash('ARTICLE UPDATED', 'success')

        return redirect(url_for('dashboard'))

    return render_template('edit_article.html', form=form)

# delete article
@app.route('/delete_article/<string:id>', methods=['POST'])
@is_logged_in
def delete_article(id):
    # create cursor
    cur = mysql.connection.cursor()

    #execute
    cur.execute("DELETE FROM articles WHERE id = %s", [id])

    #commit to DB
    cur.connection.commit()

    #close connection
    cur.close()

    flash('ARTICLE DELETED', 'success')

    return redirect(url_for('dashboard'))

if __name__=='__main__':
    app.secret_key='secret123'
    app.run(debug=True) 