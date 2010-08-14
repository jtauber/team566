from django import template


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
