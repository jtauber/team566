from django import forms

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
    
    def __init__(self, settlement, *args, **kwargs):
        self.settlement = settlement
        super(BuildingCreateForm, self).__init__(*args, **kwargs)
    
    def clean(self):
        x = self.cleaned_data.get("x")
        y = self.cleaned_data.get("y")
        
        if all([x, y]):
            if not 1 <= x <= 20 or not 1 <= y <= 20:
                raise forms.ValidationError("Building is not within map range")
            
            if SettlementBuilding.objects.filter(settlement=self.settlement, x=x, y=y).exists():
                raise forms.ValidationError("A building exists at this location")
            
            non_buildable_terrain = SettlementTerrain.objects.filter(
                settlement=self.settlement, x=x, y=y, buildable_on=False
            )
            if non_buildable_terrain.exists():
                raise forms.ValidationError("Building cannot be placed on non-buildable terrain")
        
        return self.cleaned_data
