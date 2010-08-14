from django import forms

from manoria.models import Player, Settlement, SettlementBuilding


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
    
    def clean(self):
        x = self.cleaned_data.get("x")
        y = self.cleaned_data.get("y")
        
        if x and y:
            if not 1 <= x <= 20 or not 1 <= y <= 20:
                raise forms.ValidationError("Building is not within map range")
        
        return self.cleaned_data
