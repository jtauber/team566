from django import template
from django.utils.safestring import mark_safe

from django.contrib.humanize.templatetags.humanize import intcomma


register = template.Library()


@register.inclusion_tag("manoria/_map.html")
def map(settlement):
    return {
        "settlement": settlement,
    }


@register.inclusion_tag("manoria/_map_building.html")
def map_building(building):
    # building size + border + padding
    left = building.x * 86
    top = building.y * 86
    return {
        "building": building,
        "left": left,
        "top": top,
    }


@register.inclusion_tag("manoria/_map_terrain.html")
def map_terrain(terrain):
    # terrain size + border + padding
    left = terrain.x * 86
    top = terrain.y * 86
    return {
        "terrain": terrain,
        "left": left,
        "top": top,
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
