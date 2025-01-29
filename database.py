# database.py

import sqlite3
from contextlib import closing
from datetime import datetime

DB_NAME = 'voting_app.db'

def create_connection():
    conn = sqlite3.connect(DB_NAME)
    return conn

def init_db():
    """Initialize the database and create tables if they don't exist."""
    with closing(create_connection()) as conn:
        cursor = conn.cursor()

        # Create Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('admin', 'group_admin', 'user'))
            )
        ''')

        # Create Groups table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Groups (
                group_id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_name TEXT NOT NULL UNIQUE,
                admin_user_id INTEGER NOT NULL,
                FOREIGN KEY (admin_user_id) REFERENCES Users(user_id) ON DELETE CASCADE
            )
        ''')

        # Create GroupMembers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS GroupMembers (
                member_id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('pending', 'accepted', 'rejected')),
                FOREIGN KEY (group_id) REFERENCES Groups(group_id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
            )
        ''')

        # Create Polls table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Polls (
                poll_id INTEGER PRIMARY KEY AUTOINCREMENT,
                poll_question TEXT NOT NULL,
                is_public BOOLEAN NOT NULL CHECK(is_public IN (0,1)),
                creator_id INTEGER NOT NULL,
                group_id INTEGER,
                start_time text NOT NULL,
                end_time text NOT NULL,
                FOREIGN KEY (creator_id) REFERENCES Users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (group_id) REFERENCES Groups(group_id) ON DELETE CASCADE
            )
        ''')

        # Create Options table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Options (
                option_id INTEGER PRIMARY KEY AUTOINCREMENT,
                poll_id INTEGER NOT NULL,
                option_text TEXT NOT NULL,
                FOREIGN KEY (poll_id) REFERENCES Polls(poll_id) ON DELETE CASCADE
            )
        ''')

        # Create Votes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Votes (
                vote_id INTEGER PRIMARY KEY AUTOINCREMENT,
                poll_id INTEGER NOT NULL,
                option_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                FOREIGN KEY (poll_id) REFERENCES Polls(poll_id) ON DELETE CASCADE,
                FOREIGN KEY (option_id) REFERENCES Options(option_id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
            )
        ''')

        # Create Messages table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Messages (
                message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id INTEGER NOT NULL,
                receiver_id INTEGER NOT NULL,
                message_text TEXT NOT NULL,
                timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sender_id) REFERENCES Users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (receiver_id) REFERENCES Users(user_id) ON DELETE CASCADE
            )
        ''')

        conn.commit()

# User functions
def insert_user(username, password_hash, role):
    with closing(create_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO Users (username, password_hash, role)
            VALUES (?, ?, ?)
        ''', (username, password_hash, role))
        conn.commit()
        return cursor.lastrowid

def get_user_by_username(username):
    with closing(create_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM Users WHERE username = ?
        ''', (username,))
        user = cursor.fetchone()
        return user

def get_user_count():
    with closing(create_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM Users')
        count = cursor.fetchone()[0]
        return count

# Group functions
def create_group(group_name, admin_user_id):
    with closing(create_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO Groups (group_name, admin_user_id)
            VALUES (?, ?)
        ''', (group_name, admin_user_id))
        conn.commit()
        return cursor.lastrowid

def get_group_by_name(group_name):
    with closing(create_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM Groups WHERE group_name = ?
        ''', (group_name,))
        group = cursor.fetchone()
        return group

def get_group_count():
    with closing(create_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM Groups')
        count = cursor.fetchone()[0]
        return count

def get_group_id_by_admin(admin_user_id):
    with closing(create_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT group_id FROM Groups WHERE admin_user_id = ?
        ''', (admin_user_id,))
        group = cursor.fetchone()
        return group[0] if group else None

# GroupMembers functions
def add_group_member(group_id, user_id, status='pending'):
    with closing(create_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO GroupMembers (group_id, user_id, status)
            VALUES (?, ?, ?)
        ''', (group_id, user_id, status))
        conn.commit()
        return cursor.lastrowid

def update_group_member_status(member_id, status):
    with closing(create_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE GroupMembers SET status = ? WHERE member_id = ?
        ''', (status, member_id))
        conn.commit()

def get_group_members(group_id, status='accepted'):
    with closing(create_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT Users.user_id, Users.username FROM GroupMembers
            JOIN Users ON GroupMembers.user_id = Users.user_id
            WHERE GroupMembers.group_id = ? AND GroupMembers.status = ?
        ''', (group_id, status))
        members = cursor.fetchall()
        return members

def get_group_member_requests(group_id):
    with closing(create_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT GroupMembers.member_id, Users.user_id, Users.username FROM GroupMembers
            JOIN Users ON GroupMembers.user_id = Users.user_id
            WHERE GroupMembers.group_id = ? AND GroupMembers.status = 'pending'
        ''', (group_id,))
        requests = cursor.fetchall()
        return requests

def get_group_member_count(group_id):
    with closing(create_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) FROM GroupMembers
            WHERE group_id = ? AND status = 'accepted'
        ''', (group_id,))
        count = cursor.fetchone()[0]
        return count

# Poll functions
def create_poll(poll_question, is_public, creator_id, group_id, start_time, end_time):
    with closing(create_connection()) as conn:
        cursor = conn.cursor()
        # Convert datetime objects to strings in ISO format
        start_time_str = start_time.strftime('%Y-%m-%d %H:%M:%S')
        end_time_str = end_time.strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            INSERT INTO Polls (poll_question, is_public, creator_id, group_id, start_time, end_time)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (poll_question, is_public, creator_id, group_id, start_time_str, end_time_str))
        conn.commit()
        return cursor.lastrowid

def get_current_polls(user_id):
    now = datetime.now()
    with closing(create_connection()) as conn:
        cursor = conn.cursor()
        # Get public polls
        cursor.execute('''
            SELECT * FROM Polls
            WHERE is_public = 1 AND start_time <= ? AND end_time >= ?
        ''', (now, now))
        public_polls = cursor.fetchall()

        # Get private polls for groups the user is a member of
        cursor.execute('''
            SELECT Polls.* FROM Polls
            JOIN GroupMembers ON Polls.group_id = GroupMembers.group_id
            WHERE GroupMembers.user_id = ? AND GroupMembers.status = 'accepted'
            AND Polls.is_public = 0 AND start_time <= ? AND end_time >= ?
        ''', (user_id, now, now))
        private_polls = cursor.fetchall()

        return public_polls + private_polls

def get_polls_by_creator(creator_id):
    with closing(create_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM Polls WHERE creator_id = ?
        ''', (creator_id,))
        polls = cursor.fetchall()
        return polls

# Option functions
def add_option(poll_id, option_text):
    with closing(create_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO Options (poll_id, option_text)
            VALUES (?, ?)
        ''', (poll_id, option_text))
        conn.commit()
        return cursor.lastrowid

def get_options_by_poll(poll_id):
    with closing(create_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM Options WHERE poll_id = ?
        ''', (poll_id,))
        options = cursor.fetchall()
        return options

# Vote functions
def cast_vote(poll_id, option_id, user_id):
    with closing(create_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO Votes (poll_id, option_id, user_id)
            VALUES (?, ?, ?)
        ''', (poll_id, option_id, user_id))
        conn.commit()
        return cursor.lastrowid

def has_user_voted(poll_id, user_id):
    with closing(create_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) FROM Votes WHERE poll_id = ? AND user_id = ?
        ''', (poll_id, user_id))
        count = cursor.fetchone()[0]
        return count > 0

def get_vote_counts(poll_id):
    with closing(create_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT Options.option_text, COUNT(Votes.vote_id) as vote_count FROM Options
            LEFT JOIN Votes ON Options.option_id = Votes.option_id
            WHERE Options.poll_id = ?
            GROUP BY Options.option_id
        ''', (poll_id,))
        results = cursor.fetchall()
        return results

# Message functions
def send_message(sender_id, receiver_id, message_text):
    with closing(create_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO Messages (sender_id, receiver_id, message_text)
            VALUES (?, ?, ?)
        ''', (sender_id, receiver_id, message_text))
        conn.commit()
        return cursor.lastrowid

def get_messages(user_id1, user_id2):
    with closing(create_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM Messages
            WHERE (sender_id = ? AND receiver_id = ?) OR (sender_id = ? AND receiver_id = ?)
            ORDER BY timestamp ASC
        ''', (user_id1, user_id2, user_id2, user_id1))
        messages = cursor.fetchall()
        return messages

def get_all_users():
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, username, role FROM Users')
        users = cursor.fetchall()
        return users

def get_user_by_id(user_id):
    with closing(create_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Users WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()
        return user

def delete_user(user_id):
    with closing(create_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM Users WHERE user_id = ?', (user_id,))
        conn.commit()

def delete_group(group_id):
    with closing(create_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM Groups WHERE group_id = ?', (group_id,))
        conn.commit()

def delete_poll(poll_id):
    with closing(create_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM Polls WHERE poll_id = ?', (poll_id,))
        conn.commit()

def update_poll(poll_id, poll_question=None, start_time=None, end_time=None):
    with closing(create_connection()) as conn:
        cursor = conn.cursor()
        fields = []
        params = []
        if poll_question:
            fields.append("poll_question = ?")
            params.append(poll_question)
        if start_time:
            fields.append("start_time = ?")
            params.append(start_time)
        if end_time:
            fields.append("end_time = ?")
            params.append(end_time)
        params.append(poll_id)
        query = f'UPDATE Polls SET {", ".join(fields)} WHERE poll_id = ?'
        cursor.execute(query, params)
        conn.commit()

def update_user_role(user_id, role):
    with closing(create_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE Users SET role = ? WHERE user_id = ?
        ''', (role, user_id))
        conn.commit()

def get_poll_count():
    """Returns the total number of polls."""
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM Polls')
        count = cursor.fetchone()[0]
        return count
    
def get_active_user_count():
    """Returns the number of users who have participated in at least one poll."""
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(DISTINCT user_id) FROM Votes
        ''')
        count = cursor.fetchone()[0]
        return count
    
def get_all_polls():
    """Retrieves all polls from the Polls table."""
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Polls')
        polls = cursor.fetchall()
        return polls

def get_poll_by_id(poll_id):
    """Retrieves a poll and its details by poll ID."""
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Polls WHERE poll_id = ?', (poll_id,))
        poll = cursor.fetchone()
        if poll:
            # Convert to a dictionary for easier access
            poll_dict = {
                'poll_id': poll[0],
                'poll_question': poll[1],
                'is_public': bool(poll[2]),
                'creator_id': poll[3],
                'group_id': poll[4],
                'start_time': poll[5],
                'end_time': poll[6],
            }
            return poll_dict
        else:
            return None
    
def get_users_by_role(role):
    """Retrieves users who have a specific role."""
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Users WHERE role = ?', (role,))
        users = cursor.fetchall()
        return users

def get_polls_by_group(group_id):
    """Retrieves all polls for a specific group."""
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM Polls WHERE group_id = ?
        ''', (group_id,))
        polls = cursor.fetchall()
        return polls 

def get_current_polls_by_group(group_id):
    """Retrieves current polls for a specific group."""
    now = datetime.now()
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM Polls
            WHERE group_id = ? AND start_time <= ? AND end_time >= ?
        ''', (group_id, now, now))
        polls = cursor.fetchall()
        # Convert to list of dictionaries
        poll_list = []
        for poll in polls:
            poll_dict = {
                'poll_id': poll[0],
                'poll_question': poll[1],
                'is_public': bool(poll[2]),
                'creator_id': poll[3],
                'group_id': poll[4],
                'start_time': poll[5],
                'end_time': poll[6],
            }
            poll_list.append(poll_dict)
        return poll_list

def delete_group_member(group_id, user_id):
    """Removes a user from a group."""
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM GroupMembers WHERE group_id = ? AND user_id = ?
        ''', (group_id, user_id))
        conn.commit()

# database.py

def get_polls_user_can_see_results(user_id):
    """Retrieve all polls that the user can see results for."""
    with create_connection() as conn:
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        cursor = conn.cursor()

        # Get public polls
        cursor.execute('''
            SELECT * FROM Polls
            WHERE is_public = 1
        ''')
        public_polls = cursor.fetchall()

        # Get private polls for groups the user is a member of
        cursor.execute('''
            SELECT Polls.* FROM Polls
            JOIN GroupMembers ON Polls.group_id = GroupMembers.group_id
            WHERE GroupMembers.user_id = ? AND GroupMembers.status = 'accepted' AND Polls.is_public = 0
        ''', (user_id,))
        private_polls = cursor.fetchall()

        # Combine and return the polls as a list of dictionaries
        polls = [dict(poll) for poll in public_polls + private_polls]
        return polls
# Initialize the database when the module is run
if __name__ == '__main__':
    init_db()
    print("Database initialized.")
