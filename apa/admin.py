from django.contrib import admin

from apa.models import Image, Comment, Title, Lenta, Captcha

admin.site.register(Image)

class CommentAdmin(admin.ModelAdmin):
    raw_id_fields = ['image', 'title']

admin.site.register(Comment, CommentAdmin)

admin.site.register(Title)

class LentaAdmin(admin.ModelAdmin):
    raw_id_fields = ['root']

admin.site.register(Lenta, LentaAdmin)


class CaptchaAdmin(admin.ModelAdmin):
    readonly_fields = ['image_name']

admin.site.register(Captcha, CaptchaAdmin)