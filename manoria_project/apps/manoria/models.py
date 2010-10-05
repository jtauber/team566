import collections
import datetime
import itertools
import random

from django.conf import settings
from django.db import models, transaction

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

from manoria.managers import KindManager, TileManager
from manoria.utils import weighted_choices

class Player(models.Model):
    """
    A single player associated to a User
    """
    
    user = models.OneToOneField(User)
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
    """
    A single continent in the world. Currently there is only one continent
    (Manoria).
    """
    
    name = models.CharField(max_length=20)
    allocation = models.TextField()
    
    def __unicode__(self):
        return self.name
    
    @property
    def size(self):
        """
        The size of the continent (currently stored in settings).
        """
        return settings.CONTINENT_SIZE
    
    def cells(self):
        """
        Method for yielding cells (settlements) used to render a map of the
        continent. A cell is largely a mapable object (any model with x, y
        fields)
        """
        for cell in self.settlement_set.all():
            yield cell


class BaseKind(models.Model):
    """
    An abstract base class for kinds of objects.
    """
    
    name = models.CharField(max_length=50)
    slug = models.SlugField()
    
    objects = KindManager()
    
    class Meta:
        abstract = True
    
    def __unicode__(self):
        return self.name
    
    def natural_key(self):
        return (self.slug,)


class Settlement(models.Model):
    """
    A single settlement which lives on a continent. A player has settlements,
    but the UI only allows creation of a single settlement.
    """
    
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
    
    @property
    def size(self):
        return settings.SETTLEMENT_SIZE
    
    def update_kind(self, commit=True):
        total = self.build_queue().count() + self.buildings().count()
        if total < 3:
            self.kind = "homestead"
        elif total < 10:
            self.kind = "hamlet"
        elif total < 20:
            self.kind = "village"
        else:
            self.kind = "town"
        if commit:
            self.save()
    
    @transaction.commit_on_success
    def place(self):
        """
        Logic for determining how to place itself on the continent.
        """
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
        
        # mark x,y used on the continent
        self.continent.allocation += "%s%d,%d" % (" ", x, y)
        self.continent.save()
        
        # create the resource counts which are non-player for the settlement
        for resource_kind in ResourceKind.objects.filter(player=False):
            self.settlementresourcecount_set.create(
                kind=resource_kind,
                count=1000,
                natural_rate=0,
                rate_adjustment=0,
                timestamp=datetime.datetime.now(),
                limit=0,
            )
        
        # the following code is a fairly trivial clustering algorithm which
        # checks neigbors for similar kinds and weights them in choosing what
        # the terrain will be placed as.
        #
        # it is updating an allocation table which is a denormalized way for
        # easily checking if a cell on the map is taken.
        
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
    
    def cells(self):
        """
        Method for yielding cells (buildings and terrains) used to render a
        map of the continent. A cell is largely a mapable object (any model
        with x, y fields)
        """
        cells = itertools.chain(
            self.build_queue(), self.buildings(), self.terrain.all()
        )
        for cell in cells:
            yield cell
    
    def build_queue(self):
        """
        Method for getting buildings which are not yet finished building
        (those which are construction_end in the future)
        """
        queue = SettlementBuilding.objects.filter(
            settlement=self,
            construction_end__gt=datetime.datetime.now()
        )
        queue = queue.order_by("construction_start")
        return queue
    
    def buildings(self):
        """
        Method for getting buildings which have already been built (those which
        have construction_end in the past or equal to now).
        """
        return SettlementBuilding.objects.filter(
            settlement=self,
            construction_end__lte=datetime.datetime.now()
        )
    
    def resource_counts(self):
        """
        Obtains all the resource counts for the unique kinds asociated to a
        settlement.
        """
        # @@@ instance cache
        counts = []
        for row in self.settlementresourcecount_set.distinct().values("kind"):
            kind = ResourceKind.objects.get(id=row["kind"])
            current = SettlementResourceCount.current(kind, settlement=self)
            counts.append(current)
        return counts


class ResourceKind(BaseKind):
    """
    As of DjangoDash 2010:
    
        * Wood
        * Stone
        * Iron
        * Wheat
        * Fish
        * Labour
        * Gold
    """
    
    player = models.BooleanField()


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
    """
    BaseResourceCount represents the fact that at a given time, an object will
    contain a certain amount of a certain resource and that amount is either
    increasing or decreasing at a particular rate.
    
    From a sequence of BaseResourceCounts for a particular resource on a
    particular object, the entire history and future of that resource count
    can be calculated.
    """
    
    count = models.IntegerField(default=0)
    timestamp = models.DateTimeField(default=datetime.datetime.now)
    natural_rate = models.DecimalField(max_digits=7, decimal_places=1)
    rate_adjustment = models.DecimalField(max_digits=7, decimal_places=1)
    limit = models.IntegerField(default=0)
    
    class Meta:
        abstract = True
    
    @classmethod
    def current(cls, kind, **kwargs):
        """
        Get the most recent (or based on a given when) what the current
        resource count object is for the resource of the given kind. Also,
        takes additional resource specific data for lookup.
        """
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
        """
        Find the next point in the future where the resources of the given
        kind with either hit their limit or run out.
        """
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
        """
        The current rate of which this count is growing or decreasing
        """
        return self.natural_rate + self.rate_adjustment
    
    def amount(self, when=None):
        """
        At the given time or now, return the amount of which this resource
        count is reporting. Normally called after getting the current resource
        count.
        """
        if when is None:
            when = datetime.datetime.now()
        change = when - self.timestamp
        amt = int(self.count + float(self.rate) * (change.days * 86400 + change.seconds) / 3600.0)
        if self.limit == 0:
            return max(0, amt)
        else:
            return min(max(0, amt), self.limit)


class PlayerResourceCount(BaseResourceCount):
    """
    A player resource count represents how much of a resource is associated
    to a player at any point in time.
    """
    
    kind = models.ForeignKey(ResourceKind)
    player = models.ForeignKey(Player)
    
    def __unicode__(self):
        return u"%s (%s)" % (self.kind, self.player)


class SettlementResourceCount(BaseResourceCount):
    """
    A settlement resource count represents how much of a resource is associated
    to a settlemnt at any point in time.
    """
    
    kind = models.ForeignKey(ResourceKind)
    settlement = models.ForeignKey(Settlement)
    
    def __unicode__(self):
        return u"%s (%s)" % (self.kind, self.settlement)


class BuildingKind(BaseKind):
    """
    As of DjangoDash 2010:
    
        * Cottage
        * Woodcutter's Hut
        * Fishing Hut
        * Iron Mine
        * Quarry
        * Farm
        * Gold Mine
    """
    
    build_time = models.IntegerField()
    tiles = generic.GenericRelation('Tile')


class BuildingCost(models.Model):
    """
    The cost of building an instance of a building kind.
    """
    
    building_kind = models.ForeignKey(BuildingKind)
    resource_kind = models.ForeignKey(ResourceKind)
    amount = models.IntegerField()
    
    def __unicode__(self):
        return u"%s costs %d of %s" % (self.building_kind, self.amount, self.resource_kind)


class BuildingRunningCost(models.Model):
    """
    A running cost to maintain an instance of a building kind.
    """
    
    building_kind = models.ForeignKey(BuildingKind)
    resource_kind = models.ForeignKey(ResourceKind)
    rate = models.DecimalField(max_digits=7, decimal_places=1)


class BuildingKindProduct(models.Model):
    """
    The resources a building produces and where it gets it from at some rate.
    """
    
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
    """
    A single building in a settlement.
    """
    
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
    
    @transaction.commit_on_success
    def queue(self):
        """
        Queues a building to be built.
        """
        # look for most recently added building to queue (None if none)
        try:
            oldest = self.settlement.build_queue().reverse()[0]
        except IndexError:
            oldest = None
        
        # set when construction starts based on the most recently added
        # building to the queue (if None use now)
        # @@@ hard-coded two minute build times
        if oldest:
            self.construction_start = oldest.construction_end
        else:
            self.construction_start = datetime.datetime.now()
        self.construction_end = self.construction_start + datetime.timedelta(seconds=self.kind.build_time)
        
        self.save()
        
        self.settlement.update_kind(commit=False)
        
        # allocate space on the map using settlement allocation table
        self.settlement.allocation += "%s%d,%d" % (" ", self.x, self.y)
        self.settlement.save()
        
        # deduct what the building costs
        for cost in self.kind.buildingcost_set.all():
            current = SettlementResourceCount.current(cost.resource_kind, settlement=self.settlement)
            future = SettlementResourceCount.objects.filter(
                kind=cost.resource_kind,
                settlement=self.settlement,
                timestamp__gt=datetime.datetime.now()
            )
            SettlementResourceCount.objects.filter(
                id__in=[rc.id for rc in itertools.chain([current], future)]
            ).update(count=models.F("count") - cost.amount)
        
        # handle the running costs of the building once it is finished
        # being built.
        for running_cost in self.kind.buildingrunningcost_set.all():
            current = SettlementResourceCount.current(running_cost.resource_kind,
                settlement=self.settlement, when=self.construction_end
            )
            SettlementResourceCount.objects.create(
                kind=running_cost.resource_kind,
                settlement=self.settlement,
                timestamp=self.construction_end,
                natural_rate=current.natural_rate,
                rate_adjustment=current.rate_adjustment - running_cost.rate,
                count=current.amount(when=self.construction_end)
            )
            future = SettlementResourceCount.objects.filter(
                kind=running_cost.resource_kind,
                settlement=self.settlement,
                timestamp__gt=self.construction_end
            )
            SettlementResourceCount.objects.filter(
                id__in=[rc.id for rc in future]
            ).update(rate_adjustment=models.F("rate_adjustment") - running_cost.rate)
        
        SX, SY = settings.SETTLEMENT_SIZE
        
        def check_cell(settlement, x, y, **kwargs):
            if not 1 <= x <= SX or not 1 <= y <= SY:
                terrain = None
            else:
                try:
                    terrain = settlement.terrain.filter(**kwargs).select_related("kind")
                    terrain = terrain.get(x=x, y=y)
                except SettlementTerrain.DoesNotExist:
                    terrain = None
            return terrain
        
        # iterate over what the building kind produces setting up the state
        # of resource counts when the building will be finished building
        for product in self.kind.products.all():
            # establish some common params used while creating resource counts
            common_params = {}
            if product.resource_kind.player:
                ResourceCount = PlayerResourceCount
                common_params["player"] = self.settlement.player
            else:
                ResourceCount = SettlementResourceCount
                common_params["settlement"] = self.settlement
            
            # adjust the settlement/player resource count based on what the building
            # will produce in the best case scenario.
            lookup_params = {
                "when": self.construction_end,
            }
            lookup_params.update(common_params)
            current = ResourceCount.current(product.resource_kind, **lookup_params)
            create_kwargs = {
                "kind": product.resource_kind,
                "count": current.amount(self.construction_end),
                "timestamp": self.construction_end,
                "natural_rate": current.natural_rate,
                "rate_adjustment": current.rate_adjustment + product.base_rate,
                "limit": 0, # @@@ storage
            }
            create_kwargs.update(common_params)
            ResourceCount.objects.create(**create_kwargs)
            
            if product.source_terrain_kind:
                
                # look for terrains which are adjacent and of the correct
                # kind and adjust rates of each
                
                x, y = self.x, self.y
                
                neighbors = filter(bool, [
                    check_cell(self.settlement, x+1, y, kind=product.source_terrain_kind),
                    check_cell(self.settlement, x-1, y, kind=product.source_terrain_kind),
                    check_cell(self.settlement, x, y+1, kind=product.source_terrain_kind),
                    check_cell(self.settlement, x, y-1, kind=product.source_terrain_kind),
                    check_cell(self.settlement, x+1, y+1, kind=product.source_terrain_kind),
                    check_cell(self.settlement, x-1, y-1, kind=product.source_terrain_kind),
                    check_cell(self.settlement, x+1, y-1, kind=product.source_terrain_kind),
                    check_cell(self.settlement, x-1, y+1, kind=product.source_terrain_kind),
                ])
                
                for neighbor in neighbors:
                    # when the building finishes set what affect it will have on the
                    # terrain resource count
                    current = SettlementTerrainResourceCount.current(
                        product.resource_kind,
                        terrain=neighbor, when=self.construction_end
                    )
                    SettlementTerrainResourceCount.objects.create(
                        kind=product.resource_kind,
                        terrain=neighbor,
                        count=current.amount(self.construction_end),
                        timestamp=self.construction_end,
                        natural_rate=current.natural_rate,
                        rate_adjustment=current.rate_adjustment - (product.base_rate / len(neighbors)),
                        limit=current.limit,
                    )
                    
                    # determine *when* the terrain will either run out or hit its
                    # limit based on its current rate and if the terrain will hit
                    # zero by the time the building finishes we need to adjust how
                    # it affects the settlement resource counts
                    when, hit_limit = SettlementTerrainResourceCount.calculate_extremum(
                        product.resource_kind,
                        terrain=neighbor, when=self.construction_end
                    )
                    # if when is None the terrain will never run out or hit a limit
                    if when and not hit_limit:
                        lookup_params = {
                            "when": when,
                        }
                        lookup_params.update(common_params)
                        current = ResourceCount.current(product.resource_kind, **lookup_params)
                        create_kwargs = {
                            "kind": product.resource_kind,
                            "settlement": self.settlement,
                            "count": current.amount(when),
                            "timestamp": when,
                            "natural_rate": current.natural_rate,
                            "rate_adjustment": current.rate_adjustment - product.base_rate,
                            "limit": 0, # @@@ storage
                        }
                        create_kwargs.update(common_params)
                        ResourceCount.objects.create(**create_kwargs)
    
    def status(self):
        now = datetime.datetime.now()
        if self.construction_start > now:
            return "queued"
        elif self.construction_end > now:
            return "under construction"
        else:
            return "built"


class SettlementBuildingResourceCount(BaseResourceCount):
    """
    A settlement building resource count represents how much of a resource
    is associated to a settlemnt at any point in time (to be used for storage).
    
    Decided to punt on this to finish for the DjangoDash 2010.
    """
    
    building = models.ForeignKey(SettlementBuilding)


class SettlementTerrainKind(BaseKind):
    """
    As of DjangoDash 2010:
    
        * Forest
        * Lake
        * Hill
        * Mountain
    """
    
    buildable_on = models.BooleanField(default=True)
    produces = models.ManyToManyField(ResourceKind)
    tiles = generic.GenericRelation('Tile')


class SettlementTerrain(models.Model):
    """
    An instance of a SettlementTerrainKind in a settlement.
    """
    
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
    """
    A settlement terrain resource count represents how much of a resource
    is associated to a settlement terrain at any point in time. Used for
    tracking what buildings have affect on terrain and how much they can
    provide.
    """
    
    kind = models.ForeignKey(ResourceKind)
    terrain = models.ForeignKey(SettlementTerrain)
    

class TileClass(BaseKind):
    def __unicode__(self):
        return self.slug   
       
       
class Tile(BaseKind):
    
    continent = models.ForeignKey(Continent)
    content_type = models.ForeignKey(ContentType, limit_choices_to = {"model__in": ("settlementterrainkind", "buildingkind")})
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')
    filename = models.CharField(max_length = 32)
    cls = models.ForeignKey(TileClass, verbose_name = u'class')

    objects = TileManager()

    def __unicode__(self):
        return self.slug
