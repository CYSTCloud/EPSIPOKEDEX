from django.shortcuts import render
from django.core.paginator import Paginator
from main.services.pokeapi_service import PokeAPIService
from main.models import Pokemon
import logging

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
