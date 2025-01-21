from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from main.models import Pokemon, Team
import random


@login_required
def battle(request):
    teams = Team.objects.filter(user=request.user).prefetch_related('pokemon')
    return render(request, 'battle.html', {'teams': teams})

@login_required
def get_battle_teams(request, team_id):
    team = get_object_or_404(Team, id=team_id, user=request.user)
    team_data = {
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
    
    return JsonResponse({'team': team_data, 'opponent': opponent_data})

@login_required
def start_battle(request, team_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode de requête invalide'}, status=405)
    
    team = get_object_or_404(Team, id=team_id, user=request.user)
    battle_log = []
    
    team_pokemon = [{
        'sprite_url': tp.pokemon.sprite_url,
        'name': tp.pokemon.name,
        'hp': tp.pokemon.stats['hp'],
        'attack': tp.pokemon.stats['attack'],
        'special_attack': tp.pokemon.stats['special-attack'],
        'defense': tp.pokemon.stats['defense'],
        'special_defense': tp.pokemon.stats['special-defense'],
        'speed': tp.pokemon.stats['speed']
    } for tp in team.teampokemon_set.all()]
    
    all_pokemon = list(Pokemon.objects.all())
    opponent_pokemon = [{
        'name': pokemon.name,
        'sprite_url': pokemon.sprite_url,
        'hp': pokemon.stats['hp'],
        'attack': pokemon.stats['attack'],
        'special_attack': pokemon.stats['special-attack'],
        'defense': pokemon.stats['defense'],
        'special_defense': pokemon.stats['special-defense'],
        'speed': pokemon.stats['speed']
    } for pokemon in random.sample(all_pokemon, min(5, len(all_pokemon)))]
    
    round = 1
    while team_pokemon and opponent_pokemon:
        battle_log.append(f"Tour {round}")
        
        if team_pokemon:
            attacker = team_pokemon[0]
            defender = opponent_pokemon[0]
            damage = max(0, attacker['attack'] - defender['defense'] // 2)
            defender['hp'] -= damage
            battle_log.append(f"{attacker['name']} attaque {defender['name']} pour {damage} dégâts !")
            
            if defender['hp'] <= 0:
                battle_log.append(f"{defender['name']} est K.O. !")
                opponent_pokemon.pop(0)
        
        if opponent_pokemon:
            attacker = opponent_pokemon[0]
            defender = team_pokemon[0]
            damage = max(0, attacker['attack'] - defender['defense'] // 2)
            defender['hp'] -= damage
            battle_log.append(f"{attacker['name']} attaque {defender['name']} pour {damage} dégâts !")
            
            if defender['hp'] <= 0:
                battle_log.append(f"{defender['name']} est K.O. !")
                team_pokemon.pop(0)
        
        round += 1
        if round > 50:
            break
    
    if team_pokemon:
        winner = f"Équipe {team.name}"
    elif opponent_pokemon:
        winner = "Équipe adverse"
    else:
        winner = "Match nul"
    
    return JsonResponse({
        'winner': winner,
        'log': battle_log
    })