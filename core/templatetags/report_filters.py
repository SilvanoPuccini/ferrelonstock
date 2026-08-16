from django import template

register = template.Library()


@register.filter
def clp(value):
    """Format a numeric value as CLP: rounded integer with '.' thousands separator."""
    try:
        value = int(round(value))
    except (TypeError, ValueError):
        return value
    sign = '-' if value < 0 else ''
    return f'{sign}${abs(value):,}'.replace(',', '.')