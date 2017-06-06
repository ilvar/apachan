from django import template
from django.utils.safestring import mark_safe

import bleach


def bleach_text(dirty_html):
    ALLOWED_ATTRS = {u'a': [u'href', u'title'], u'img': ['alt', 'src', 'title']}
    ALLOWED_TAGS = [u'a', u'b', u'blockquote', u'code', u'em', u'i', u'li', u'ol', u'strong', 
    				u'ul', u'p', 'h1', 'h2', 'hr', 'img']

    return mark_safe(bleach.clean(dirty_html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS))

register = template.Library()
register.filter('bleach', bleach_text)