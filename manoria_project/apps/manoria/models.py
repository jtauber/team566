import collections
import datetime
import itertools
import random

from django.conf import settings
from django.db import models

from django.contrib.auth.models import User

from manoria.utils import weighted_choices


class Player(models.Model):
    
    user = models.ForeignKey(User, related_name="players")
    name = models.CharField(max_length=20, unique=True)
    
    # @@@ points
    
    def __unicode__(self):
        return self.name
    
    def resource_counts(self):
        # @@@ instance cache
        counts = []
        for row in self.playerresourcecount_set.distinct().values("kind"):
            kind = ResourceKind.objects.get(id=row["kind"])
            current = PlayerResourceCount.current(kind, player=self)
            counts.append(current)
        return counts


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
    
    allocation = models.TextField()
    
    # @@@ points
    
    def __unicode__(self):
        return u"%s (%s)" % (self.name, self.player)
    
    def place(self):
        CX, CY = settings.CONTINENT_SIZE
        SX, SY = settings.SETTLEMENT_SIZE
        # @@@ need to test if continent is full otherwise an infinite loop
        # will occur
        y = None
        while y is None:
            x = random.randint(1, CX)
            S = set(range(1, CY+1)) - set([s.y for s in Settlement.objects.filter(x=x)])
            if S:
                y = random.choice(list(S))
        self.x = x
        self.y = y
        self.save()
        
        for resource_kind in ResourceKind.objects.filter(player=False):
            self.settlementresourcecount_set.create(
                kind=resource_kind,
                count=0,
                natural_rate=0,
                rate_adjustment=0,
                timestamp=datetime.datetime.now(),
                limit=0,
            )
        
        def check_cell(settlement, x, y):
            if not 1 <= x <= SX or not 1 <= y <= SY:
                terrain = None
            else:
                try:
                    terrain = settlement.terrain.select_related("kind").get(x=x, y=y)
                except SettlementTerrain.DoesNotExist:
                    terrain = None
            return terrain
        
        allocation = []
        
        for i in range(settings.SETTLEMENT_RESOURCE_COUNT):
            occupied = True
            while occupied:
                x = random.randint(1, SX)
                y = random.randint(1, SY)
                # check if the randomly chosen x, y is not already occupied
                if not (x, y) in allocation:
                    break
            allocation.append((x, y))
            # check surrounding cells
            neighbors = [
                check_cell(self, x+1, y),
                check_cell(self, x-1, y),
                check_cell(self, x, y+1),
                check_cell(self, x, y-1),
                check_cell(self, x+1, y+1),
                check_cell(self, x-1, y-1),
                check_cell(self, x+1, y-1),
                check_cell(self, x-1, y+1),
            ]
            counts = collections.defaultdict(int)
            for neighbor in filter(bool, neighbors):
                counts[neighbor.kind.slug] += 1
            population = []
            for kind in SettlementTerrainKind.objects.all():
                population.append((kind, counts.get(kind.slug, 0) + 1))
            kind = weighted_choices(population, 1)[0]
            terrain = self.terrain.create(kind=kind, x=x, y=y)
            # create resource counts for what the terrain kind produces
            for resource_kind in kind.produces.all():
                count = random.randint(1, 50000)
                terrain.settlementterrainresourcecount_set.create(
                    kind=resource_kind,
                    count=count,
                    natural_rate=count / 100,
                    rate_adjustment=0,
                    timestamp=datetime.datetime.now(),
                    limit=count
                )
        
        self.allocation = " ".join(("%d,%d" % (x, y) for x, y in allocation))
        # for updating the allocation table
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
    
    def resource_counts(self):
        # @@@ instance cache
        counts = []
        for row in self.settlementresourcecount_set.distinct().values("kind"):
            kind = ResourceKind.objects.get(id=row["kind"])
            current = SettlementResourceCount.current(kind, settlement=self)
            counts.append(current)
        return counts


class ResourceKind(models.Model):
    
    name = models.CharField(max_length=25)
    slug = models.SlugField()
    player = models.BooleanField()
    
    def __unicode__(self):
        return self.name


def pairwise(iterable):
    """
    pulled from itertools recipes, but modified to return last item and None
    s -> (s0,s1), (s1,s2), (s2, s3), (s3, None)
    """
    a, b = itertools.tee(iterable)
    next(b, None)
    for a, b in itertools.izip(a, b):
        yield a, b
    yield b, None


class BaseResourceCount(models.Model):
    
    count = models.IntegerField(default=0)
    timestamp = models.DateTimeField(default=datetime.datetime.now)
    natural_rate = models.DecimalField(max_digits=7, decimal_places=1)
    rate_adjustment = models.DecimalField(max_digits=7, decimal_places=1)
    limit = models.IntegerField(default=0)
    
    class Meta:
        abstract = True
    
    @classmethod
    def current(cls, kind, **kwargs):
        when = kwargs.pop("when", datetime.datetime.now())
        lookup_params = {
            "kind": kind,
            "timestamp__lt": when,
        }
        lookup_params.update(kwargs)
        past = cls._default_manager.filter(**lookup_params).order_by("-timestamp")
        return past[0]
    
    @classmethod
    def calculate_extremum(cls, kind, **kwargs):
        current = cls.current(kind, **kwargs)
        del kwargs["when"]
        lookup_params = {
            "kind": kind,
            "timestamp__gte": current.timestamp,
        }
        lookup_params.update(kwargs)
        future_counts = cls._default_manager.filter(**lookup_params).order_by("timestamp")
        for a, b in pairwise(future_counts):
            if b is None:
                start, end = a.timestamp, None
            else:
                start, end = a.timestamp, b.timestamp
            count = a.count
            rate = a.rate
            limit = a.limit
            if a.rate < 0:
                # when the count will hit zero
                timestamp = start + datetime.timedelta(hours=(count / -float(rate)))
                if end is not None and timestamp > end:
                    continue
                return timestamp, False
            elif a.rate > 0:
                # when the count will hit the limit
                timestamp = start + datetime.timedelta(hours=((limit - count) / float(rate)))
                if end is not None and timestamp > end:
                    continue
                return timestamp, True
            else:
                continue
        return None, None
    
    @property
    def rate(self):
        return self.natural_rate + self.rate_adjustment
    
    def amount(self, when=None):
        if when is None:
            when = datetime.datetime.now()
        change = when - self.timestamp
        amt = int(self.count + float(self.rate) * (change.days * 86400 + change.seconds) / 3600.0)
        if self.limit == 0:
            return max(0, amt)
        else:
            return min(max(0, amt), self.limit)


class PlayerResourceCount(BaseResourceCount):
    
    kind = models.ForeignKey(ResourceKind)
    player = models.ForeignKey(Player)
    
    def __unicode__(self):
        return u"%s (%s)" % (self.kind, self.player)


class SettlementResourceCount(BaseResourceCount):
    
    kind = models.ForeignKey(ResourceKind)
    settlement = models.ForeignKey(Settlement)
    
    def __unicode__(self):
        return u"%s (%s)" % (self.kind, self.settlement)


class BuildingKind(models.Model):
    
    name = models.CharField(max_length=30)
    slug = models.SlugField()
    
    def __unicode__(self):
        return self.name


class BuildingKindProduct(models.Model):
    
    building_kind = models.ForeignKey(BuildingKind, related_name="products")
    resource_kind = models.ForeignKey(ResourceKind, related_name="produced_by")
    source_terrain_kind = models.ForeignKey("SettlementTerrainKind", null=True)
    base_rate = models.IntegerField()
    
    def __unicode__(self):
        bits = []
        bits.append("%s produces %s" % (self.building_kind, self.resource_kind))
        if self.source_terrain_kind:
            bits.append("from %s" % self.source_terrain_kind)
        bits.append("at %d/hr" % self.base_rate)
        return " ".join(bits)


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
    
    def queue(self, commit=True):
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
        
        self.settlement.allocation += "%s%d,%d" % (" ", self.x, self.y)
        self.settlement.save()
        
        for product in self.kind.products.all():
            current = SettlementResourceCount.current(
                product.resource_kind,
                settlement=self.settlement, when=self.construction_end
            )
            amount = current.amount(self.construction_end)
            src = SettlementResourceCount(
                kind=product.resource_kind,
                settlement=self.settlement,
                count=amount,
                timestamp=self.construction_end,
                natural_rate=current.natural_rate,
                rate_adjustment=current.rate_adjustment + product.base_rate,
                limit=0, # @@@ storage
            )
            src.save()
            
            terrain = SettlementTerrain.objects.filter(
                settlement=self.settlement, kind=product.source_terrain_kind
            )
            closest = sorted([
                (((self.x - t.x) ** 2) + ((self.y - t.y) ** 2), t)
                for t in terrain
            ])[0][1]
            current = SettlementTerrainResourceCount.current(
                product.resource_kind,
                terrain=closest, when=self.construction_end
            )
            amount = current.amount(self.construction_end)
            strc = SettlementTerrainResourceCount(
                kind=product.resource_kind,
                terrain=closest,
                count=amount,
                timestamp=self.construction_end,
                natural_rate=current.natural_rate,
                rate_adjustment=current.rate_adjustment - product.base_rate,
                limit=current.limit,
            )
            strc.save()
            when, hit_limit = SettlementTerrainResourceCount.calculate_extremum(
                closest.kind,
                terrain=closest, when=self.construction_end
            )
            # if when is None the terrain will never run out or hit a limit
            if when and not hit_limit:
                current = SettlementResourceCount.current(
                    product.resource_kind,
                    settlement=self.settlement, when=when
                )
                amount = current.amount(when)
                SettlementResourceCount(
                    kind=product.resource_kind,
                    settlement=self.settlement,
                    count=amount,
                    timestamp=when,
                    natural_rate=current.natural_rate,
                    rate_adjustment=current.rate_adjustment - product.base_rate,
                    limit=0, # @@@ storage
                ).save()
        
        if commit:
            self.save()
    
    def status(self):
        now = datetime.datetime.now()
        if self.construction_start > now:
            return "queued"
        elif self.construction_end > now:
            return "under construction"
        else:
            return "built"


class SettlementBuildingResourceCount(BaseResourceCount):
    
    building = models.ForeignKey(SettlementBuilding)


class SettlementTerrainKind(models.Model):
    
    name = models.CharField(max_length=50)
    slug = models.SlugField()
    buildable_on = models.BooleanField(default=True)
    produces = models.ManyToManyField(ResourceKind)
    
    def __unicode__(self):
        return self.name


class SettlementTerrain(models.Model):
    
    kind = models.ForeignKey(SettlementTerrainKind)
    settlement = models.ForeignKey(Settlement, related_name="terrain")
    
    # location in settlement
    x = models.IntegerField()
    y = models.IntegerField()
    
    def __unicode__(self):
        return u"%s on %s" % (self.kind, self.settlement)
    
    def resource_counts(self):
        # @@@ instance cache
        counts = []
        for row in self.settlementterrainresourcecount_set.distinct().values("kind"):
            kind = ResourceKind.objects.get(id=row["kind"])
            current = SettlementTerrainResourceCount.current(kind, terrain=self)
            counts.append(current)
        return counts


class SettlementTerrainResourceCount(BaseResourceCount):
    
    kind = models.ForeignKey(ResourceKind)
    terrain = models.ForeignKey(SettlementTerrain)
