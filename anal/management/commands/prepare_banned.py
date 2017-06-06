# coding=utf-8
import csv
import datetime
from django.core.management.base import BaseCommand
from django.db.models import Min

from apa.models import Lenta, Comment


class Command(BaseCommand):
    help = 'Export banned texts'

    def handle(self, *args, **options):
        min_dt = Comment.objects.filter(deleted=True).using('experiments').aggregate(md=Min('datetime'))['md']
        
        result = csv.writer(open("texts.csv", "w"))
        all_comments = Comment.objects.filter(datetime__gt=min_dt).using('experiments')

        result.writerow(["Datetime", "Root", "Parent", "Text", "Deleted"])
        for c in all_comments.only('deleted', 'text', 'datetime', 'root_id', 'parent_id'):
            result.writerow([c.datetime, c.root_id, c.parent_id, c.text.encode('utf8'), c.deleted and 1 or 0])
        