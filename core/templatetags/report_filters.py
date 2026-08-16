from django import template

register = template.Library()


@register.filter
def clp(value):
    """Format a numeric value as CLP: integer with '.' thousands separator."""
    try:
        value = int(value)
    except (TypeError, ValueError):
        return value
    return f'${value:,}'.replace(',', '.')