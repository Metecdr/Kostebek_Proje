from django import template

register = template.Library()

@register.filter
def split(value, key=','):
    """Virgül veya belirlenen anahtarla metni parçalar."""
    return value.split(key)