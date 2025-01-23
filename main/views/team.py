from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from main.services.pokeapi_service import PokeAPIService
from main.models import Team, TeamPokemon, Pokemon


@login_required
def team_list(request):
    teams = Team.objects.filter(user=request.user).prefetch_related('pokemon')
    return render(request, 'team_list.html', {'teams': teams})

@login_required
def create_team(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            team = Team.objects.create(name=name, user=request.user)
            messages.success(request, f'Équipe "{name}" créée avec succès !')
        else:
            messages.error(request, 'Le nom de l\'équipe est requis.')
    return redirect('team_list')

@login_required
def delete_team(request, team_id):
    if request.method == 'POST':
        team = get_object_or_404(Team, id=team_id, user=request.user)
        team_name = team.name
        team.delete()
        messages.success(request, f'Équipe "{team_name}" supprimée avec succès !')
    return redirect('team_list')

@login_required
def add_to_team(request, team_id, pokemon_id):
    if request.method == 'POST':
        team = get_object_or_404(Team, id=team_id, user=request.user)
        
        if team.pokemon.count() >= 5:
            return JsonResponse({
                'success': False,
                'error': 'L\'équipe a déjà 5 Pokémon'
            })
        
        pokemon = PokeAPIService.get_or_create_pokemon(pokemon_id)
        if not pokemon:
            return JsonResponse({
                'success': False,
                'error': 'Pokémon non trouvé'
            })
        
        position = team.pokemon.count() + 1
        TeamPokemon.objects.create(team=team, pokemon=pokemon, position=position)
        
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False, 'error': 'Méthode de requête invalide'})

@login_required
def remove_from_team(request, team_id, pokemon_id):
    if request.method == 'POST':
        team = get_object_or_404(Team, id=team_id, user=request.user)
        pokemon = get_object_or_404(Pokemon, pokemon_id=pokemon_id)
        TeamPokemon.objects.filter(team=team, pokemon=pokemon).delete()
        
        remaining_pokemon = TeamPokemon.objects.filter(team_id=team_id).order_by('position')
        for i, tp in enumerate(remaining_pokemon, 1):
            tp.position = i
            tp.save()
        
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False, 'error': 'Méthode de requête invalide'})