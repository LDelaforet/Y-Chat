import sqlite3

conn = sqlite3.connect("database.db")
db = conn.cursor()

def register(username, password, id=None):
    if id == None:
        db.execute("""
            INSERT INTO users (username, password, is_moderator)
            VALUES (?, ?, false)
        """, (username, password))
    else:
        db.execute("""
            INSERT INTO users (id, username, password, is_moderator)
            VALUES (?, ?, ?, false)
        """, (id, username, password))
    conn.commit()
    return(db.lastrowid)

def connect(username, password):
    db.execute("""
        SELECT id FROM users
        WHERE username = ? AND password = ?
    """, (username, password))
    
    result = db.fetchone()
    if result:
        return result[0]
    else:
        return None

def get_user_id_by_username(username):
    db.execute("""
        SELECT id FROM users
        WHERE username = ?
    """, (username,))
    result = db.fetchone()
    if result:
        return result[0]
    else:
        return None

def get_username_by_user_id(id):
    db.execute("""
        SELECT username FROM users
        WHERE id = ?
    """, (id,))
    result = db.fetchone()
    if result:
        return result[0]
    else:
        return None

def check_mod_by_username(username):
    db.execute("""
        SELECT is_moderator FROM users
        WHERE username = ?
    """, (username,))
    result = db.fetchone()
    if result:
        return result[0]
    else:
        return None

def new_channel(name, is_private=False, id=None):
    if id == None:
        db.execute("""
            INSERT INTO channels (name, is_private)
            VALUES (?, ?)
        """, (name, is_private))
    else:
        db.execute("""
            INSERT INTO channels (id, name, is_private)
            VALUES (?, ?, ?)
        """, (id, name, is_private))
    conn.commit()
    return(db.lastrowid)

def get_channel_id(name):
    db.execute("""
        SELECT id FROM channels
        WHERE name = ?
    """, (name,))
    result = db.fetchone()
    if result:
        return result[0]
    else:
        return None

def get_channel_id_by_name(name):
    db.execute("""
        SELECT id FROM channels
        WHERE name = ?
    """, (name,))
    result = db.fetchone()
    if result:
        return result[0]
    else:
        return None

def make_friend_request(userid, friendid):
    db.execute("""
        INSERT INTO friendships (user_id, friend_id, is_pending)
        VALUES (?, ?, ?)
    """, (userid, friendid, True))
    print("Lignes modifiées:", db.rowcount) 
    conn.commit()
    return(db.lastrowid)

def get_friendship_id_by_ids(userId, friendId):
    db.execute("""
        SELECT id FROM friendships
        WHERE user_id = ?
        AND friend_id = ?
    """, (userId,friendId))
    result = db.fetchone()
    print("userId:",userId)
    print("friendId:",friendId)
    print("j'ai fait la requete, result:",result)
    if result:
        return result[0]
    else:
        return None

def accept_friendship(friendshipId, privateChannelId=None):
    if friendshipId is None:
        print("ERROR: friendshipId is None")
        return

    db.execute("""
        UPDATE friendships
        SET is_pending = 0
        WHERE id = ?;
    """, (friendshipId,))
    conn.commit()

    if privateChannelId is not None:
        db.execute("""
            UPDATE friendships
            SET channel_id = ?
            WHERE id = ?;
        """, (privateChannelId, friendshipId,))
        conn.commit()


def refuse_friendship(friendshipId):
    db.execute("""
        DELETE FROM friendships
        WHERE id = ?;
    """, (friendshipId,))
    conn.commit()
    return()

def remove_channel(channelId):
    db.execute("""
        DELETE FROM channels
        WHERE id = ?;
    """, (channelId,))
    conn.commit()
    return()

def wipe_channel(channelId):
    db.execute("""
        DELETE FROM messages
        WHERE channel_id = ?;
    """, (channelId,))
    conn.commit()
    return()

def is_friendship_pending(friendshipID):
    db.execute("""
        SELECT is_pending FROM friendships
        WHERE id = ?
    """, (int(friendshipID),))
    result = db.fetchone()
    if result:
        return bool(result[0])
    else:
        return None

def who_asked_friendship(user1, user2):
    db.execute("""
        SELECT user_id, friend_id, is_pending, id FROM friendships
        WHERE (user_id = ? AND friend_id = ?) OR (user_id = ? AND friend_id = ?)
        LIMIT 1
    """, (user1, user2, user2, user1,))
    result = db.fetchone()
    if not result:
        return None

    requester_id, other_id, is_pending, friendship_id = result
    if is_pending in (1, '1', True):
        return requester_id
    return None

def list_friendships_ids(userId):
    db.execute("""
        SELECT id FROM friendships
        WHERE friend_id = ? OR user_id = ?
    """, (userId, userId))

    results = db.fetchall()

    if not results:
        return []

    return [row[0] for row in results]

def get_user_id_by_friendship(friendshipId):
    db.execute("""
        SELECT user_id FROM friendships
        WHERE id = ?
    """, (friendshipId,))

    userId = db.fetchone()[0]

    db.execute("""
        SELECT friend_id FROM friendships
        WHERE id = ?
    """, (friendshipId,))

    friendId = db.fetchone()[0]

    return [userId, friendId]

def get_private_channel_id_by_friendship_id(friendshipId):
    db.execute("""
        SELECT channel_id FROM friendships
        WHERE id = ?
    """, (friendshipId,))

    result = db.fetchone()
    if result:
        return result[0]
    return None

def send_message(senderId, channelId, content):
    db.execute("""
        INSERT INTO messages (sender_id, channel_id, content)
        VALUES (?, ?, ?)
    """, (senderId, channelId, content))
    conn.commit()
    return(db.lastrowid)

def read_messages(channelId, offset):
    db.execute("""
        SELECT sender_id, content, sent_at
        FROM messages
        WHERE channel_id = ?
        ORDER BY id
        LIMIT 20 OFFSET ?
    """, (channelId, offset))
    results = db.fetchall()

    if not results:
        return []

    return results

def get_channel_list():
    db.execute("""
        SELECT id, name, is_private
        FROM channels
    """)
    return db.fetchall()

def rename_channel(channelId, newName):
    db.execute("""
        UPDATE channels
        SET name = ?
        WHERE id = ?;
    """, (newName, channelId,))
    conn.commit()