from django.conf.urls.defaults import *


urlpatterns = patterns("",
    url(r"^$", "manoria.views.homepage", name="home"),
    
    url(r"^players/create/$", "manoria.views.player_create", name="player_create"),
    
    url(r"^settlements/settlement/(\d+)/$", "manoria.views.settlement_detail", name="settlement_detail"),
    url(r"^settlements/create/$", "manoria.views.settlement_create", name="settlement_create"),
    
    url(r"^buildings/building/(\d+)/$", "manoria.views.building_detail", name="building_detail"),
    url(r"^buildings/create/(\d+)/$", "manoria.views.building_create", name="building_create"),
    
    url(r"^terrain/terrain/(\d+)/$", "manoria.views.terrain_detail", name="terrain_detail"),
    
    url(r"^leaderboard/$", "manoria.views.leaderboard", name="leaderboard"),
    
    url(r"^ajax_resource_count/(\d+)/$", "manoria.views.ajax_resource_count", name="ajax_resource_count"),
    url(r"^fragment_resource_count/(\d+)/$", "manoria.views.fragment_resource_count", name="fragment_resource_count"),
    url(r"^fragment_build_queue/(\d+)/$", "manoria.views.fragment_build_queue", name="fragment_build_queue"),
    url(r"^fragment_settlement_map/(\d+)/$", "manoria.views.fragment_settlement_map", name="fragment_settlement_map"),
    
    url(r"^help/$", "manoria.views.resource_kind_list", name="help_index"),
    url(r"^help/terrain/$", "manoria.views.terrain_kind_list", name="help_terrain"),
    url(r"^help/resources/$", "manoria.views.resource_kind_list", name="help_resources"),
    url(r"^help/buildings/$", "manoria.views.building_kind_list", name="help_buildings"),
)