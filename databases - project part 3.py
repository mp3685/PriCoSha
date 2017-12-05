'''
Name: Hassani Junior							NetID: hs2636
Name: Randy Martinez							NetID: rm4078
Name: Matthew Persad							NetID: mp3685

We completed Option 1, Option 4, and Option 6.
We started Option 2, but it is incomplete (it doesn't show comments or tags,
because we haev not implemented that yet.
'''

from flask import Flask, render_template, request, session, url_for, redirect
import pymysql.cursors
from datetime import datetime
import webbrowser
import hashlib

app = Flask(__name__)

conn = pymysql.connect(host='localhost',
                       user='root',
                       password='',
                       db='pricosha',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)
 
@app.route("/")
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
    username = request.form['username']
    password = request.form['password']

    h = hashlib.md5(password.encode('utf-8')).hexdigest()

    cursor = conn.cursor()

    query = 'SELECT * FROM person WHERE username = %s and password = %s'
    cursor.execute(query, (username, h))

    data = cursor.fetchone()

    cursor.close()
    if(data):
        session['username'] = username

        return redirect(url_for('home'))

    else:
        error = 'Invalid login or username'
        return render_template('login.html', error=error)

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
    username = request.form['username']
    password = request.form['password']
    first_name = request.form['first name']
    last_name = request.form['last name']

    h = hashlib.md5(password.encode('utf-8')).hexdigest()

    cursor = conn.cursor()

    query = 'SELECT * FROM person WHERE username = %s'
    cursor.execute(query, (username))

    data = cursor.fetchone()

    if(data):
        error = "This user already exists"
        cursor.close()
        return render_template('register.html', error=error)
    else:
        ins = 'INSERT INTO person VALUES(%s, %s, %s, %s)'
        cursor.execute(ins, (username, h, first_name, last_name))

        conn.commit()
        cursor.close()
        return render_template('index.html')

@app.route('/post')
def post():
    return render_template('create_new_content.html')

@app.route('/create_new_content')
def create_new_content():
    '''cursor = conn.cursor()
    query = 'TRUNCATE TABLE content'
    cursor.execute(query)
    conn.commit()
    cursor.close()'''
    return render_template('create_new_content.html')

@app.route('/create_new_content_AUTH', methods=['GET', 'POST'])
def create_new_content_AUTH():
    username = session['username']
    cursor = conn.cursor()
    file_path = request.form['file_path']
    content_name = request.form['content_name']
    public = request.form['public']

    session['content_name'] = content_name
    
    query = 'INSERT INTO content (username, timest, file_path, content_name, public) VALUES (%s, %s, %s, %s, %s)'
    cursor.execute(query, (username, datetime.now(), file_path, content_name, public))
    conn.commit()
    cursor.close()
    
    cursor.close()
    if (int(public)==0):
        username = session['username']
        cursor = conn.cursor();
        query = "SELECT * FROM friendgroup WHERE username = %s"
        cursor.execute(query, (username))
        data = cursor.fetchall()
        cursor.close()
        
        return render_template('share_content.html', name=content_name, fg=data)
    else:
        return redirect(url_for('home'))
    
@app.route('/share_content')
def share_content():
    return render_template('share_content.html')

@app.route('/share_content_AUTH', methods=['GET', 'POST'])
def share_content_AUTH():
    username = session['username']
    cursor = conn.cursor()
    query = "SELECT group_name FROM friendgroup WHERE username = %s"
    cursor.execute(query, (username))
    data = cursor.fetchall()
    cursor.close()
    cursor = conn.cursor()

    query1 = 'SELECT id FROM content WHERE username = %s AND content_name = %s'
    cursor.execute(query1, (username, session['content_name']))
    data1 = cursor.fetchone()
    cursor.close()
    
    for row in data:
        if (request.form.get(row['group_name'])):
            cursor = conn.cursor()
            query = "INSERT INTO share VALUES (%s, %s, %s)"
            cursor.execute(query, (data1['id'], row['group_name'], username))
            conn.commit()
            cursor.close()
    return redirect(url_for('home'))
    #return render_template('temp.html', error=data1['id'])

@app.route('/home')
def home():
    username = session['username']
    cursor = conn.cursor();
    query = "SELECT * FROM content WHERE username = %s OR public='1' OR id IN (SELECT id FROM share WHERE group_name in (SELECT group_name FROM member WHERE username = %s)) ORDER BY timest DESC"
    cursor.execute(query, (username, username))
    data = cursor.fetchall()
    cursor.close()
    return render_template('home.html', username=username, posts=data)

@app.route('/create_fb')
def create_fb():
    return render_template('create_fb.html')

@app.route('/create_fb_AUTH', methods=['GET', 'POST'])
def create_fb_AUTH():
    username = session['username']
    group_name = request.form['group_name']
    description = request.form['description']

    cursor = conn.cursor()

    query = 'SELECT group_name FROM friendgroup WHERE group_name = %s and username = %s'
    cursor.execute(query, (group_name, username))

    data = cursor.fetchone()

    if(data):
        error = "This group already exists"
        cursor.close()
        return render_template('create_fb.html', error=error)
    else:
        ins = 'INSERT INTO friendgroup VALUES(%s, %s, %s)'
        cursor.execute(ins, (group_name, username, description))
        conn.commit()
        ins2 = 'INSERT INTO member VALUES(%s, %s, %s)'
        cursor.execute(ins2, (username, group_name, username))
        
        conn.commit()
        cursor.close()
        return redirect(url_for('home'))

@app.route('/add_member_fb')
def add_member_fb():
    return render_template('add_member_fb.html')

@app.route('/add_member_fb_AUTH', methods=['GET', 'POST'])
def add_member_fb_AUTH():
    username = session['username']
    group_name = request.form['group_name']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    #username = request.form['username']

    cursor1 = conn.cursor()
    count_query = 'SELECT count(username) AS num FROM person WHERE first_name = %s and last_name = %s'
    cursor1.execute(count_query, (first_name, last_name))
    count_data = cursor1.fetchone()
    count_num = count_data['num']

    if(int(count_num) > 1):
        cursor1.close()
        return render_template('add_member_fb_2.html')
    
    query1 = 'SELECT group_name FROM friendgroup WHERE group_name = %s and username = %s'
    query2 = 'SELECT DISTINCT person.username FROM person RIGHT JOIN member ON person.username=member.username WHERE first_name = %s AND last_name = %s'
    cursor1.execute(query1, (group_name, username))
    data1 = cursor1.fetchone()
    cursor1.execute(query2, (first_name, last_name))
    data2 = cursor1.fetchone()
    cursor1.close()
    if (data2):
        error = "This user already belongs to a FriendGroup with that name"
        return render_template('add_member_fb.html', error=error)
    elif (data1):
        cursor = conn.cursor()

        query = 'SELECT username FROM member NATURAL JOIN person WHERE username_creator = %s AND group_name = %s AND first_name = %s AND last_name = %s'
        cursor.execute(query, (username, group_name, first_name, last_name))

        data = cursor.fetchone()

        if(data):
            error = "A user with that name already exists in this group"
            cursor.close()
            return render_template('add_member_fb.html', error=error)
        else:

            determine = 'SELECT username FROM person WHERE first_name = %s AND last_name = %s'
            cursor.execute(determine, (first_name, last_name))
            user = cursor.fetchone()

            if(user):
                ins = 'INSERT INTO member VALUES(%s, %s, %s)'
                #determine which username to put in ""
                cursor.execute(ins, (user['username'], group_name, username))

                conn.commit()
                cursor.close()
                #return render_template('temp.html', error=user['username'])
                return redirect(url_for('home'))
            else:
                error = "This user does not exist"
                return render_template('add_member_fb.html', error=error)
        
    else:
        error = "You do not own a FriendGroup with that name"
        return render_template('add_member_fb.html', error=error)

@app.route('/add_member_wb_2')
def add_member_wb_2():
    return render_template('add_member_wb_2.html')

@app.route('/add_member_wb_2_AUTH', methods=['GET', 'POST'])
def add_member_wb_2_AUTH():
    username = session['username']
    group_name = request.form['group_name']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    username_add = request.form['username']

    cursor1 = conn.cursor()    
    query1 = 'SELECT group_name FROM friendgroup WHERE group_name = %s and username = %s'
    query2 = 'SELECT username FROM member WHERE username = %s AND group_name = %s'
    cursor1.execute(query1, (group_name, username))
    data1 = cursor1.fetchone()
    cursor1.execute(query2, (username_add, group_name))
    data2 = cursor1.fetchone()
    cursor1.close()
    if (data2):
        error = "This user already belongs to a FriendGroup with that name"
        return render_template('add_member_fb.html', error=error)
    elif (data1):
        cursor = conn.cursor()

        query = 'SELECT username FROM member WHERE username_creator = %s AND group_name = %s'
        cursor.execute(query, (username, group_name))

        data = cursor.fetchone()

        if(data):
            error = "The user already exists in this group"
            cursor.close()
            return render_template('add_member_fb.html', error=error)
        else:

            determine = 'SELECT username FROM person WHERE first_name = %s AND last_name = %s AND username = %s'
            cursor.execute(determine, (first_name, last_name, username_add))
            user = cursor.fetchone()

            if(user):
                ins = 'INSERT INTO member VALUES(%s, %s, %s)'
                #determine which username to put in ""
                cursor.execute(ins, (username_add, group_name, username))

                conn.commit()
                cursor.close()
                #return render_template('temp.html', error=user['username'])
                return redirect(url_for('home'))
            else:
                error = "This user does not exist"
                return render_template('add_member_fb.html', error=error)
        
    else:
        error = "You do not own a FriendGroup with that name"
        return render_template('add_member_fb.html', error=error)

@app.route('/manage_fb')
def manage_fb():
    username = session['username']
    cursor = conn.cursor();
    query = "SELECT * FROM friendgroup WHERE username = %s"
    cursor.execute(query, (username))
    data = cursor.fetchall()
    cursor.close()
    if(data):
        return render_template('manage_fb.html', groups=data, test=[''])
    else:
        return render_template('manage_fb.html', groups=data, not_true=True)   

@app.route('/logout')
def logout():
    session.pop('username')
    return redirect('/')

app.secret_key = 'some key that you will never guess'

if __name__ == "__main__":
    app.run('127.127.0.1', 5000, debug = True)
