from django.contrib import admin

from manoria import models


admin.site.register(models.Continent)
admin.site.register(models.ResourceKind)
admin.site.register(models.PlayerResourceCount,
    list_display = ["kind", "player", "count"]
)
admin.site.register(models.SettlementResourceCount,
    list_display = ["pk", "kind", "settlement", "count", "timestamp", "natural_rate", "rate_adjustment", "rate"]
)
admin.site.register(models.BuildingKind)
admin.site.register(models.BuildingCost,
    list_display = ["pk", "building_kind", "resource_kind", "amount"]
)
admin.site.register(models.BuildingKindProduct)
admin.site.register(models.SettlementBuilding)
admin.site.register(models.SettlementTerrainKind)
admin.site.register(models.SettlementTerrain)
admin.site.register(models.SettlementTerrainResourceCount,
    list_display = ["pk", "kind", "terrain", "count", "timestamp", "natural_rate", "rate_adjustment", "rate"]
)