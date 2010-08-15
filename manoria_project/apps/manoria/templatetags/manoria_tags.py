from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

from django.contrib.humanize.templatetags.humanize import intcomma


register = template.Library()


@register.inclusion_tag("manoria/_map.html")
def render_map(settlement):
    empty_cells = []
    allocation = [map(int, a.split(",")) for a in settlement.allocation.split()]
    for x in range(settings.SETTLEMENT_SIZE[0]):
        for y in range(settings.SETTLEMENT_SIZE[1]):
            if (x, y) in allocation:
                continue
            empty_cells.append((x*86, y*86))
    return {
        "settlement": settlement,
        "empty_cells": empty_cells,
    }


@register.inclusion_tag("manoria/_map_building.html")
def render_map_building(building):
    # building size + border + padding
    left = building.x * 86
    top = building.y * 86
    return {
        "building": building,
        "left": left,
        "top": top,
    }


@register.inclusion_tag("manoria/_map_terrain.html")
def render_map_terrain(terrain):
    # terrain size + border + padding
    left = terrain.x * 86
    top = terrain.y * 86
    return {
        "terrain": terrain,
        "left": left,
        "top": top,
    }


@register.inclusion_tag("manoria/_map_empty_cell.html")
def render_map_empty_cell(cell):
    return {
        "left": cell[0],
        "top": cell[1],
    }


@register.filter
def format_rate(i):
    if i > 0:
        ret = u"+%s" % intcomma(i)
    elif i < 0:
        ret = u"&minus;%s" % intcomma(abs(i))
    else:
        ret = "0"
    return mark_safe(ret)
