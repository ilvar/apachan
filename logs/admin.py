from django.contrib import admin

from logs.models import Log


class LogAdmin(admin.ModelAdmin):
    list_display = ['type', 'message', 'cookie_id', 'dt']
    readonly_fields = ['type', 'message', 'cookie_id', 'dt', 'ip', 'data']

admin.site.register(Log, LogAdmin)
