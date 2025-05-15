from django import template
from django.utils.safestring import mark_safe
from django.template.loader import render_to_string

from menu.models import MenuItem

register = template.Library()


@register.filter
def dict_get(d, key):
    return d.get(key, [])


@register.inclusion_tag("menu/menu.html", takes_context=True)
def draw_menu(context, menu_name):
    """
    – Берём текущий request.path
    – С одним запросом вытаскиваем все пункты меню menu_name
    – Строим children_map {parent_id: [child1, child2…]}
    – Определяем активный пункт и его цепочку предков
    – Раскрываем предков + детей активного пункта (первый уровень)
    – Возвращаем только корни + вспомогательные структуры
    """

    request = context.get("request")
    if request is None:
        # Без request нет смысла определять активный пункт
        return ""
    path = request.path

    # 1 запрос: все пункты меню, упорядоченные
    items = list(
        MenuItem.objects
        .filter(menu__name=menu_name)
        .order_by("order")
    )

    # строим дерево
    children_map = {}
    for it in items:
        children_map.setdefault(it.parent_id, []).append(it)

    # находим активный элемент
    active = next((it for it in items if it.get_url() == path), None)
    active_id = active.id if active else None

    # собираем всех предков активного
    expanded = set()
    p = active
    while p:
        expanded.add(p.id)
        p = p.parent

    # раскрываем первый уровень детей активного
    if active:
        for child in children_map.get(active.id, []):
            expanded.add(child.id)

    for it in items:
       # присваиваем каждому элементу атрибут children
       it.sub_items = children_map.get(it.id, [])
    # корни
    roots = [it for it in items if it.parent_id is None]

    return {
        'menu_tree': roots,
        'children_map': children_map,
        'expanded_ids': expanded,
        'active_id': active.id if active else None,
    }
