import datetime
import random

from django.db import models

from django.contrib.auth.models import User


class Player(models.Model):
    
    user = models.ForeignKey(User, related_name="players")
    name = models.CharField(max_length=20, unique=True)
    
    # @@@ points


class Continent(models.Model):
    
    name = models.CharField(max_length=20)
    
    def __unicode__(self):
        return self.name


class Settlement(models.Model):
    
    name = models.CharField(max_length=20)
    kind = models.CharField(
        max_length=15,
        choices=[
            ("homestead", "Homestead"),
            ("hamlet", "Hamlet"),
            ("village", "Village"),
            ("town", "Town"),
        ],
        default="homestead",
    )
    player = models.ForeignKey(Player, related_name="settlements")
    continent = models.ForeignKey(Continent)
    # location on continent
    x = models.IntegerField()
    y = models.IntegerField()
    
    # @@@ points
    
    def place(self, commit=True):
        # @@@ need to test if continent is full otherwise an infinite loop
        # will occur
        y = None
        while y is None:
            x = random.randint(1, 10)
            S = set(range(1, 11)) - set([s.y for s in Settlement.objects.filter(x=x)])
            if S:
                y = random.choice(list(S))
        self.x = x
        self.y = y
        if commit:
            self.save()


class ResourceKind(models.Model):
    
    name = models.CharField(max_length=25)


class BaseResourceCount(models.Model):
    
    count = models.IntegerField(default=0)
    timestamp = models.DateTimeField(default=datetime.datetime.now)
    rate = models.DecimalField(max_digits=7, decimal_places=1)
    limit = models.IntegerField(default=0)
    
    def current(self):
        change = datetime.datetime.now() - self.timestamp
        amount = count + rate * (change.days * 86400 + change.seconds) / 3600.0
        if limit == 0:
            return amount
        else:
            return min(amount, limit)
    
    class Meta:
        abstract = True


class PlayerResourceCount(BaseResourceCount):
    
    kind = models.ForeignKey(ResourceKind)
    player = models.ForeignKey(Player)


class SettlementResourceCount(BaseResourceCount):
    
    kind = models.ForeignKey(ResourceKind)
    settlement = models.ForeignKey(Settlement)
