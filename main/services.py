import requests
from django.core.cache import cache
from .models import Pokemon
import logging

logger = logging.getLogger(__name__)

class PokeAPIService:
    BASE_URL = "https://pokeapi.co/api/v2"
    CACHE_TIMEOUT = 60 * 60 * 24  # 24 hours

    @classmethod
    def get_pokemon_list(cls, limit=12, offset=0):
        """Get a paginated list of Pokemon"""
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
            
            # Cache the results
            cache.set(cache_key, data, cls.CACHE_TIMEOUT)
            return data
        except Exception as e:
            logger.error(f"Error fetching Pokemon list: {str(e)}")
            return None

    @classmethod
    def get_pokemon_details(cls, pokemon_id):
        """Get detailed information about a specific Pokemon"""
        cache_key = f"pokemon_details_{pokemon_id}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        try:
            # Get basic Pokemon data
            response = requests.get(f"{cls.BASE_URL}/pokemon/{pokemon_id}")
            response.raise_for_status()
            pokemon_data = response.json()
            
            # Cache the results
            cache.set(cache_key, pokemon_data, cls.CACHE_TIMEOUT)
            return pokemon_data
            
        except Exception as e:
            logger.error(f"Error fetching Pokemon details for ID {pokemon_id}: {str(e)}")
            return None

    @classmethod
    def get_or_create_pokemon(cls, pokemon_id):
        """Get or create a Pokemon object from API data"""
        try:
            # Try to get from database first
            pokemon = Pokemon.objects.filter(pokemon_id=pokemon_id).first()
            if pokemon:
                return pokemon
            
            # If not in database, fetch from API
            pokemon_data = cls.get_pokemon_details(pokemon_id)
            if not pokemon_data:
                return None
            
            # Create Pokemon object
            pokemon = Pokemon.objects.create(
                pokemon_id=pokemon_id,
                name=pokemon_data['name'],
                types=pokemon_data.get('types', []),
                height=pokemon_data.get('height', 0),
                weight=pokemon_data.get('weight', 0),
                stats=pokemon_data.get('stats', {}),
                sprite_url=pokemon_data['sprites']['front_default'],
                sprite_shiny_url=pokemon_data['sprites'].get('front_shiny'),
                abilities=pokemon_data.get('abilities', []),
                base_experience=pokemon_data.get('base_experience'),
                species_url=pokemon_data.get('species', {}).get('url')
            )
            return pokemon
            
        except Exception as e:
            logger.error(f"Error creating Pokemon {pokemon_id}: {str(e)}")
            return None
