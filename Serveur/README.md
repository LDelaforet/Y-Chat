# Y-Chat — Serveur

Serveur du projet Y-Chat : un serveur de chat multi-clients minimal en Python, inspiré d'IRC et utilisant un protocole simple (YCP).

## Table des matières

- [Description](#description)
- [Prérequis](#prerequis)
- [Installation](#installation)
- [Initialisation de la base de données](#initialisation-de-la-base-de-donnees)
- [Lancement](#lancement)
- [Configuration](#configuration)
- [Protocole et commandes](#protocole-et-commandes)
- [Structure des fichiers](#structure-des-fichiers)

<a name="description"></a>
## Description

Ce dépôt contient la partie serveur de Y-Chat. Le serveur gère les connexions TCP, l'authentification, les channels publics/privés, les demandes d'ami et la persistance des messages dans une base SQLite.

Le protocole utilisé (YCP) est documenté dans `protocoleYCP.txt` à la racine du workspace — il décrit les messages client->serveur et serveur->client.

<a name="prerequis"></a>
## Prérequis

- Python 3.8 ou supérieur
- pip
- Le module Python `bcrypt` (utilisé pour le hachage des mots de passe)

Installer la dépendance :

```powershell
pip install bcrypt
```

> Remarque : le code utilise uniquement des modules de la bibliothèque standard + `bcrypt`.

<a name="installation"></a>
## Installation

1. Clonez le dépôt ou copiez le dossier `Serveur` sur votre machine.
2. Installez `bcrypt` (voir ci-dessus).

<a name="initialisation-de-la-base-de-donnees"></a>
## Initialisation de la base de données

Le serveur utilise SQLite et se connecte à `database.db`. Un fichier est fourni d'office mais si vous souhaitez le créer vous meme a l'aide des commandes fournies ci-dessous:

```sql
-- users
CREATE TABLE IF NOT EXISTS users (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	username TEXT UNIQUE NOT NULL,
	password BLOB NOT NULL,
	is_moderator BOOLEAN DEFAULT 0
);

-- channels
CREATE TABLE IF NOT EXISTS channels (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	name TEXT UNIQUE NOT NULL,
	is_private BOOLEAN DEFAULT 0
);

-- friendships
CREATE TABLE IF NOT EXISTS friendships (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	user_id INTEGER NOT NULL,
	friend_id INTEGER NOT NULL,
	is_pending BOOLEAN DEFAULT 1,
	channel_id INTEGER,
	FOREIGN KEY(user_id) REFERENCES users(id),
	FOREIGN KEY(friend_id) REFERENCES users(id)
);

-- messages
CREATE TABLE IF NOT EXISTS messages (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	sender_id INTEGER NOT NULL,
	channel_id INTEGER NOT NULL,
	sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	content TEXT,
	FOREIGN KEY(sender_id) REFERENCES users(id),
	FOREIGN KEY(channel_id) REFERENCES channels(id)
);

INSERT INTO "main"."users" ("id", "username", "password", "is_moderator") VALUES (0, 'SERVER', 'SERVER', 1);
INSERT INTO "main"."channels" ("id", "name", "is_private") VALUES (0, 'commands', 0);
```

Vous pouvez créer `database.db` et exécuter ce SQL via `sqlite3` ou un client SQLite.

<a name="lancement"></a>
## Lancement

Depuis le dossier `Server/Serveur`, lancez :

```powershell
python main.py
```

Par défaut, le serveur écoute sur le port 484 (constante `SERVER_PORT` dans `main.py`). Vous verrez un message indiquant que le serveur a démarré.

<a name="configuration"></a>
## Configuration

- Port : modifier la valeur `SERVER_PORT` dans `main.py` si vous souhaitez un autre port.
- Intervalle de ping / timeout : variables `PING_INTERVAL` et `PING_TIMEOUT` dans `main.py`.
- Base de données : `dbControl.py` se connecte à `database.db` dans le dossier courant.

<a name="protocole-et-commandes"></a>
## Protocole et commandes

Le protocole YCP (fichier `protocoleYCP.txt`) décrit les commandes que le client envoie et les réponses du serveur. Les principales commandes prises en charge par le serveur sont listées et implémentées dans `commands.py` — exemple :

- USER, PASS, LOGIN, REGISTER — authentification
- NEWMSG, LISTMSG — messages publics
- NEWPRIVMSG, LISTPRIVMSG — messages privés
- ASKFRIEND, ACCEPTFRIEND, REJECTFRIEND — gestion des amis
- CHANNELLIST — obtenir la liste des channels
- PING/PONG — vérification de connexion

Le serveur envoie plusieurs types de messages au client, like `SUCCESS`, `WARNING <msg>`, `ERROR <msg>`, `MSG`, `PRIVMSG`, etc. Voir `protocoleYCP.txt` pour le protocole complet.

<a name="structure-des-fichiers"></a>
## Structure des fichiers (dossier `Server/Serveur`)

- `main.py` — point d'entrée du serveur, gestion des sockets et de la boucle asyncio.
- `classes.py` — définition de la classe `User` (gestion du socket, envoi, ping, déconnexion).
- `commands.py` — implémentation des commandes et du dictionnaire `COMMAND_LIST`.
- `dbControl.py` — accès à la base de données (SQLite) et fonctions utilitaires (hachage avec bcrypt).
- `README.md` — ce fichier.