from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('pokemon/<int:pokemon_id>/', views.pokemon_detail, name='pokemon_detail'),
    path('teams/', views.team_list, name='team_list'),
    path('teams/create/', views.create_team, name='create_team'),
    path('teams/<int:team_id>/delete/', views.delete_team, name='delete_team'),
    path('teams/<int:team_id>/add_pokemon/<int:pokemon_id>/', views.add_to_team, name='add_to_team'),
    path('teams/<int:team_id>/remove_pokemon/<int:pokemon_id>/', views.remove_from_team, name='remove_from_team'),
    path('battle/', views.battle, name='battle'),
    path('battle/team/<int:team_id>/', views.get_battle_teams, name='get_battle_teams'),
    path('battle/start/<int:team_id>/', views.start_battle, name='start_battle'),
    # API endpoints
    path('api/pokemon/search/', views.pokemon_search_api, name='pokemon_search_api'),
    # Auth
    path('accounts/register/', views.register, name='register'),
    path('accounts/logout/', views.logout_view, name='logout'),
]
