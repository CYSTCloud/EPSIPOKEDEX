import requests
from django.core.cache import cache
from .models import Pokemon
import logging

logger = logging.getLogger(__name__)

class PokeAPIService:
    BASE_URL = "https://pokeapi.co/api/v2"
    CACHE_TIMEOUT = 60 * 60 * 24  

    @classmethod
    def get_pokemon_list(cls, limit=12, offset=0):
        cache_key = f"pokemon_list_{limit}_{offset}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        try:
            response = requests.get(f"{cls.BASE_URL}/pokemon", params={
                'limit': limit,
                'offset': offset
            })
            response.raise_for_status()
            data = response.json()
            

            cache.set(cache_key, data, cls.CACHE_TIMEOUT)
            return data
        except Exception as e:
            logger.error(f"Erreur: {str(e)}")
            return None

    @classmethod
    def get_pokemon_details(cls, pokemon_id):
        cache_key = f"pokemon_details_{pokemon_id}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        try:
            response = requests.get(f"{cls.BASE_URL}/pokemon/{pokemon_id}")
            response.raise_for_status()
            pokemon_data = response.json()

            # Traduire les types en français
            type_translations = {
                'normal': 'Normal',
                'fighting': 'Combat',
                'flying': 'Vol',
                'poison': 'Poison',
                'ground': 'Sol',
                'rock': 'Roche',
                'bug': 'Insecte',
                'ghost': 'Spectre',
                'steel': 'Acier',
                'fire': 'Feu',
                'water': 'Eau',
                'grass': 'Plante',
                'electric': 'Électrik',
                'psychic': 'Psy',
                'ice': 'Glace',
                'dragon': 'Dragon',
                'dark': 'Ténèbres',
                'fairy': 'Fée'
            }

            # Traduire les types
            for type_data in pokemon_data['types']:
                eng_type = type_data['type']['name']
                type_data['type']['name'] = type_translations.get(eng_type, eng_type)

            cache.set(cache_key, pokemon_data, cls.CACHE_TIMEOUT)
            return pokemon_data
            
        except Exception as e:
            logger.error(f"Erreur ID {pokemon_id}: {str(e)}")
            return None

    @classmethod
    def get_or_create_pokemon(cls, pokemon_id):
        try:
            pokemon = Pokemon.objects.filter(pokemon_id=pokemon_id).first()
            if pokemon:
                return pokemon
            
            pokemon_data = cls.get_pokemon_details(pokemon_id)
            if not pokemon_data:
                return None

            # Extraire et traduire les types
            type_translations = {
                'normal': 'Normal',
                'fighting': 'Combat',
                'flying': 'Vol',
                'poison': 'Poison',
                'ground': 'Sol',
                'rock': 'Roche',
                'bug': 'Insecte',
                'ghost': 'Spectre',
                'steel': 'Acier',
                'fire': 'Feu',
                'water': 'Eau',
                'grass': 'Plante',
                'electric': 'Électrik',
                'psychic': 'Psy',
                'ice': 'Glace',
                'dragon': 'Dragon',
                'dark': 'Ténèbres',
                'fairy': 'Fée'
            }
            
            types = []
            for type_data in pokemon_data['types']:
                eng_type = type_data['type']['name']
                fr_type = type_translations.get(eng_type, eng_type)
                types.append(fr_type)
            
            pokemon = Pokemon.objects.create(
                pokemon_id=pokemon_id,
                name=pokemon_data['name'],
                types=types,
                height=pokemon_data['height'],
                weight=pokemon_data['weight'],
                stats={stat['stat']['name']: stat['base_stat'] for stat in pokemon_data['stats']},
                sprite_url=pokemon_data['sprites']['front_default'],
                sprite_shiny_url=pokemon_data['sprites']['front_shiny'],
                abilities=[ability['ability']['name'] for ability in pokemon_data['abilities']],
                base_experience=pokemon_data['base_experience'],
                species_url=pokemon_data['species']['url']
            )
            return pokemon
            
        except Exception as e:
            logger.error(f"Erreur lors de la création du Pokémon ID {pokemon_id}: {str(e)}")
            return None
