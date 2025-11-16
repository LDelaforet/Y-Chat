# Y-Chat — Application de messagerie client/serveur

Application de messagerie instantanée composée d'un serveur backend et d'un client avec interface graphique, développée en Python.

## Sommaire
- [Vue d'ensemble](#vue-densemble)
- [Bonnes pratiques](#bonnes-pratiques)
- [Structure du projet](#structure-du-projet)
- [Prérequis](#prérequis)
- [Démarrage rapide](#démarrage-rapide)
- [Serveur public](#serveur-public)
- [Utilisation](#utilisation)
- [Configuration](#configuration)
- [Protocole YCP](#protocole-ycp)

## Vue d'ensemble

Y-Chat est une application d'apprentissage permettant d'expérimenter avec une architecture client/serveur simple. Le projet illustre :

- Communication réseau entre un serveur et plusieurs clients
- Architecture modulaire (client/serveur séparés)
- Gestion de base de données locale (SQLite)
- Protocole de communication personnalisé (YCP)

## Bonnes pratiques

Ce projet suit des conventions de code claires pour faciliter la lecture et la maintenance.

### Conventions de nommage

- **Variables** : `camelCase` → `server_port`, `current_messages`
- **Classes** : `PascalCase` → `ChatGUI`, `User`
- **Fonctions** : `snake_case` → `send_message()`, `receive_loop()`
- **Constantes** : `UPPER_SNAKE_CASE` → `SERVER_PORT`, `PING_INTERVAL`

### Principes de développement

**KISS** (Keep It Simple, Stupid) : Le code privilégie la simplicité et la lisibilité. Une solution simple qui fonctionne vaut mieux qu'une solution complexe qui impressionne.

**DRY** (Don't Repeat Yourself) : La duplication de code est éviter. Il vaut mieux écrire une fonction que d'écrire deux fois le même code.

## Structure du projet

```
YChat/
├── serv/
│   ├── main.py              # Point d'entrée du serveur
│   ├── dbControl.py         # Gestion de la base de données
│   └── database.db          # Base de données SQLite
├── client/
│   ├── main.py              # Point d'entrée du client
│   └── GUI.py               # Interface graphique
└── protocoleYCP.txt         # Spécification du protocole
```

## Prérequis

- **Python 3.8+** (version recommandée : 3.10 ou supérieure)
- Bibliothèques standards Python (sqlite3, socket, tkinter)

### Installation des dépendances

Si le projet utilise des dépendances externes :

```bash
pip install -r requirements.txt
```

> **Note** : Ce projet utilise principalement des bibliothèques standards Python. L'installation de dépendances externes n'est généralement pas nécessaire.

## Démarrage rapide

### 1. Lancer le serveur

Ouvrez un terminal à la racine du projet :

```bash
python serv/main.py
```

Le serveur démarre et écoute sur le port configuré (voir configuration dans `main.py`).

> ⚠️ Assurez-vous que le fichier `database.db` dispose des permissions d'écriture nécessaires.

### 2. Lancer le client

Dans un nouveau terminal :

```bash
python client/main.py
```

L'interface graphique s'ouvre et vous permet de vous connecter au serveur.

## Serveur public

Une instance du serveur est accessible publiquement :

- **Adresse** : `leovelazquez.fr`
- **Port** : `484`

Vous pouvez vous y connecter directement sans lancer votre propre serveur.

Si elle est indisponible prévenez moi sur une de mes adresses mail:

`contact@leovelazquez.fr`, `velazquez.leo@protonmail.com`

## Utilisation

1. Lancez le serveur (local ou utilisez le serveur public)
2. Démarrez le client
3. Connectez-vous avec vos identifiants
4. Commencez à discuter !

## Configuration

Les paramètres de connexion (adresse, port) peuvent être modifiés dans les fichiers de configuration respectifs du client et du serveur.

## Protocole YCP

Le protocole de communication personnalisé est documenté dans le fichier `protocoleYCP.txt` à la racine du projet.

### Aperçu du protocole

YCP (Y-Chat Protocol) utilise des commandes textuelles (séparées par des espaces) pour la communication client/serveur. Exemples (client → serveur) :

- `USER <username>` — définir le nom d'utilisateur (ex: `USER alice`)
- `PASS <password>` — définir le mot de passe (ex: `PASS s3cr3t`)
- `LOGIN` — tenter la connexion (doit être précédé de `USER` et `PASS`)
- `REGISTER` — créer un compte (doit être précédé de `USER` et `PASS`)
- `NEWMSG <channel> <message...>` — envoyer un message dans un channel (ex: `NEWMSG general Bonjour tout le monde !`)
- `NEWPRIVMSG <username> <message...>` — envoyer un message privé (ex: `NEWPRIVMSG bob Salut Bob !`)
- `LISTMSG <channel> <offset>` — lister les messages d'un channel (ex: `LISTMSG general 0`)
- `QUIT` — se déconnecter

Exemples de messages envoyés par le serveur (serveur → client) :

- `MSG <channel> <sender> <timestamp> <content>`
- `PRIVMSG <username> <sender> <timestamp> <content>`

Consultez [protocoleYCP.txt](protocoleYCP.txt) pour la spécification complète.

De nouveaux clients YCP seront peut-être voués a voir le jour sur des repos différents.
