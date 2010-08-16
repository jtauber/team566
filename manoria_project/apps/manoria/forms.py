from django import forms
from django.conf import settings

from manoria.models import Player, Settlement, SettlementBuilding, SettlementTerrain


class PlayerCreateForm(forms.ModelForm):
    
    class Meta:
        model = Player
        fields = ["name"]


class SettlementCreateForm(forms.ModelForm):
    
    class Meta:
        model = Settlement
        fields = ["name"]


class BuildingCreateForm(forms.ModelForm):
    
    class Meta:
        model = SettlementBuilding
        fields = ["kind", "x", "y"]
        widgets = {
            "kind": forms.HiddenInput,
            "x": forms.HiddenInput,
            "y": forms.HiddenInput,
        }
    
    def __init__(self, settlement, *args, **kwargs):
        self.settlement = settlement
        super(BuildingCreateForm, self).__init__(*args, **kwargs)
    
    def clean(self):
        SX, SY = settings.SETTLEMENT_SIZE
        
        x = self.cleaned_data.get("x")
        y = self.cleaned_data.get("y")
        
        if all([x, y]):
            if not 1 <= x <= SX or not 1 <= y <= SY:
                raise forms.ValidationError("Building is not within map range")
            
            if SettlementBuilding.objects.filter(settlement=self.settlement, x=x, y=y).exists():
                raise forms.ValidationError("A building exists at this location")
            
            non_buildable_terrain = SettlementTerrain.objects.filter(
                settlement=self.settlement, x=x, y=y, kind__buildable_on=False
            )
            if non_buildable_terrain.exists():
                raise forms.ValidationError("Building cannot be placed on non-buildable terrain")
        
        return self.cleaned_data
    
    def clean_kind(self):
        building_kind = self.cleaned_data["kind"]
        resource_counts = {}
        for resource_count in self.settlement.resource_counts():
            resource_counts[resource_count.kind] = resource_count
        failed = []
        for cost in building_kind.buildingcost_set.all():
            if resource_counts[cost.resource_kind].amount() < cost.amount:
                failed.append(cost.resource_kind)
        if failed:
            raise forms.ValidationError("Insufficient resources: %s" % ", ".join([k.name for k in failed]))
        return building_kind
