from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, Http404
from django.contrib import messages
from .services import PokeAPIService
from .models import Pokemon, Team, TeamPokemon
import logging
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, logout
import random

logger = logging.getLogger(__name__)

def home(request):
    try:
        page = request.GET.get('page', 1)
        search_query = request.GET.get('search', '').strip()
        
        logger.info(f"Page d'accueil demandée - Page: {page}, Recherche: {search_query}")
        
        page_size = 12
        page_number = int(page)
        offset = (page_number - 1) * page_size
        
        if search_query:
            try:
                if search_query.isdigit():
                    pokemon_id = int(search_query)
                    pokemon_list = Pokemon.objects.filter(pokemon_id=pokemon_id)
                    if not pokemon_list.exists():
                        pokemon = PokeAPIService.get_or_create_pokemon(pokemon_id)
                        if pokemon:
                            pokemon_list = [pokemon]
                else:
                    pokemon_list = Pokemon.objects.filter(name__icontains=search_query)
                    if not pokemon_list.exists():
                        api_response = PokeAPIService.get_pokemon_list(limit=1000, offset=0)
                        if api_response and 'results' in api_response:
                            matching_pokemon = [
                                p for p in api_response['results'] 
                                if search_query.lower() in p['name'].lower()
                            ]
                            pokemon_list = []
                            for pokemon_data in matching_pokemon:
                                pokemon_id = int(pokemon_data['url'].split('/')[-2])
                                pokemon = PokeAPIService.get_or_create_pokemon(pokemon_id)
                                if pokemon:
                                    pokemon_list.append(pokemon)
                
                logger.info(f"Nombre de résultats de recherche: {len(pokemon_list)}")
                paginator = Paginator(pokemon_list, page_size)
                pokemons = paginator.get_page(page)
            
            except ValueError as e:
                logger.error(f"Requête de recherche invalide: {str(e)}")
                return render(request, 'home.html', {
                    'error_message': 'Requête de recherche invalide. Veuillez entrer un nom ou un ID de Pokémon valide.'
                })
        else:
            logger.info(f"Récupération de la liste des Pokémon depuis l'API - Offset: {offset}, Limite: {page_size}")
            api_response = PokeAPIService.get_pokemon_list(limit=page_size, offset=offset)
            
            if not api_response:
                logger.error("Échec de la récupération de la liste des Pokémon depuis l'API")
                return render(request, 'home.html', {
                    'error_message': 'Échec de la récupération des données Pokémon.'
                })
            
            logger.info(f"Réponse de l'API - Nombre: {api_response.get('count')}, Résultats: {len(api_response.get('results', []))}")
            
            pokemon_list = []
            for pokemon_data in api_response['results']:
                pokemon_id = int(pokemon_data['url'].split('/')[-2])
                logger.info(f"Traitement de l'ID Pokémon: {pokemon_id}")
                pokemon = PokeAPIService.get_or_create_pokemon(pokemon_id)
                if pokemon:
                    pokemon_list.append(pokemon)
                else:
                    logger.error(f"Échec de la récupération/création du Pokémon ID: {pokemon_id}")
            
            logger.info(f"Nombre de Pokémon traités: {len(pokemon_list)}")
            
            class APIPaginator:
                def __init__(self, object_list, per_page, count, number):
                    self.object_list = object_list
                    self.per_page = per_page
                    self._count = count
                    self.number = number

                @property
                def count(self):
                    return self._count

                @property
                def num_pages(self):
                    return (self._count + self.per_page - 1) // self.per_page

                @property
                def page_range(self):
                    return range(1, self.num_pages + 1)

                def has_next(self):
                    return self.number < self.num_pages

                def has_previous(self):
                    return self.number > 1

                def has_other_pages(self):
                    return self.has_next or self.has_previous

                def next_page_number(self):
                    return self.number + 1

                def previous_page_number(self):
                    return self.number - 1

                def start_index(self):
                    return (self.number - 1) * self.per_page + 1

                def end_index(self):
                    return min(self.number * self.per_page, self._count)

            pokemons = APIPaginator(
                object_list=pokemon_list,
                per_page=page_size,
                count=api_response['count'],
                number=page_number
            )

        context = {
            'pokemons': pokemons,
            'search_query': search_query
        }
        logger.info("Rendu du modèle d'accueil avec le contexte")
        return render(request, 'home.html', context)
        
    except Exception as e:
        logger.error(f"Erreur dans la vue d'accueil: {str(e)}", exc_info=True)
        return render(request, 'home.html', {
            'error_message': 'Une erreur est survenue lors du chargement des Pokémon.'
        })

def pokemon_detail(request, pokemon_id):
    pokemon = PokeAPIService.get_or_create_pokemon(pokemon_id)
    if not pokemon:
        raise Http404("Pokémon non trouvé")
    return render(request, 'pokemon_detail.html', {'pokemon': pokemon})

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

@login_required
def pokemon_search_api(request):
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'error': 'Le paramètre de requête est requis'}, status=400)
    
    # On utilise un set pour stocker les IDs déjà traités
    processed_ids = set()
    pokemon_list = []
    
    # Recherche dans la base de données locale
    local_pokemon = Pokemon.objects.filter(name__icontains=query)[:10]
    for pokemon in local_pokemon:
        processed_ids.add(pokemon.pokemon_id)
        pokemon_list.append({
            'id': pokemon.pokemon_id,
            'name': pokemon.name,
            'sprite_url': pokemon.sprite_url
        })
    
    # Si on a moins de 5 résultats, on cherche dans l'API
    if len(pokemon_list) < 5:
        api_response = PokeAPIService.get_pokemon_list(limit=1000, offset=0)
        if api_response and 'results' in api_response:
            matching_pokemon = [
                p for p in api_response['results']
                if query.lower() in p['name'].lower()
            ][:10]
            
            for pokemon_data in matching_pokemon:
                pokemon_id = int(pokemon_data['url'].split('/')[-2])
                # On vérifie si on n'a pas déjà ce Pokémon
                if pokemon_id not in processed_ids:
                    pokemon = PokeAPIService.get_or_create_pokemon(pokemon_id)
                    if pokemon:
                        processed_ids.add(pokemon_id)
                        pokemon_list.append({
                            'id': pokemon.pokemon_id,
                            'name': pokemon.name,
                            'sprite_url': pokemon.sprite_url
                        })
    
    return JsonResponse(pokemon_list, safe=False)

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
            'hp': random.randint(50, 100),
            'attack': random.randint(40, 80),
            'defense': random.randint(30, 60)
        } for tp in team.teampokemon_set.all()]
    }
    
    all_pokemon = list(Pokemon.objects.all())
    opponent_pokemon = random.sample(all_pokemon, min(5, len(all_pokemon)))
    opponent_data = {
        'name': 'Équipe adverse',
        'pokemon': [{
            'name': pokemon.name,
            'sprite_url': pokemon.sprite_url,
            'hp': random.randint(50, 100),
            'attack': random.randint(40, 80),
            'defense': random.randint(30, 60)
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
        'name': tp.pokemon.name,
        'hp': random.randint(50, 100),
        'attack': random.randint(40, 80),
        'defense': random.randint(30, 60)
    } for tp in team.teampokemon_set.all()]
    
    all_pokemon = list(Pokemon.objects.all())
    opponent_pokemon = [{
        'name': pokemon.name,
        'hp': random.randint(50, 100),
        'attack': random.randint(40, 80),
        'defense': random.randint(30, 60)
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

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Bienvenue !')
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "Vous avez été déconnecté avec succès.")
    return redirect('home')
