from django.db import models
from django.contrib.auth.models import User



class Pokemon(models.Model):
    pokemon_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=100)
    types = models.JSONField()
    height = models.IntegerField()
    weight = models.IntegerField()
    stats = models.JSONField() 
    sprite_url = models.URLField()
    sprite_shiny_url = models.URLField(null=True, blank=True)
    abilities = models.JSONField(default=list)  
    base_experience = models.IntegerField(null=True)
    species_url = models.URLField(null=True, blank=True)

    def __str__(self):
        return self.name

    def get_types(self):
        if isinstance(self.types, list):
            return self.types
        elif isinstance(self.types, str):
            return [self.types]
        else:
            return [type_data['type']['name'] for type_data in self.types]

    class Meta:
        ordering = ['pokemon_id']

class Team(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    pokemon = models.ManyToManyField(Pokemon, through='TeamPokemon')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s team: {self.name}"

class TeamPokemon(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    pokemon = models.ForeignKey(Pokemon, on_delete=models.CASCADE)
    position = models.IntegerField() 

    class Meta:
        ordering = ['position']
        unique_together = [['team', 'position']]
