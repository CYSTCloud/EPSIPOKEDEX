from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from main.models import Pokemon, Team
from main.views import battle
import random
import logging

logger = logging.getLogger(__name__)

def get_opponent_action():
    return random.choice(['attaque'])

def execute_turn(request, team, opponent, action):
    turn_log = []

    player_pokemon = team[0] if team else None
    opponent_pokemon = opponent[0] if opponent else None

    if not player_pokemon or not opponent_pokemon:
        turn_log.append("Un des camps n'a plus de Pokémon, fin du combat.")
        return {
            'team': team,
            'opponent': opponent,
            'log': turn_log,
            'winner': 'Équipe adverse' if not team else 'Votre équipe'
        }
    
    if 'effects' not in player_pokemon:
        player_pokemon['effects'] = {}
    if 'effects' not in opponent_pokemon:
        opponent_pokemon['effects'] = {}

    for effect in ['defense_boost', 'evasion']:
        if effect in player_pokemon['effects']:
            player_pokemon['effects'][effect] -= 1
            if player_pokemon['effects'][effect] <= 0:
                del player_pokemon['effects'][effect]

        if effect in opponent_pokemon['effects']:
            opponent_pokemon['effects'][effect] -= 1
            if opponent_pokemon['effects'][effect] <= 0:
                del opponent_pokemon['effects'][effect]

    # Action du joueur
    if action == 'attaque':

        defense_multiplier = 0.75 if 'defense_boost' in opponent_pokemon['effects'] else 0.5
        damage = max(0, player_pokemon['attack'] - (opponent_pokemon['defense'] * defense_multiplier))
        opponent_pokemon['hp'] -= damage
        turn_log.append(f"{player_pokemon['name']} attaque {opponent_pokemon['name']} et inflige {damage} dégâts.")
        
        if opponent_pokemon['hp'] <= 0:
            turn_log.append(f"{opponent_pokemon['name']} est KO.")
            opponent.pop(0)

    elif action == 'défense':
        player_pokemon['effects']['defense_boost'] = 3 
        turn_log.append(f"{player_pokemon['name']} adopte une posture défensive. Sa défense est augmentée pour 3 tours.")
    
    else:
        turn_log.append(f"Action non reconnue : {action}")

    # Action de l'adversaire
    opponent_action = get_opponent_action()

    if opponent_action == 'attaque':
        defense_multiplier = 0.75 if 'defense_boost' in player_pokemon['effects'] else 0.5
        damage = max(0, opponent_pokemon['attack'] - (player_pokemon['defense'] * defense_multiplier))
        player_pokemon['hp'] -= damage
        turn_log.append(f"{opponent_pokemon['name']} attaque {player_pokemon['name']} et inflige {damage} dégâts.")
        if player_pokemon['hp'] <= 0:
            turn_log.append(f"{player_pokemon['name']} est KO.")
            team.pop(0) 

    elif opponent_action == 'défense':
        opponent_pokemon['effects']['defense_boost'] = 3
        turn_log.append(f"{opponent_pokemon['name']} adopte une posture défensive. Sa défense est augmentée pour 3 tours.")
    
    else:
        turn_log.append(f"Action non reconnue : {opponent_action}")
    
    winner = None
    if not team:
        winner = 'Équipe adverse'
    elif not opponent:
        winner = 'Votre équipe'
    
    
    return {
        'team': team,
        'opponent': opponent,
        'log': turn_log,
        'winner': winner
    }

    