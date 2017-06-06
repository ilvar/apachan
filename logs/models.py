from __future__ import unicode_literals

from django.db import models
from ipware.ip import get_ip


class Log(models.Model):
    TYPE_POST = "post"
    TYPE_VALIDATION = "validation"
    TYPES = (
        (TYPE_POST, TYPE_POST),
        (TYPE_VALIDATION, TYPE_VALIDATION),
    )
    
    cookie_id = models.CharField(max_length=255, editable=False)
    ip = models.CharField(max_length=255, editable=False)
    type = models.CharField(max_length=255, choices=TYPES, editable=False)
    dt = models.DateTimeField(auto_now_add=True, editable=False)
    message = models.CharField(max_length=255, editable=False)
    data = models.TextField(blank=True, editable=False)

    @staticmethod
    def write(type, message, request, data):
        Log.objects.create(cookie_id=request.cookie_id, ip=get_ip(request), type=type, message=message, data=data)