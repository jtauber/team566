import re

from django import forms

from manoria.models import Player, Settlement


class PlayerCreateForm(forms.ModelForm):
    
    class Meta:
        model = Player
        fields = ["name"]


class SettlementCreateForm(forms.ModelForm):
    
    class Meta:
        model = Settlement
        fields = ["name"]
