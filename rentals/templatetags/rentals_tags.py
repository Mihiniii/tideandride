from decimal import Decimal, InvalidOperation

from django import template
from django.conf import settings

register = template.Library()


@register.filter
def money(value, show_currency=True):
    """3500.00 -> 'LKR 3,500'"""
    try:
        amount = Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        return value
    text = f"{amount:,.0f}"
    return f"{settings.SITE_CURRENCY} {text}" if show_currency else text


@register.filter
def times(value, factor):
    try:
        return Decimal(value) * Decimal(factor)
    except (InvalidOperation, TypeError, ValueError):
        return ""


@register.simple_tag(takes_context=True)
def query_with(context, **kwargs):
    """Current GET params with some keys replaced, e.g. {% query_with category='jeep' %}."""
    params = context["request"].GET.copy()
    params.pop("page", None)
    for key, value in kwargs.items():
        if value in (None, ""):
            params.pop(key, None)
        else:
            params[key] = value
    encoded = params.urlencode()
    return f"?{encoded}" if encoded else "?"
