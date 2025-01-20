from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
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
        # Get page number and search query
        page = request.GET.get('page', 1)
        search_query = request.GET.get('search', '').strip()
        
        logger.info(f"Home page requested - Page: {page}, Search: {search_query}")
        
        # Calculate offset based on page
        page_size = 12
        page_number = int(page)
        offset = (page_number - 1) * page_size
        
        if search_query:
            # Check if search query is a number (Pokemon ID)
            try:
                if search_query.isdigit():
                    pokemon_id = int(search_query)
                    pokemon_list = Pokemon.objects.filter(pokemon_id=pokemon_id)
                    if not pokemon_list.exists():
                        # Try to fetch from API if not in database
                        pokemon = PokeAPIService.get_or_create_pokemon(pokemon_id)
                        if pokemon:
                            pokemon_list = [pokemon]
                else:
                    # Search by name (case-insensitive)
                    pokemon_list = Pokemon.objects.filter(name__icontains=search_query)
                    if not pokemon_list.exists():
                        # If no results in database, try to fetch from API
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
                
                logger.info(f"Search results count: {len(pokemon_list)}")
                paginator = Paginator(pokemon_list, page_size)
                pokemons = paginator.get_page(page)
            
            except ValueError as e:
                logger.error(f"Invalid search query: {str(e)}")
                return render(request, 'home.html', {
                    'error_message': 'Invalid search query. Please enter a valid Pokemon name or ID.'
                })
        else:
            # Get Pokemon list from API
            logger.info(f"Fetching Pokemon list from API - Offset: {offset}, Limit: {page_size}")
            api_response = PokeAPIService.get_pokemon_list(limit=page_size, offset=offset)
            
            if not api_response:
                logger.error("Failed to get Pokemon list from API")
                return render(request, 'home.html', {
                    'error_message': 'Failed to fetch Pokemon data.'
                })
            
            logger.info(f"API Response - Count: {api_response.get('count')}, Results: {len(api_response.get('results', []))}")
            
            # Get or create Pokemon objects for each result
            pokemon_list = []
            for pokemon_data in api_response['results']:
                pokemon_id = int(pokemon_data['url'].split('/')[-2])
                logger.info(f"Processing Pokemon ID: {pokemon_id}")
                pokemon = PokeAPIService.get_or_create_pokemon(pokemon_id)
                if pokemon:
                    pokemon_list.append(pokemon)
                else:
                    logger.error(f"Failed to get/create Pokemon ID: {pokemon_id}")
            
            logger.info(f"Processed Pokemon count: {len(pokemon_list)}")
            
            # Create a custom paginator for API results
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

            # Create a paginator instance with the API's total count
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
        logger.info("Rendering home template with context")
        return render(request, 'home.html', context)
        
    except Exception as e:
        logger.error(f"Error in home view: {str(e)}", exc_info=True)
        return render(request, 'home.html', {
            'error_message': 'An error occurred while loading Pokemon.'
        })

def pokemon_detail(request, pokemon_id):
    pokemon = get_object_or_404(Pokemon, pokemon_id=pokemon_id)
    return render(request, 'pokemon_detail.html', {'pokemon': pokemon})

@login_required
def team_list(request):
    """View for listing user's teams"""
    teams = Team.objects.filter(user=request.user).prefetch_related('pokemon')
    return render(request, 'team_list.html', {'teams': teams})

@login_required
def create_team(request):
    """Create a new team"""
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            team = Team.objects.create(name=name, user=request.user)
            messages.success(request, f'Team "{name}" created successfully!')
        else:
            messages.error(request, 'Team name is required.')
    return redirect('team_list')

@login_required
def delete_team(request, team_id):
    """Delete a team"""
    if request.method == 'POST':
        team = get_object_or_404(Team, id=team_id, user=request.user)
        team_name = team.name
        team.delete()
        messages.success(request, f'Team "{team_name}" deleted successfully!')
    return redirect('team_list')

@login_required
def add_to_team(request, team_id, pokemon_id):
    """Add a Pokemon to a team"""
    if request.method == 'POST':
        team = get_object_or_404(Team, id=team_id, user=request.user)
        
        # Check if team is full
        if team.pokemon.count() >= 5:
            return JsonResponse({
                'success': False,
                'error': 'Team already has 5 Pokemon'
            })
        
        # Get or create the Pokemon
        pokemon = PokeAPIService.get_or_create_pokemon(pokemon_id)
        if not pokemon:
            return JsonResponse({
                'success': False,
                'error': 'Pokemon not found'
            })
        
        # Add Pokemon to team
        position = team.pokemon.count() + 1
        TeamPokemon.objects.create(team=team, pokemon=pokemon, position=position)
        
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def remove_from_team(request, team_id, pokemon_id):
    """Remove a Pokemon from a team"""
    if request.method == 'POST':
        team_pokemon = get_object_or_404(
            TeamPokemon,
            team__id=team_id,
            team__user=request.user,
            pokemon__id=pokemon_id
        )
        team_pokemon.delete()
        
        # Reorder remaining Pokemon
        remaining_pokemon = TeamPokemon.objects.filter(team_id=team_id).order_by('position')
        for i, tp in enumerate(remaining_pokemon, 1):
            tp.position = i
            tp.save()
        
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def pokemon_search_api(request):
    """API endpoint for searching Pokemon"""
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'error': 'Query parameter is required'}, status=400)
    
    # Search in database first
    pokemon_list = list(Pokemon.objects.filter(
        name__icontains=query
    ).values('id', 'name', 'sprite_url')[:10])
    
    # If no results or few results, try API
    if len(pokemon_list) < 5:
        api_response = PokeAPIService.get_pokemon_list(limit=1000, offset=0)
        if api_response and 'results' in api_response:
            matching_pokemon = [
                p for p in api_response['results']
                if query.lower() in p['name'].lower()
            ][:10]
            
            for pokemon_data in matching_pokemon:
                pokemon_id = int(pokemon_data['url'].split('/')[-2])
                pokemon = PokeAPIService.get_or_create_pokemon(pokemon_id)
                if pokemon:
                    pokemon_dict = {
                        'id': pokemon.id,
                        'name': pokemon.name,
                        'sprite_url': pokemon.sprite_url
                    }
                    if pokemon_dict not in pokemon_list:
                        pokemon_list.append(pokemon_dict)
    
    return JsonResponse(pokemon_list, safe=False)

@login_required
def battle(request):
    """Battle view"""
    teams = Team.objects.filter(user=request.user).prefetch_related('pokemon')
    return render(request, 'battle.html', {'teams': teams})

@login_required
def get_battle_teams(request, team_id):
    """Get teams for battle"""
    # Get user's team
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
    
    # Generate opponent team
    all_pokemon = list(Pokemon.objects.all())
    opponent_pokemon = random.sample(all_pokemon, min(5, len(all_pokemon)))
    opponent_data = {
        'name': 'Opponent Team',
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
    """Start a battle"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)
    
    team = get_object_or_404(Team, id=team_id, user=request.user)
    battle_log = []
    
    # Get team Pokemon with stats
    team_pokemon = [{
        'name': tp.pokemon.name,
        'hp': random.randint(50, 100),
        'attack': random.randint(40, 80),
        'defense': random.randint(30, 60)
    } for tp in team.teampokemon_set.all()]
    
    # Generate opponent team
    all_pokemon = list(Pokemon.objects.all())
    opponent_pokemon = [{
        'name': pokemon.name,
        'hp': random.randint(50, 100),
        'attack': random.randint(40, 80),
        'defense': random.randint(30, 60)
    } for pokemon in random.sample(all_pokemon, min(5, len(all_pokemon)))]
    
    # Simple battle simulation
    round = 1
    while team_pokemon and opponent_pokemon:
        battle_log.append(f"Round {round}")
        
        # Team Pokemon attacks
        if team_pokemon:
            attacker = team_pokemon[0]
            defender = opponent_pokemon[0]
            damage = max(0, attacker['attack'] - defender['defense'] // 2)
            defender['hp'] -= damage
            battle_log.append(f"{attacker['name']} attacks {defender['name']} for {damage} damage!")
            
            if defender['hp'] <= 0:
                battle_log.append(f"{defender['name']} fainted!")
                opponent_pokemon.pop(0)
        
        # Opponent Pokemon attacks
        if opponent_pokemon:
            attacker = opponent_pokemon[0]
            defender = team_pokemon[0]
            damage = max(0, attacker['attack'] - defender['defense'] // 2)
            defender['hp'] -= damage
            battle_log.append(f"{attacker['name']} attacks {defender['name']} for {damage} damage!")
            
            if defender['hp'] <= 0:
                battle_log.append(f"{defender['name']} fainted!")
                team_pokemon.pop(0)
        
        round += 1
        if round > 50:  # Prevent infinite battles
            break
    
    # Determine winner
    if team_pokemon:
        winner = f"Team {team.name}"
    elif opponent_pokemon:
        winner = "Opponent Team"
    else:
        winner = "Draw"
    
    return JsonResponse({
        'winner': winner,
        'log': battle_log
    })

def register(request):
    """Register a new user"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful! Welcome to Pokedex!')
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "Vous avez été déconnecté avec succès.")
    return redirect('home')
