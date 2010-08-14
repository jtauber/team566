from django.http import Http404
from django.template import RequestContext
from django.shortcuts import get_object_or_404, render_to_response, redirect

from django.contrib.auth.decorators import login_required

from manoria.forms import PlayerCreateForm, SettlementCreateForm
from manoria.models import Continent, Player, Settlement


@login_required
def player_detail(request, name):
    player = get_object_or_404(Player, name=name)
    
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
def settlement_create(request, player_id):
    player = get_object_or_404(Player, id=player_id)
    
    if request.method == "POST":
        form = SettlementCreateForm(request.POST)
        
        if form.is_valid():
            settlement = form.save(commit=False)
            
            settlement.player = player
            settlement.continent = Continent.objects.get(pk=1)
            
            settlement.place()
            
            return redirect("player_detail", player.name)
    else:
        form = SettlementCreateForm()
    
    ctx = {
        "player": player,
        "form": form,
    }
    ctx = RequestContext(request, ctx)
    return render_to_response("manoria/settlement_create.html", ctx)
