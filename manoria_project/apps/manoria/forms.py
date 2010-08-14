import re

from django import forms

from manoria.models import Player, Settlement


class PlayerCreateForm(forms.ModelForm):
    
    class Meta:
        model = Player
        fields = ["name"]
    
    def clean_name(self):
        value = self.cleaned_data["name"].strip()
        if not re.match(r"^\w+$", value):
            raise forms.ValidationError("Name must match \\w")
        return value


class SettlementCreateForm(forms.ModelForm):
    
    class Meta:
        model = Settlement
        fields = ["name"]
