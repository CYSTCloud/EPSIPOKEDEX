from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from main.models import Pokemon, Team
from .turn import execute_turn
import random
import logging
import json

logger = logging.getLogger(__name__)

@login_required
def battle(request):
    teams = Team.objects.filter(user=request.user).prefetch_related('pokemon')
    return render(request, 'battle.html', {'teams': teams})

def get_team_data(team):
    return {
        'name': team.name,
        'pokemon': [{
            'name': tp.pokemon.name,
            'sprite_url': tp.pokemon.sprite_url,
            'hp': tp.pokemon.stats['hp'],
            'attack': tp.pokemon.stats['attack'],
            'special_attack': tp.pokemon.stats['special-attack'],
            'defense': tp.pokemon.stats['defense'],
            'special_defense': tp.pokemon.stats['special-defense'],
            'speed': tp.pokemon.stats['speed']
        } for tp in team.teampokemon_set.all()]
    }

@login_required
def get_battle_teams(request, team_id):
    team = get_object_or_404(Team, id=team_id, user=request.user)
    if 'team_data' in request.session:
        team_data = request.session['team_data']
    else:
        team_data = get_team_data(team)   
        request.session['team_data'] = team_data
        request.session.modified = True
            
    reset_opponent = request.GET.get('reset', 'false').lower() == 'true'

    if reset_opponent:
        team_data = get_team_data(team)   
        request.session['team_data'] = team_data
        request.session.modified = True

    if reset_opponent or 'opponent_team' not in request.session:
        all_pokemon = list(Pokemon.objects.all())
        opponent_pokemon = random.sample(all_pokemon, min(5, len(all_pokemon)))
        opponent_data = {
            'name': 'Équipe adverse',
            'pokemon': [{
                'name': pokemon.name,
                'sprite_url': pokemon.sprite_url,
                'hp': pokemon.stats['hp'],
                'attack': pokemon.stats['attack'],
                'special_attack': pokemon.stats['special-attack'],
                'defense': pokemon.stats['defense'],
                'special_defense': pokemon.stats['special-defense'],
                'speed': pokemon.stats['speed']
            } for pokemon in opponent_pokemon]
        }
        request.session['opponent_team'] = opponent_data
        request.session.modified = True
    else:
        opponent_data = request.session['opponent_team']
    
    return JsonResponse({'team': team_data, 'opponent': opponent_data})

@login_required
def start_battle(request, team_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode de requête invalide'}, status=405)
    
    team = get_object_or_404(Team, id=team_id, user=request.user)
    battle_log = []
    
    team_pokemon = request.session.get('team_data', {}).get('pokemon', [])
    if not team_pokemon:
        return JsonResponse({'error': 'Équipe non trouvée dans la session'}, status=400)
    opponent_team = request.session.get('opponent_team')

    if not opponent_team:
        return JsonResponse({'error': 'Équipe adverse non trouvée dans la session'}, status=400)
    opponent_pokemon = opponent_team['pokemon']

    round = 1
    while team_pokemon and opponent_pokemon:
        battle_log.append(f"Tour {round}")
        
        turn_result = execute_turn(team_pokemon, opponent_pokemon, 'attaque')
        battle_log.extend(turn_result['log'])

        team_pokemon = turn_result['team']
        opponent_pokemon = turn_result['opponent']
        
        round += 1
        if round > 50:
            battle_log.append("Limite de tours atteinte !")
            break
    
    if team_pokemon:
        winner = f"Équipe {team.name}"
    elif opponent_pokemon:
        winner = "Équipe adverse"
    else:
        winner = "Match nul"
    
    return JsonResponse({'log': battle_log, 'winner': winner})

@login_required
def action(request, team_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode de requête invalide'}, status=405)
    
    try:
        body = json.loads(request.body)
        action = body.get('action')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Données JSON invalides'}, status=400)
    
    if not action:
        return JsonResponse({'error': 'Action non spécifiée'}, status=400)
    
    team_pokemon = request.session.get('team_data', {}).get('pokemon', [])
    if not team_pokemon:
        return JsonResponse({'error': 'Équipe non trouvée dans la session'}, status=400)
    
    opponent_team = request.session.get('opponent_team')
    if not opponent_team:
        return JsonResponse({'error': 'Équipe adverse non trouvée dans la session'}, status=400)
    opponent_pokemon = opponent_team['pokemon']
    

    logger.debug(f"Votre équipe : {team_pokemon}")
    turn_result = execute_turn(request, team_pokemon, opponent_pokemon, action)

    request.session['opponent_team']['pokemon'] = turn_result['opponent']
    request.session['team_data']['pokemon'] = turn_result['team']
    request.session.modified = True

    logger.debug(f"Action: {action}")

    return JsonResponse({
        'log': turn_result['log'],
        'winner': turn_result.get('winner'),
        'team': turn_result['team'],
        'opponent': turn_result['opponent'] 
    })
