from django.db import models


class KindManager(models.Manager):
    
    def get_by_natural_key(self, slug):
        return self.get(slug=slug)
