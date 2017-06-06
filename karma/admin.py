from django.contrib import admin

from karma.models import LikeTransaction, CommentTransaction


admin.site.register(LikeTransaction)

admin.site.register(CommentTransaction)
