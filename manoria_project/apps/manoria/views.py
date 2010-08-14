from django.http import Http404
from django.template import RequestContext
from django.shortcuts import get_object_or_404, render_to_response, redirect

from django.contrib.auth.decorators import login_required

from manoria.forms import PlayerCreateForm, SettlementCreateForm
from manoria.models import Continent, Player, Settlement, SettlementBuilding


@login_required
def player_detail(request, pk):
    player = get_object_or_404(Player, pk=pk)
    
    if request.user != player.user:
        raise Http404
    
    ctx = {
        "player": player,
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
def settlement_create(request, player_pk):
    player = get_object_or_404(Player, pk=player_pk)
    
    if request.method == "POST":
        form = SettlementCreateForm(request.POST)
        
        if form.is_valid():
            settlement = form.save(commit=False)
            
            settlement.player = player
            settlement.continent = Continent.objects.get(pk=1)
            
            settlement.place()
            
            return redirect("player_detail", player.pk)
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
