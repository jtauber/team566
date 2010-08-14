from django import forms

from manoria.models import Player


class PlayerCreateForm(forms.ModelForm):
    
    class Meta:
        model = Player
        fields = ["name"]
