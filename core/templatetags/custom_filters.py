from django import template

register = template.Library()


@register.filter
def divide_by_thousand(value):
    """
    Divides a value by 1000 and removes decimal points.
    Used for currency conversion after government removed 3 zeros.
    Example: 50000 -> 50, 1000 -> 1
    """
    try:
        num = float(value)
        result = int(num / 1000)
        return result
    except (ValueError, TypeError):
        return value
