# coding=utf-8

import datetime
from django.core.management.base import BaseCommand

from django.contrib.sessions.models import Session


class Command(BaseCommand):
    help = 'Copy rating from Comment into lenta'

    def handle(self, *args, **options):
        all_sessions = Session.objects.all()
        all_cnt = all_sessions.count()
        print "Total count %s" % all_cnt

        batch_size = 10000

        for i in range(0, all_cnt / batch_size + 1):
            to_delete = []
            sessions = list(all_sessions[i*batch_size:(i+1)*batch_size])
            for s in sessions:
                if s.get_decoded().keys() == ['user_since']:
                    to_delete.append(s.pk)

            Session.objects.filter(pk__in=to_delete).delete()
            print "Batch %s completed, deleted %s of %s" % (i * batch_size, len(to_delete), len(sessions))