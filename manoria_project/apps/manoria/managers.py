import os.path
from random import randint

from django.conf import settings
from django.db import models
from django.utils.functional import curry

TILES_URL = getattr(settings, 'TILES_URL', os.path.join(settings.MEDIA_URL, 'img', 'tiles'))


class KindManager(models.Manager):
    
    def get_by_natural_key(self, slug):
        return self.get(slug=slug)


class TileManager(models.Manager):
    def get_random_tile(self):
        num_tiles = self.count()
        return os.path.join(TILES_URL, self.all()[randint(0, num_tiles-1)].filename)

    def _get_random_CLASS_tile(self, tile_class):
        qs = self.filter(cls=tile_class)
        num_tiles = qs.count()
        if qs:
            return os.path.join(TILES_URL, qs[randint(0, num_tiles-1)].filename)
        else:
            return ''
 
    def add_accessor_methods(self, *args, **kwargs):
        from models import TileClass
        for cls in TileClass.objects.all():
            if not hasattr(self, 'get_random_%s_tile' % cls):
                setattr(self, 'get_random_%s_tile' % cls, curry(self._get_random_CLASS_tile, tile_class=cls))
    
    def __init__(self, *args, **kwargs):
        self.add_accessor_methods()
        super(TileManager, self).__init__(*args, **kwargs)
