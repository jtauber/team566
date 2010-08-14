from django.contrib import admin

from manoria import models


admin.site.register(models.Continent)
admin.site.register(models.ResourceKind)
admin.site.register(models.PlayerResourceCount,
    list_display = ["kind", "player", "count"]
)
admin.site.register(models.SettlementResourceCount,
    list_display = ["kind", "settlement", "count"]
)
