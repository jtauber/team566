from django import template


register = template.Library()


@register.inclusion_tag("manoria/_map.html")
def map(settlement):
    return {
        "settlement": settlement,
    }


@register.inclusion_tag("manoria/_map_building.html")
def map_building(building):
    left = building.x * 53
    top = building.y * 53
    return {
        "building": building,
        "left": left,
        "top": top,
    }
