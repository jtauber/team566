import datetime

from django.http import Http404
from django.template import RequestContext
from django.shortcuts import get_object_or_404, render_to_response, redirect

from django.contrib.auth.decorators import login_required

from manoria.forms import PlayerCreateForm, SettlementCreateForm, BuildingCreateForm
from manoria.models import Continent, Player, Settlement, SettlementBuilding, SettlementTerrain, ResourceKind, BuildingKind


def homepage(request):
    if request.user.is_authenticated():
        try:
            player = request.user.player
            return _player_detail(request, player)
        except Player.DoesNotExist:
            return player_create(request)
    
    ctx = RequestContext(request, {})
    return render_to_response("manoria/homepage.html", ctx)


def _player_detail(request, player):
    continent = get_object_or_404(Continent, pk=1)

    ctx = {
        "player": player,
        "continent": continent,
    }
    ctx = RequestContext(request, ctx)
    return render_to_response("manoria/player_detail.html", ctx)


@login_required
def player_create(request):
    if request.method == "POST":
        form = PlayerCreateForm(request.POST)
        
        if form.is_valid():
            player = form.save(commit=False)
            player.user = request.user
            player.save()
            
            for resource_kind in ResourceKind.objects.filter(player=True):
                player.playerresourcecount_set.create(
                    kind=resource_kind,
                    count=0,
                    natural_rate=0,
                    rate_adjustment=0,
                    limit=0,
                    timestamp=datetime.datetime.now(),
                )
            
            return redirect("home")
    else:
        form = PlayerCreateForm()
    
    ctx = {
        "form": form,
    }
    ctx = RequestContext(request, ctx)
    return render_to_response("manoria/player_create.html", ctx)


@login_required
def settlement_detail(request, pk):
    settlement = get_object_or_404(Settlement, pk=pk)
    
    if request.user != settlement.player.user:
        raise Http404
    
    ctx = {
        "settlement": settlement,
    }
    ctx = RequestContext(request, ctx)
    return render_to_response("manoria/settlement_detail.html", ctx)


@login_required
def settlement_create(request):
    player = request.user.player
    
    if request.method == "POST":
        form = SettlementCreateForm(request.POST)
        
        if form.is_valid():
            settlement = form.save(commit=False)
            
            settlement.player = player
            settlement.continent = Continent.objects.get(pk=1)
            
            settlement.place()
            
            return redirect("settlement_detail", settlement.pk)
    else:
        form = SettlementCreateForm()
    
    ctx = {
        "player": player,
        "form": form,
    }
    ctx = RequestContext(request, ctx)
    return render_to_response("manoria/settlement_create.html", ctx)


@login_required
def building_detail(request, pk):
    building = get_object_or_404(SettlementBuilding, pk=pk)
    
    if request.user != building.settlement.player.user:
        raise Http404
    
    ctx = {
        "building": building,
    }
    ctx = RequestContext(request, ctx)
    return render_to_response("manoria/building_detail.html", ctx)


@login_required
def building_create(request, settlement_pk):
    settlement = get_object_or_404(Settlement, pk=settlement_pk)
    
    def buildings():
        resource_counts = {}
        for resource_count in self.settlement.resource_counts():
            resource_counts[resource_count.kind] = resource_count
        for building_kind in BuildingKind.objects.all():
            d = {"building_kind": building_kind, "costs": []}
            for cost in building_kind.buildingcost_set.all():
                cost.sufficient = resource_counts[cost.resource_kind].count >= cost.amount
                d["costs"].append(cost)
            yield d
    
    if request.method == "POST":
        form = BuildingCreateForm(settlement, request.POST)
        
        if form.is_valid():
            building = form.save(commit=False)
            
            building.settlement = settlement
            
            building.queue()
            
            return redirect("settlement_detail", settlement.pk)
    else:
        x = request.GET.get("x")
        y = request.GET.get("y")
        initial = {}
        if x:
            initial["x"] = x
        if y:
            initial["y"] = y
        form = BuildingCreateForm(settlement, initial=initial)
    
    ctx = {
        "form": form,
        "settlement": settlement,
        "buildings": buildings(),
    }
    ctx = RequestContext(request, ctx)
    return render_to_response("manoria/building_create.html", ctx)


@login_required
def terrain_detail(request, pk):
    terrain = get_object_or_404(SettlementTerrain, pk=pk)
    
    if request.user != terrain.settlement.player.user:
        raise Http404
    
    ctx = {
        "terrain": terrain,
    }
    ctx = RequestContext(request, ctx)
    return render_to_response("manoria/terrain_detail.html", ctx)


def resource_kind_list(request):
    ctx = {
        "resource_kinds": ResourceKind.objects.all(),
    }
    ctx = RequestContext(request, ctx)
    return render_to_response("manoria/resource_kind_list.html", ctx)


def building_kind_list(request):
    ctx = {
        "building_kinds": BuildingKind.objects.all(),
    }
    ctx = RequestContext(request, ctx)
    return render_to_response("manoria/building_kind_list.html", ctx)


def terrain_kind_list(request):
    ctx = {
        "terrain_kinds": TerrainKind.objects.all(),
    }
    ctx = RequestContext(request, ctx)
    return render_to_response("manoria/terrain_kind_list.html", ctx)
