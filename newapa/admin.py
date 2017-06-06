from django.contrib import admin

from newapa.models import RandomPack, RandomPackImage, Category, RandomLogo, ModerationLog


class RandomPackImageInline(admin.TabularInline):
    model = RandomPackImage


class RandomPackAdmin(admin.ModelAdmin):
    inlines = [RandomPackImageInline]

admin.site.register(RandomPack, RandomPackAdmin)

class CategoryAdmin(admin.ModelAdmin):
    pass

admin.site.register(Category, CategoryAdmin)

admin.site.register(RandomLogo)


class ModerationLogAdmin(admin.ModelAdmin):
    readonly_fields = ['moderator', 'action', 'comment_id', 'datetime']
    list_display = ['moderator', 'action', 'comment_link', 'datetime']

    def comment_link(self, log):
        return '<a href="/%s.html" target="_blank">#%s</a>' % (log.comment_id, log.comment_id)
    comment_link.allow_tags = True


admin.site.register(ModerationLog, ModerationLogAdmin)