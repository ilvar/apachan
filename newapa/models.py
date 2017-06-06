from __future__ import unicode_literals

from django.db import models


class RandomPack(models.Model):
    title = models.CharField(max_length=255)

    def __unicode__(self):
        return self.title


class RandomPackImage(models.Model):
    pack = models.ForeignKey(RandomPack, related_name='images')
    image = models.ImageField(upload_to='random/new/')

    def __unicode__(self):
        return u"%s - %s" % (self.pack, self.image)


class RandomLogo(models.Model):
    image = models.ImageField(upload_to='random/logos/')

    def __unicode__(self):
        return u"%s" % self.image


class Category(models.Model):
    number = models.IntegerField(primary_key=True, db_index=True)
    code = models.CharField(max_length=25, db_index=True)
    name = models.CharField(max_length=255)
    description = models.TextField()

    def __unicode__(self):
        return self.name


class Favorite(models.Model):
    cookie_id = models.CharField(max_length=64, db_index=True)
    comment_id = models.IntegerField()
    datetime = models.DateTimeField(auto_now_add=True)


class ModerationLog(models.Model):
    moderator = models.CharField(max_length=64)
    action = models.CharField(max_length=64)
    comment_id = models.CharField(max_length=64)
    datetime = models.DateTimeField(auto_now_add=True)


class DisLike(models.Model):
    cookie_id = models.CharField(max_length=64, db_index=True)
    comment_id = models.IntegerField()
    datetime = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = (
            ('cookie_id', 'comment_id')
        )