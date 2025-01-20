# Pokédex - Application Web Django

## Description
Une application web Django permettant aux utilisateurs de parcourir les Pokémon, créer des équipes et participer à des batailles.

## Fonctionnalités
- Parcourir et rechercher des Pokémon
- Créer et gérer des équipes de Pokémon
- Système de combat entre équipes
- Authentification des utilisateurs
- Interface entièrement en français

## Technologies Utilisées
- Django 4.2
- Python 3.12
- Bootstrap 5
- SQLite3
- PokeAPI

## Installation

1. Cloner le dépôt :
```bash
git clone https://github.com/votre-nom/pokedex.git
cd pokedex
```

2. Créer un environnement virtuel :
```bash
python -m venv venv

venv\Scripts\activate    
```

3. Installer les dépendances :
```bash
pip install -r requirements.txt
```

4. Appliquer les migrations :
```bash
python manage.py migrate
```

5. Lancer le serveur :
```bash
python manage.py runserver
```
