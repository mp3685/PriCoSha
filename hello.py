'''
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
#Start Screen
@app.route("/")
def index():
    return render_template('index.html')

#Part 1 - Login
@app.route('/login')
def login():
    return render_template('login.html')

#Part 1 - Login AUTH
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

#Part 1 - Register
@app.route('/register')
def register():
    return render_template('register.html')

#Part 1 - Register AUTH
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

#Part 4 - Post Content
@app.route('/create_new_content')
def create_new_content():
    '''cursor = conn.cursor()
    query = 'TRUNCATE TABLE content'
    cursor.execute(query)
    conn.commit()
    cursor.close()'''
    return render_template('create_new_content.html')

#Part 4 - Post Content AUTH
@app.route('/create_new_content_AUTH', methods=['GET', 'POST'])
def create_new_content_AUTH():
    username = session['username']
    cursor = conn.cursor()
    file_path = request.form['file_path']
    content_name = request.form['content_name']
    public = request.form['public']

    session['content_name'] = content_name
    time = datetime.now()
    query = 'INSERT INTO content (username, timest, file_path, content_name, public) VALUES (%s, %s, %s, %s, %s)'
    cursor.execute(query, (username, time, file_path, content_name, public))
    conn.commit()

    
    query2 = "SELECT * FROM content WHERE username=%s ORDER BY timest DESC"
    cursor.execute(query2, (username))
    data2 = cursor.fetchone()
    print(data2)
    query1 = "INSERT INTO votes VALUES(%s, %s)"
    cursor.execute(query1, (data2['id'], 0))
    conn.commit()
    
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

#Part 4 - Share AUTH
@app.route('/share_content_AUTH', methods=['GET', 'POST'])
def share_content_AUTH():
    username = session['username']
    cursor = conn.cursor()
    query = "SELECT group_name FROM friendgroup WHERE username = %s"
    cursor.execute(query, (username))
    data = cursor.fetchall()

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

#Part 5 - Tag a Content Item
#Add code to home - Next to Content Items
@app.route('/tag_user_content', methods=['GET', 'POST'])
def tag_user_content():
    cursor = conn.cursor()
    username = session['username']
    query1 = "SELECT id FROM content WHERE username = %s OR public='1' OR id IN (SELECT id FROM share WHERE group_name in (SELECT group_name FROM member WHERE username = %s))"
    cursor.execute(query1, (username, username))
    data1 = cursor.fetchall()
    cursor.close()
    for x in data1:
        if request.args.get(str(x['id']), None) == "Tag":
            session['content_id'] = str(x['id'])
            #print(session['content_id'])
    return render_template('tag_user_content.html')

@app.route('/tag_user_content_AUTH', methods=['GET', 'POST'])
def tag_user_content_AUTH():
    tagger = session['username']
    taggee = request.form['username']
    content_id = session['content_id']
    if tagger==taggee:
        cursor = conn.cursor()
        query1 = "INSERT INTO tag(id, username_tagger, username_taggee, timest, status) VALUES(%s, %s, %s, %s, %s)"
        cursor.execute(query1, (content_id, tagger, taggee, datetime.now(), 1))
        conn.commit()
        cursor.close()
        return redirect(url_for('home'))
    else:
        #Test to see if person even exists
        cursor = conn.cursor()
        query2 = "select count(username) as num from member where username=%s or username=%s GROUP BY group_name, username_creator"
        cursor.execute(query2, (taggee, tagger))
        data1 = cursor.fetchall()
        cursor.close()
        for x in data1:
            if x['num'] == 2:
                #print(content_id, tagger, taggee, datetime.now())
                cursor = conn.cursor()
                query3 = "INSERT INTO tag VALUES(%s, %s, %s, %s, %s)"
                cursor.execute(query3, (content_id, tagger, taggee, datetime.now(), 0))
                conn.commit()
                cursor.close()
                return redirect(url_for('home'))
        error="You and the that user do not have a common Friend Group"
        return render_template('tag_user_content.html', error=error)

#Part 3 - Manage Tags
@app.route('/manage_tags')
def manage_tags():
    username = session['username']
    cursor = conn.cursor();
    query = "SELECT * FROM tag WHERE username_taggee = %s"
    cursor.execute(query, (username))
    data = cursor.fetchall()
    cursor.close()
    if(data):
        return render_template('manage_tags.html', groups=data, test=[''])
    else:
        return render_template('manage_tags.html', groups=data, not_true=True)

@app.route('/manage_tags_AUTH')
def manage_tags_AUTH():
    cursor = conn.cursor()
    username = session['username']
    query1 = "SELECT id FROM tag WHERE username_taggee = %s AND status = 0"
    cursor.execute(query1, (username))
    data1 = cursor.fetchall()
    cursor.close()
    for x in data1:
        temp=str(x['id'])
        if request.args.get((temp+'_accept'), None) == "Accept":
            cursor = conn.cursor()
            query2 = "UPDATE tag SET status=1 WHERE id=%s AND username_taggee=%s"
            cursor.execute(query2, (temp, username))
            conn.commit()
            cursor.close()
            return redirect(url_for('home'))
        elif request.args.get((temp+'_decline'), None) == "Decline":
            cursor = conn.cursor()
            query3 = "DELETE FROM tag WHERE id=%s AND username_taggee=%s"
            cursor.execute(query3, (temp, username))
            conn.commit()
            cursor.close()
            return redirect(url_for('home'))
    return render_template('tag_user_content.html')

#Comments
@app.route('/comment_on_post')
def comment_on_post():
    cursor = conn.cursor()
    username = session['username']
    query1 = "SELECT id FROM content WHERE username = %s OR public='1' OR id IN (SELECT id FROM share WHERE group_name in (SELECT group_name FROM member WHERE username = %s))"
    cursor.execute(query1, (username, username))
    data1 = cursor.fetchall()
    cursor.close()
    for x in data1:
        if request.args.get(str(x['id']), None) == "Comment":
            session['content_id'] = str(x['id'])
    return render_template('comment_on_post.html')

@app.route('/comment_on_post_AUTH', methods=['GET', 'POST'])
def comment_on_post_AUTH():
    username = session['username']
    content_id = session['content_id']
    comment = request.form['comment']

    cursor = conn.cursor()
    query = "INSERT INTO comment VALUES(%s, %s, %s, %s)"
    cursor.execute(query, (content_id, username, datetime.now(), comment))
    conn.commit()
    cursor.close()
    return redirect(url_for('home'))

#Part 2 - More Info on Posted Content (Tags/Comments)
@app.route('/more_info_post')
def more_info_post():
    cursor = conn.cursor()
    username = session['username']
    query1 = "SELECT id FROM content WHERE username = %s OR public='1' OR id IN (SELECT id FROM share WHERE group_name in (SELECT group_name FROM member WHERE username = %s))"
    cursor.execute(query1, (username, username))
    data1 = cursor.fetchall()
    content_id=''
    for x in data1:
        if request.args.get(str(x['id']), None) == "More Info":
            content_id = str(x['id'])
    query = "SELECT * FROM tag LEFT JOIN person ON tag.username_taggee=person.username WHERE status=1 and id=%s and (username_taggee in (SELECT username FROM member where group_name in (select group_name from member where username = %s) and username_creator in (select username_creator from member where username=%s)) AND username_tagger in (SELECT username FROM member where group_name in (select group_name from member where username = %s) and username_creator in (select username_creator from member where username=%s)))"
    cursor.execute(query, (content_id, username, username, username, username))
    data2 = cursor.fetchall()

    query2 = "SELECT * FROM comment WHERE id=%s and username in (SELECT username FROM member where group_name in (select group_name from member where username = %s) and username_creator in (select username_creator from member where username=%s))"
    cursor.execute(query2, (content_id, username, username))
    data3 = cursor.fetchall()
    cursor.close()
    if(data2 and data3):
        return render_template('more_info_post.html', group1=data2, test1=[''], group2=data3, test2=[''])
    elif (data2 and (not data3)):
        return render_template('more_info_post.html', group1=data2, test1=[''], no_comments=True)
    elif ((not data2) and data3):
        return render_template('more_info_post.html', group2=data3, test2=[''], no_tags=True)
    else:
        return render_template('more_info_post.html', group1=data2, not_true=True)

#Home Screen
@app.route('/home')
def home():
    username = session['username']
    cursor = conn.cursor();
    query = "SELECT * FROM content LEFT JOIN votes ON content.id=votes.id WHERE (username in (SELECT username FROM member where group_name in (select group_name from member where username = %s) and username_creator in (select username_creator from member where username=%s))) AND (username = %s OR public='1' OR content.id IN (SELECT id FROM share WHERE group_name in (SELECT group_name FROM member WHERE username = %s))) ORDER BY timest DESC"
    cursor.execute(query, (username, username, username, username))
    data = cursor.fetchall()
    cursor.close()
    return render_template('home.html', username=username, posts=data)

#Create Friend Group
@app.route('/create_fb')
def create_fb():
    return render_template('create_fb.html')

#Create Friend Group
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

#Part 6 - Add Friend
@app.route('/add_member_fb')
def add_member_fb():
    return render_template('add_member_fb.html')

#Part 6 - Add Friend AUTH
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

    #If there is only one person with the inputted name
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
    if (data1):
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

#Part 6 - Add Friend (With Username)
@app.route('/add_member_fb_2')
def add_member_fb_2():
    return render_template('add_member_fb_2.html')

#Part 6 - Add Friend (With Username) AUTH
@app.route('/add_member_fb_2_AUTH', methods=['GET', 'POST'])
def add_member_fb_2_AUTH():
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

#Manage Friend Groups
@app.route('/manage_fb')
def manage_fb():
    username = session['username']
    cursor = conn.cursor()
    query = "SELECT * FROM friendgroup WHERE username = %s"
    cursor.execute(query, (username))
    data = cursor.fetchall()
    cursor.close()
    #to simplify add friend, somehow use: session['group_name'] = group_name
    if(data):
        return render_template('manage_fb.html', groups=data, test=[''])
    else:
        return render_template('manage_fb.html', groups=data, not_true=True)

#Part 7 - #1 - Messaging
@app.route('/messages')
def messages():
    username = session['username']
    cursor = conn.cursor()
    query = "SELECT * FROM message WHERE sender = %s OR receiver = %s ORDER BY timest DESC"
    cursor.execute(query, (username, username))
    data = cursor.fetchall()
    cursor.close()
    return render_template('messages.html',posts = data)

@app.route('/messages_2')
def messages_2():
    return render_template('messages_2.html')

@app.route('/messages_AUTH', methods=['GET', 'POST'])
def messages_AUTH():
    send = session['username']
    receive = request.form['username']
    message = request.form['message']
    cursor = conn.cursor()

    query1 = "SELECT username FROM person WHERE username=%s"
    cursor.execute(query1, (receive))
    data = cursor.fetchone()
    if (data):
        query = "INSERT INTO message(sender, receiver, msg, timest) VALUES(%s, %s, %s, %s)"
        cursor.execute(query, (send, receive, message, datetime.now()))
        conn.commit()
        cursor.close()
        return redirect(url_for('home'))
    else:
        error = "That user does not exist"
        return render_template('messages_2.html', error=error)

@app.route('/forwarding')
def forwarding():
    cursor = conn.cursor()
    username = session['username']
    query1 = "SELECT * FROM message"
    cursor.execute(query1)
    data1 = cursor.fetchall()
    message=''
    for x in data1:
        if request.args.get(str(x['id'])+'_user', None) == "Forward":
            message = str(x['msg'])
    query2 = "SELECT * FROM group_chat"
    cursor.execute(query2)
    data2 = cursor.fetchall()
    for x in data2:
        if request.args.get(str(x['id'])+'_fg', None) == "Forward":
            message = str(x['msg'])
    cursor.close()
    session['forward_msg'] = message
    return render_template('forward.html')

@app.route('/forwarding_user', methods=['GET', 'POST'])
def forwarding_user():
    return render_template('forward_user.html')

@app.route('/forwarding_user_AUTH', methods=['GET', 'POST'])
def forwarding_user_AUTH():
    username = session['username']
    message = session['forward_msg']
    cursor = conn.cursor()
    user = request.form['username']
    query = "SELECT * FROM person WHERE username=%s"
    cursor.execute(query, (user))
    data = cursor.fetchone()
    if (data):
        query1 = "INSERT INTO message(sender, receiver, msg, timest) VALUES(%s, %s, %s, %s)"
        cursor.execute(query1, (username, user, message, datetime.now()))
        conn.commit()
        cursor.close()
        return redirect(url_for('home'))
    else:
        cursor.close()
        error="That user does not exist."
        return render_template('forward_user.html', error=error)

@app.route('/forwarding_fg', methods=['GET', 'POST'])
def forwarding_fg():
    username = session['username']
    cursor = conn.cursor();
    query = "SELECT * FROM friendgroup WHERE username = %s"
    cursor.execute(query, (username))
    data = cursor.fetchall()
    cursor.close()
    return render_template('forward_fg.html', fg=data)

@app.route('/forwarding_fg_AUTH', methods=['GET', 'POST'])
def forwarding_fg_AUTH():
    username = session['username']
    message = session['forward_msg']
    cursor = conn.cursor()
    query = "SELECT * FROM friendgroup WHERE username = %s"
    cursor.execute(query, (username))
    data = cursor.fetchall()
    
    cursor.close()
    for row in data:
        if (request.form.get(row['group_name'])):
            cursor = conn.cursor()
            query = "INSERT INTO group_chat(username, group_name, username_creator, msg, timest) VALUES (%s, %s, %s, %s, %s)"
            query2 = "SELECT * FROM member WHERE username=%s AND group_name=%s"
            cursor.execute(query2, (username, row['group_name']))
            data2 = cursor.fetchone()
            cursor.execute(query, (username, row['group_name'], data2['username_creator'], message, datetime.now()))
            conn.commit()
            cursor.close()
    return redirect(url_for('home'))

@app.route('/vote', methods=['GET', 'POST'])
def vote():
    username = session['username']
    cursor = conn.cursor()
    query = "SELECT * FROM content NATURAL JOIN votes WHERE (username in (SELECT username FROM member where group_name in (select group_name from member where username = %s) and username_creator in (select username_creator from member where username=%s))) AND (username = %s OR public='1' OR id IN (SELECT id FROM share WHERE group_name in (SELECT group_name FROM member WHERE username = %s))) ORDER BY timest DESC"
    cursor.execute(query, (username, username, username, username))
    data = cursor.fetchall()
    vote = ''
    for x in data:
        if request.args.get(str(x['id']), None) == "Upvote":
            vote = str(x['id'])
            query = "UPDATE votes SET pts = pts + 1 WHERE id=%s"
            cursor.execute(query, (vote))
            conn.commit()
        elif request.args.get(str(x['id']), None) == "Downvote":
            vote = str(x['id'])
            query = "UPDATE votes SET pts = pts - 1 WHERE id=%s"
            cursor.execute(query, (vote))
            conn.commit()
    query = "SELECT * FROM content LEFT JOIN votes ON content.id=votes.id WHERE (username in (SELECT username FROM member where group_name in (select group_name from member where username = %s) and username_creator in (select username_creator from member where username=%s))) AND (username = %s OR public='1' OR content.id IN (SELECT id FROM share WHERE group_name in (SELECT group_name FROM member WHERE username = %s))) ORDER BY timest DESC"
    cursor.execute(query, (username, username, username, username))
    data = cursor.fetchall()
    cursor.close()
    return render_template('home.html', username=username, posts=data)

@app.route('/group_chat_home')
def member_of_friend_groups():
    username = session['username']
    cursor = conn.cursor()
    query = "SELECT * FROM member WHERE username=%s"
    cursor.execute(query, (username))
    data = cursor.fetchall()
    cursor.close()
    return render_template('group_chat_home.html', posts=data)

@app.route('/group_chat', methods=['GET', 'POST'])
def group_chat():
    cursor = conn.cursor()
    username = session['username']
    query1 = "SELECT * FROM member WHERE username = %s"
    cursor.execute(query1, (username))
    data1 = cursor.fetchall()
    group_name=''
    for x in data1:
        if request.args.get(str(x['group_name']), None) == "Continue":
            group_name = str(x['group_name'])
            session['group_name'] = group_name
    query2 = "SELECT username_creator FROM member WHERE username = %s AND group_name=%s"
    print("HERE:", username, group_name)
    cursor.execute(query2, (username, group_name))
    data2 = cursor.fetchone()
    print(data2)
    session['friend_group_creator'] = data2['username_creator']
    query3 = "SELECT * FROM group_chat WHERE username = %s AND group_name=%s AND username_creator=%s ORDER BY timest DESC"
    cursor.execute(query3, (username, group_name, session['friend_group_creator']))
    data3 = cursor.fetchall()
    cursor.close()
    return render_template('group_chat.html', name=session['group_name'], text=data3)

@app.route('/group_chat_AUTH', methods=['GET', 'POST'])
def group_chat_AUTH():
    username = session['username']
    group_name = session['group_name']
    username_creator = session['friend_group_creator']
    message = request.form['message']
    cursor = conn.cursor()
    query = "INSERT INTO group_chat (username, group_name, username_creator, msg, timest) VALUES(%s, %s, %s, %s, %s)"
    cursor.execute(query, (username, group_name, username_creator, message, datetime.now()))
    conn.commit()
    query3 = "SELECT * FROM group_chat WHERE username = %s AND group_name=%s AND username_creator=%s ORDER BY timest DESC"
    cursor.execute(query3, (username, group_name, session['friend_group_creator']))
    data3 = cursor.fetchall()
    cursor.close()
    return render_template('group_chat.html', name=session['group_name'], text=data3)

#Part 8 (Part 7 - #5) - Defriend
@app.route('/defriend_user')
def defriend_user():
    cursor = conn.cursor()
    username = session['username']
    query1 = "SELECT * FROM friendgroup WHERE username = %s"
    cursor.execute(query1, (username))
    data1 = cursor.fetchall()
    group_name=''
    for x in data1:
        if request.args.get(str(x['group_name']), None) == "Defriend":
            group_name = str(x['group_name'])
            session['group_name'] = group_name
    query2 = "SELECT * FROM member WHERE username_creator = %s and username != %s and group_name=%s"
    cursor.execute(query2, (username, username, group_name))
    data2=cursor.fetchall()
    cursor.close()
    if (data2):
        return render_template('defriend_user.html', name=group_name, loop=[''], members=data2)
    else:
        error="There are no users in this Friend Group"
        return render_template('defriend_user.html', name=group_name, error=error)


@app.route('/defriend_user_AUTH')
def defriend_user_AUTH():
    cursor = conn.cursor()
    username = session['username']
    group_name = session['group_name']
    query1 = "SELECT * FROM member WHERE username_creator = %s AND group_name=%s"
    cursor.execute(query1, (username, group_name))
    data1 = cursor.fetchall()
    defriended=''
    for x in data1:
        if request.args.get(str(x['username'] + '_defriend'), None) == "Confirm":
            defriended = str(x['username'])
    print(defriended)
    query2 = "DELETE FROM member WHERE username=%s"
    cursor.execute(query2, (defriended))
    conn.commit()
    cursor.close()
    return redirect(url_for('home'))

#Logout
@app.route('/logout')
def logout():
    session.pop('username')
    return redirect('/')

app.secret_key = 'some key that you will never guess'

if __name__ == "__main__":
    app.run('127.127.0.1', 5000, debug = True)
