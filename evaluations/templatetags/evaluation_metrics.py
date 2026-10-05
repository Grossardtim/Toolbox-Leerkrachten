from django import template

register = template.Library()


@register.filter
def out_of_100(metric):
    if not metric or not metric['count']:
        return None
    return metric['total'] / metric['maximum'] * 100
