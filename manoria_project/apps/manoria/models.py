from django.db import models

from django.contrib.auth.models import User


class Player(models.Model):
    
    user = models.ForeignKey(User)
    name = models.CharField(max_length=20)
    
    # @@@ points


class Continent(models.Model):
    
    name = models.CharField(max_length=20)


class Settlement(models.Model):
    
    name = models.CharField(max_length=20)
    kind = models.CharField(
        max_length=1,
        choices=[
            ("homestead", "Homestead"),
            ("hamlet", "Hamlet"),
            ("village", "Village"),
            ("town", "Town"),
        ]
    )
    player = models.ForeignKey(Player)
    continent = models.ForeignKey(Continent)
    # location on continent
    x = models.IntegerField()
    y = models.IntegerField()
    
    # @@@ points
