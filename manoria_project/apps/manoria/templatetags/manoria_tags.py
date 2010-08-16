import itertools

from django import template
from django.conf import settings
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from django.contrib.humanize.templatetags.humanize import intcomma

from manoria.models import Continent, Settlement, SettlementBuilding, SettlementTerrain


register = template.Library()


class EmptyCell(object):
    def __init__(self, x, y, mapable):
        self.x = x
        self.y = y
        self.mapable = mapable
    
    def create_url(self):
        if isinstance(self.mapable, Continent):
            # return reverse("settlement_create")
            return None
        elif isinstance(self.mapable, Settlement):
            return reverse("building_create", args=(self.mapable.pk,))


@register.inclusion_tag("manoria/_map.html")
def render_map(mapable):
    empty_cells = []
    allocation = [map(int, a.split(",")) for a in mapable.allocation.split()]
    for x in range(1, mapable.size[0]+1):
        for y in range(1, mapable.size[1]+1):
            if (x, y) in allocation:
                continue
            empty_cells.append(EmptyCell(x, y, mapable))
    return {
        "mapable": mapable,
        "cells": itertools.chain(empty_cells, mapable.cells()),
    }


class RenderMapCellNode(template.Node):
    
    @classmethod
    def handle_token(cls, parser, token):
        bits = token.split_contents()
        return cls(bits[1])
    
    def __init__(self, cell):
        self.cell = template.Variable(cell)
    
    def render(self, context):
        cell = self.cell.resolve(context)
        
        ctx = {
            "cell": cell,
            # building size + border + padding
            "left": cell.x * 86,
            "top": cell.y * 86,
        }
        template = {
            EmptyCell: "_map_empty_cell.html",
            Settlement: "_map_settlement.html",
            SettlementBuilding: "_map_building.html",
            SettlementTerrain: "_map_terrain.html"
        }[type(cell)]
        
        if isinstance(cell, EmptyCell):
            ctx["create_url"] = cell.create_url()
        
        return render_to_string("manoria/%s" % template, ctx)


@register.tag
def render_map_cell(parser, token):
    return RenderMapCellNode.handle_token(parser, token)


@register.filter
def format_rate(i):
    if i > 0:
        ret = u"+%s" % intcomma(i)
    elif i < 0:
        ret = u"&minus;%s" % intcomma(abs(i))
    else:
        ret = "0"
    return mark_safe(ret)
