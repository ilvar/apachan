# coding=utf-8

import datetime
from django.core.management.base import BaseCommand

from apa.models import Lenta, Comment


class Command(BaseCommand):
    help = 'Copy rating from Comment into lenta'

    def handle(self, *args, **options):
        for rating in range(-10, 100):
            if rating == 0:
                continue

            begin = datetime.datetime.now()
            all_comments = Comment.objects.filter(rating=rating, parent_id=0).values_list('pk', flat=True)
            Lenta.objects.filter(root__in=all_comments).update(rating=rating)
            print '%s ready' % rating, datetime.datetime.now() - begin

        all_comments = Comment.objects.filter(rating__gte=100).select_related('lenta')
        cnt = all_comments.count()
        begin = datetime.datetime.now()
        for i, c in enumerate(all_comments):
            Lenta.objects.filter(root=c.pk).update(rating=c.rating)
            if i % 1000 == 0:
                print "Done %s of %s - %s" % (i, cnt, datetime.datetime.now() - begin)

        all_comments = Comment.objects.filter(rating__lte=-10).select_related('lenta')
        cnt = all_comments.count()
        begin = datetime.datetime.now()
        for i, c in enumerate(all_comments):
            Lenta.objects.filter(root=c.pk).update(rating=c.rating)
            if i % 1000 == 0:
                print "Done %s of %s - %s" % (i, cnt, datetime.datetime.now() - begin)