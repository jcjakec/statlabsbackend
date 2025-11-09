from django.db import models
from django_extensions.db.fields import AutoSlugField
# Game related models

# Developer and publisher models

class Company(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=200, db_index=True)
    slug = AutoSlugField(populate_from=['name'], db_index=True)

    def __str__(self):
        return self.name
    
    class Meta:
        indexes = [
            models.Index(fields=["name", "slug"]),
        ]
    

# Tag model
class Tag(models.Model):
    name = models.CharField(max_length=200, db_index=True)
    slug = AutoSlugField(populate_from=['name'], db_index=True)

    def __str__(self):
        return self.name
    
    class Meta:
        indexes = [
            models.Index(fields=["name", "slug"]),
        ]
    


# Central game model
class Game(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=200, db_index=True)
    description = models.TextField(null=True, blank=True)

    aliases = models.JSONField(null=True, blank=True)
    popularity = models.FloatField(null=True, blank=True, db_index=True)
    companies = models.ManyToManyField(Company, db_index=True)
    cover = models.URLField(null=True, blank=True)
    tags = models.ManyToManyField(Tag, db_index=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        indexes = [
            models.Index(fields=["name", "popularity"])
        ]
    


# Platform model 
class Platform(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


# Platform profile - game & platform link 
class GameInstance(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='game_instances')
    platform = models.ForeignKey(Platform, on_delete=models.CASCADE)
    uid = models.CharField(max_length=200, null=True, blank=True)
    url = models.URLField(null=True, blank=True)

    class Meta:
        unique_together = ["game", "platform"]

    def __str__(self):
        return self.game.name + " - " + self.platform.name
