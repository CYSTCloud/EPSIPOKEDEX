from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, Http404
from main.services.pokeapi_service import PokeAPIService
from main.models import Pokemon

def pokemon_detail(request, pokemon_id):
    pokemon = PokeAPIService.get_or_create_pokemon(pokemon_id)
    if not pokemon:
        raise Http404("Pokémon non trouvé")
    return render(request, 'pokemon_detail.html', {'pokemon': pokemon})

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