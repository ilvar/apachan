import random

from django.db import models
import koremutake

import apa.utils


class Inbox(models.Model):
    cookie_id = models.CharField(max_length=64)
    code = models.CharField(max_length=255, db_index=True, primary_key=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now_add=True, db_index=True)
    read = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.code:
            code = random.randint(100000000, 99999999999)
            self.code = koremutake.encode(code)
        return super(Inbox, self).save(*args, **kwargs)

    def get_messages(self):
        return self.message_set.all().order_by('-created')

    def get_unread_count(self):
        if getattr(self, '_unread_count', None) is None:
            self._unread_count = self.get_messages().filter(read__isnull=True).count()
        return self._unread_count

    def mark_read(self):
        import datetime
        return self.get_messages().update(read=datetime.datetime.now(tz=apa.utils.get_tz()))


class Message(models.Model):
    inbox = models.ForeignKey(Inbox)
    cookie_id = models.CharField(max_length=64)
    message = models.TextField()
    created = models.DateTimeField(auto_now_add=True, db_index=True)
    read = models.DateTimeField(blank=True, null=True, db_index=True)