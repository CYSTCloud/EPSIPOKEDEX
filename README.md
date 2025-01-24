# Pokédex - Application Web Django

## Description
Pokédex est une application web Django qui permet aux utilisateurs de créer et gérer leurs équipes Pokémon, de participer à des combats et d'explorer l'univers Pokémon. L'application utilise l'API PokeAPI pour obtenir les données des Pokémon.


## Fonctionnalités
- Parcourir et rechercher des Pokémon
- Créer et gérer des équipes de Pokémon
- Système de combat entre équipes
- Authentification des utilisateurs

### Système de combat
- Combats simples entre deux équipes
- Combats multiples entre plusieurs équipes
- Gestion des statistiques des Pokémon
### Gestion des équipes
- Création d'équipes personnalisées
- Ajout/Suppression de Pokémon
- Limite de 5 Pokémon par équipe
### Authentification
- Inscription utilisateur
- Connexion/Déconnexion
- Profil utilisateur

## API et Services
### PokeAPI
L'application utilise PokeAPI pour récupérer les données des Pokémon :
- Informations de base
- Statistiques
- Images et sprites
- Types et capacités

### Endpoints API internes
- `/api/pokemon/search/` : Recherche de Pokémon
- `/teams/<team_id>/add_pokemon/<pokemon_id>/` : Ajout d'un Pokémon à une équipe
- `/teams/<team_id>/remove_pokemon/<pokemon_id>/` : Suppression d'un Pokémon d'une équipe
- `/battle/action/<team_id>/` : Actions de combat


## Base de données
### Relations
- Un utilisateur peut avoir plusieurs équipes
- Une équipe peut contenir jusqu'à 5 Pokémon
- Un Pokémon peut appartenir à plusieurs équipes
### Modèles principaux
- `User` : Utilisateurs de l'application
- `Pokemon` : Données des Pokémon
- `Team` : Équipes de Pokémon
- `TeamPokemon` : Association entre Pokémon et équipes
- `Battle` : Données des combats

## Sécurité
- Authentification requise pour les actions sensibles
- Protection CSRF sur les formulaires
- Gestion des permissions utilisateur

## Technologies Utilisées
- Django 4.2
- Python 3.12
- Bootstrap 5
- SQLite3
- PokeAPI

## Installation

1. Cloner le dépôt :
```bash
git clone ssh
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
