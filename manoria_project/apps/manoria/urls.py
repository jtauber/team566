from django.conf.urls.defaults import *


urlpatterns = patterns("",
    url(r"^players/player/(\d+)/$", "manoria.views.player_detail", name="player_detail"),
    url(r"^players/create/$", "manoria.views.player_create", name="player_create"),
    url(r"^settlements/settlement/(\d+)/$", "manoria.views.settlement_detail", name="settlement_detail"),
    url(r"^settlements/create/(\d+)/$", "manoria.views.settlement_create", name="settlement_create"),
    url(r"^buildings/building/(\d+)/$", "manoria.views.building_detail", name="building_detail"),
)