# Y-Chat — Client

Client graphique pour Y-Chat, une application de chat multi-clients en Python.

Ce dépôt contient l'interface client (GUI) et le client réseau qui communique avec le serveur Y-Chat via le protocole YCP (voir `protocoleYCP.txt` à la racine du workspace).

## Table des matières

- [Description](#description)
- [Prérequis](#prerequis)
- [Installation](#installation)
- [Lancement](#lancement)
- [Utilisation](#utilisation)
- [Protocole & commandes](#protocole--commandes)
- [Structure des fichiers](#structure-des-fichiers)

## Description

Le client fournit une interface graphique (basée sur CustomTkinter) permettant de se connecter au serveur, gérer les channels, envoyer/recevoir des messages publics et privés, et gérer la liste d'amis. La logique de communication respecte le protocole YCP implémenté côté serveur.

## Prérequis

- Python 3.8 ou supérieur
- pip
- Le package Python `customtkinter` (utilisé pour l'interface graphique)

Installer la dépendance :

```bash
pip install customtkinter
```

Remarque : le client utilise la bibliothèque standard pour les sockets et asyncio; aucune autre dépendance n'est requise par défaut.

## Installation

1. Clonez le dépôt ou copiez le dossier `Client` sur votre machine.
2. Installez `customtkinter` comme indiqué ci‑dessus.

## Lancement

Dans le dossier `Y-Chat/Client`, lancez le client :

```bash
python main.py
```

Au démarrage, une petite fenêtre vous demandera l'adresse du serveur et le port (par défaut `leovelazquez.fr:484` dans l'UI). Après connexion, une fenêtre de login/sinscription apparaîtra pour entrer votre nom d'utilisateur et mot de passe.

## Utilisation

- Se connecter : renseigner l'adresse IP/nom d'hôte et le port du serveur.
- S'authentifier : la popup permet de se connecter (`LOGIN`) ou de s'inscrire (`REGISTER`).
- Channels : la colonne de gauche liste les channels publics et vos amis (conversations privées). Cliquez pour changer de conversation.
- Envoyer un message : saisir du texte et appuyer sur `Entrée` ou le bouton `Envoyer`.
- Demandes d'ami : bouton `+` pour demander un ami (envoie `ASKFRIEND <username>`).
- Récupération des messages : le client utilise `LISTMSG` / `LISTPRIVMSG` pour charger l'historique.

Les commandes supportées côté client (exemples utilisés par l'UI) :

- NEWMSG <channel> <message>
- NEWPRIVMSG <username> <message>
- LISTMSG <channel> <offset>
- LISTPRIVMSG <username> <offset>
- ASKFRIEND <username>
- CHANNELLIST, FRIENDLIST, etc.

Pour le protocole complet et la liste détaillée des messages échangés entre client et serveur, consultez `protocoleYCP.txt` à la racine du workspace.

## Structure des fichiers (dossier `Y-Chat/Client`)

- `main.py` — point d'entrée du client : création de la GUI, connexion réseau et boucle de réception.
- `GUI.py` — composant graphique (CustomTkinter) : fenêtre principale, popups, affichage des messages.
- `commands.py` — handlers pour les commandes reçues (décodage et dispatch des messages serveur).
- `README.md` — ce fichier.