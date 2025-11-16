import bcrypt
import sqlite3

conn = sqlite3.connect("database.db")
db = conn.cursor()


def password_hasher(password: str) -> bytes:
    """Hash un mot de passe avec bcrypt."""
    passwordBytes = password.encode()
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(passwordBytes, salt)


def password_check(password: str, hashed: bytes) -> bool:
    """Vérifie si un mot de passe correspond au hash."""
    return bcrypt.checkpw(password.encode(), hashed)


def register(username, password, id=None):
    """Enregistre un nouvel utilisateur."""
    passwordHash = password_hasher(password)
    
    if id is None:
        db.execute("""
            INSERT INTO users (username, password, is_moderator)
            VALUES (?, ?, false)
        """, (username, passwordHash))
    else:
        db.execute("""
            INSERT INTO users (id, username, password, is_moderator)
            VALUES (?, ?, ?, false)
        """, (id, username, passwordHash))
    
    conn.commit()
    return db.lastrowid


def connect(username, password):
    """Connecte un utilisateur et retourne son ID si les credentials sont valides."""
    db.execute("""
        SELECT id, password FROM users
        WHERE username = ?
    """, (username,))
    
    row = db.fetchone()
    if row is None:
        return None
    
    userId, passwordHash = row
    
    if isinstance(passwordHash, str):
        passwordHash = passwordHash.encode()

    if password_check(password, passwordHash):
        return userId
    
    return None


def get_user_id_by_username(username):
    """Récupère l'ID d'un utilisateur par son username."""
    db.execute("""
        SELECT id FROM users
        WHERE username = ?
    """, (username,))
    
    result = db.fetchone()
    return result[0] if result else None


def get_username_by_user_id(id):
    """Récupère le username d'un utilisateur par son ID."""
    db.execute("""
        SELECT username FROM users
        WHERE id = ?
    """, (id,))
    
    result = db.fetchone()
    return result[0] if result else None


def check_mod_by_username(username):
    """Vérifie si un utilisateur est modérateur."""
    db.execute("""
        SELECT is_moderator FROM users
        WHERE username = ?
    """, (username,))
    
    result = db.fetchone()
    return result[0] if result else None


def new_channel(name, isPrivate=False, id=None):
    """Crée un nouveau channel."""
    if id is None:
        db.execute("""
            INSERT INTO channels (name, is_private)
            VALUES (?, ?)
        """, (name, isPrivate))
    else:
        db.execute("""
            INSERT INTO channels (id, name, is_private)
            VALUES (?, ?, ?)
        """, (id, name, isPrivate))
    
    conn.commit()
    return db.lastrowid


def get_channel_id_by_name(name):
    """Récupère l'ID d'un channel par son nom."""
    db.execute("""
        SELECT id FROM channels
        WHERE name = ?
    """, (name,))
    
    result = db.fetchone()
    return result[0] if result else None


def make_friend_request(userId, friendId):
    """Crée une demande d'ami."""
    db.execute("""
        INSERT INTO friendships (user_id, friend_id, is_pending)
        VALUES (?, ?, ?)
    """, (userId, friendId, True))
    
    conn.commit()
    return db.lastrowid


def get_friendship_id_by_ids(userId, friendId):
    """Récupère l'ID d'une amitié par les IDs des utilisateurs."""
    db.execute("""
        SELECT id FROM friendships
        WHERE user_id = ?
        AND friend_id = ?
    """, (userId, friendId))
    
    result = db.fetchone()
    return result[0] if result else None


def accept_friendship(friendshipId, privateChannelId=None):
    """Accepte une demande d'ami."""
    if friendshipId is None:
        return

    db.execute("""
        UPDATE friendships
        SET is_pending = 0
        WHERE id = ?
    """, (friendshipId,))
    conn.commit()

    if privateChannelId is not None:
        db.execute("""
            UPDATE friendships
            SET channel_id = ?
            WHERE id = ?
        """, (privateChannelId, friendshipId))
        conn.commit()


def refuse_friendship(friendshipId):
    """Refuse et supprime une demande d'ami."""
    db.execute("""
        DELETE FROM friendships
        WHERE id = ?
    """, (friendshipId,))
    conn.commit()


def remove_channel(channelId):
    """Supprime un channel."""
    db.execute("""
        DELETE FROM channels
        WHERE id = ?
    """, (channelId,))
    conn.commit()


def wipe_channel(channelId):
    """Supprime tous les messages d'un channel."""
    db.execute("""
        DELETE FROM messages
        WHERE channel_id = ?
    """, (channelId,))
    conn.commit()


def is_friendship_pending(friendshipId):
    """Vérifie si une demande d'ami est en attente."""
    db.execute("""
        SELECT is_pending FROM friendships
        WHERE id = ?
    """, (int(friendshipId),))
    
    result = db.fetchone()
    return bool(result[0]) if result else None


def who_asked_friendship(user1, user2):
    """Retourne l'ID de celui qui a demandé l'amitié si elle est en attente."""
    db.execute("""
        SELECT user_id, friend_id, is_pending, id FROM friendships
        WHERE (user_id = ? AND friend_id = ?) OR (user_id = ? AND friend_id = ?)
        LIMIT 1
    """, (user1, user2, user2, user1))
    
    result = db.fetchone()
    if not result:
        return None

    requesterId, otherId, isPending, friendshipId = result
    if isPending in (1, '1', True):
        return requesterId
    
    return None


def list_friendships_ids(userId):
    """Liste tous les IDs d'amitiés d'un utilisateur."""
    db.execute("""
        SELECT id FROM friendships
        WHERE friend_id = ? OR user_id = ?
    """, (userId, userId))

    results = db.fetchall()
    return [row[0] for row in results] if results else []


def get_user_id_by_friendship(friendshipId):
    """Récupère les deux IDs d'utilisateurs d'une amitié."""
    db.execute("""
        SELECT user_id, friend_id FROM friendships
        WHERE id = ?
    """, (friendshipId,))

    result = db.fetchone()
    if not result:
        return None

    userId, friendId = result
    return [userId, friendId]


def get_private_channel_id_by_friendship_id(friendshipId):
    """Récupère l'ID du channel privé associé à une amitié."""
    db.execute("""
        SELECT channel_id FROM friendships
        WHERE id = ?
    """, (friendshipId,))

    result = db.fetchone()
    return result[0] if result else None


def send_message(senderId, channelId, content):
    """Envoie un message dans un channel."""
    db.execute("""
        INSERT INTO messages (sender_id, channel_id, content)
        VALUES (?, ?, ?)
    """, (senderId, channelId, content))
    
    conn.commit()
    return db.lastrowid


def read_messages(channelId, offset):
    """Lit les messages d'un channel avec pagination."""
    db.execute("""
        SELECT id
        FROM messages
        WHERE channel_id = ?
        ORDER BY id DESC
        LIMIT 20 OFFSET ?
    """, (channelId, offset))
    
    results = db.fetchall()
    return list(reversed(results)) if results else []


def get_message_info(messageId):
    """Récupère les informations d'un message."""
    db.execute("""
        SELECT channel_id, sender_id, sent_at, content
        FROM messages
        WHERE id = ?
    """, (messageId,))
    
    result = db.fetchone()
    return result if result else None


def get_channel_list():
    """Récupère la liste de tous les channels."""
    db.execute("""
        SELECT id, name, is_private
        FROM channels
    """)
    return db.fetchall()


def rename_channel(channelId, newName):
    """Renomme un channel."""
    db.execute("""
        UPDATE channels
        SET name = ?
        WHERE id = ?
    """, (newName, channelId))
    conn.commit()


def change_password(userId, newPassword):
    """Change le mot de passe d'un utilisateur."""
    newPasswordHash = password_hasher(newPassword)

    db.execute("""
        UPDATE users
        SET password = ?
        WHERE id = ?
    """, (newPasswordHash, userId))

    conn.commit()