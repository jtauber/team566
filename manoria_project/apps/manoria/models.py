import datetime
import random

from django.db import models

from django.contrib.auth.models import User


class Player(models.Model):
    
    user = models.ForeignKey(User, related_name="players")
    name = models.CharField(max_length=20, unique=True)
    
    # @@@ points
    
    def __unicode__(self):
        return self.name


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
    
    def __unicode__(self):
        return u"%s (%s)" % (self.name, self.player)
    
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
    
    def build_queue(self):
        queue = SettlementBuilding.objects.filter(
            settlement=self,
            construction_end__gt=datetime.datetime.now()
        )
        queue = queue.order_by("construction_start")
        return queue
    
    def buildings(self):
        return SettlementBuilding.objects.filter(
            settlement=self,
            construction_end__lte=datetime.datetime.now()
        )


class ResourceKind(models.Model):
    
    name = models.CharField(max_length=25)
    
    def __unicode__(self):
        return self.name


class BaseResourceCount(models.Model):
    
    count = models.IntegerField(default=0)
    timestamp = models.DateTimeField(default=datetime.datetime.now)
    natural_rate = models.DecimalField(max_digits=7, decimal_places=1)
    rate_adjustment = models.DecimalField(max_digits=7, decimal_places=1)
    limit = models.IntegerField(default=0)
    
    class Meta:
        abstract = True
    
    @property
    def rate(self):
        return self.natural_rate + self.rate_adjustment
    
    def current(self):
        change = datetime.datetime.now() - self.timestamp
        amount = int(self.count + float(self.rate) * (change.days * 86400 + change.seconds) / 3600.0)
        if self.limit == 0:
            return max(0, amount)
        else:
            return min(max(0, amount), self.limit)


class PlayerResourceCount(BaseResourceCount):
    
    kind = models.ForeignKey(ResourceKind)
    player = models.ForeignKey(Player, related_name="resource_counts")
    
    class Meta:
        unique_together = [("kind", "player")]
    
    def __unicode__(self):
        return u"%s (%s)" % (self.kind, self.player)


class SettlementResourceCount(BaseResourceCount):
    
    kind = models.ForeignKey(ResourceKind)
    settlement = models.ForeignKey(Settlement, related_name="resource_counts")
    
    class Meta:
        unique_together = [("kind", "settlement")]
    
    def __unicode__(self):
        return u"%s (%s)" % (self.kind, self.settlement)


class BuildingKind(models.Model):
    
    name = models.CharField(max_length=30)
    
    def __unicode__(self):
        return self.name


class SettlementBuilding(models.Model):
    
    kind = models.ForeignKey(BuildingKind)
    settlement = models.ForeignKey(Settlement)
    
    # location in settlement
    x = models.IntegerField()
    y = models.IntegerField()
    
    # build queue
    construction_start = models.DateTimeField(default=datetime.datetime.now)
    construction_end = models.DateTimeField(default=datetime.datetime.now)
    
    class Meta:
        unique_together = [("settlement", "x", "y")]
    
    def __unicode__(self):
        return u"%s on %s" % (self.kind, self.settlement)
    
    def build(self, commit=True):
        try:
            oldest = self.settlement.build_queue().reverse()[0]
        except IndexError:
            oldest = None
        
        # @@@ hard-coded two minute build times
        if oldest:
            self.construction_start = oldest.construction_end
        else:
            self.construction_start = datetime.datetime.now()
        self.construction_end = self.construction_start + datetime.timedelta(minutes=2)
        
        if commit:
            self.save()


class SettlementTerrainKind(models.Model):
    
    name = models.CharField(max_length=50)
    buildable_on = models.BooleanField(default=True)
    
    def __unicode__(self):
        return self.name


class SettlementTerrain(models.Model):
    
    kind = models.ForeignKey(SettlementTerrainKind)
    settlement = models.ForeignKey(Settlement)
    
    # location in settlement
    x = models.IntegerField()
    y = models.IntegerField()
    
    def __unicode__(self):
        return u"%s on %s" % (self.kind, self.settlement)


class SettlementTerrainResourceCount(BaseResourceCount):
    
    terrain = models.ForeignKey(SettlementTerrain)
