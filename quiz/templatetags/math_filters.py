from django import template

register = template.Library()

@register.filter
def mul(value, arg):
    """Çarpma işlemi"""
    try:
        return int(value) * int(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def div(value, arg):
    """Bölme işlemi"""
    try:
        return int(value) / int(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def sub(value, arg):
    """Çıkarma işlemi"""
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def add_custom(value, arg):
    """Toplama işlemi"""
    try:
        return int(value) + int(arg)
    except (ValueError, TypeError):
        return 0