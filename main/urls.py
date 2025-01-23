from django.urls import path
from main.views import battle, home, pokemon, team, user

urlpatterns = [
    path('', home.home, name='home'),
    path('pokemon/<int:pokemon_id>/', pokemon.pokemon_detail, name='pokemon_detail'),
    path('teams/', team.team_list, name='team_list'),
    path('teams/create/', team.create_team, name='create_team'),
    path('teams/<int:team_id>/delete/', team.delete_team, name='delete_team'),
    path('teams/<int:team_id>/add_pokemon/<int:pokemon_id>/', team.add_to_team, name='add_to_team'),
    path('teams/<int:team_id>/remove_pokemon/<int:pokemon_id>/', team.remove_from_team, name='remove_from_team'),
    path('battle/', battle.battle, name='battle'),
    path('battle/team/<int:team_id>/', battle.get_battle_teams, name='get_battle_teams'),
    path('battle/start/<int:team_id>/', battle.start_battle, name='start_battle'),
    path('battle/action/<int:team_id>/', battle.action, name='action'),
    
    # API endpoints
    path('api/pokemon/search/', pokemon.pokemon_search_api, name='pokemon_search_api'),

    # Auth
    path('accounts/register/', user.register, name='register'),
    path('accounts/logout/', user.logout_view, name='logout'),
]
