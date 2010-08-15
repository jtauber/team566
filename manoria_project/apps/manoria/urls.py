from django.conf.urls.defaults import *


urlpatterns = patterns("",
    url(r"^$", "manoria.views.homepage", name="home"),
    
    url(r"^players/create/$", "manoria.views.player_create", name="player_create"),
    
    url(r"^settlements/settlement/(\d+)/$", "manoria.views.settlement_detail", name="settlement_detail"),
    url(r"^settlements/create/$", "manoria.views.settlement_create", name="settlement_create"),
    
    url(r"^buildings/building/(\d+)/$", "manoria.views.building_detail", name="building_detail"),
    url(r"^buildings/create/(\d+)/$", "manoria.views.building_create", name="building_create"),
    
    url(r"^terrain/terrain/(\d+)/$", "manoria.views.terrain_detail", name="terrain_detail"),
    
    url(r"^resource_kinds/$", "manoria.views.resource_kind_list", name="resource_kind_list"),
)