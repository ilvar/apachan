from __future__ import unicode_literals

import datetime
import hashlib
import os
import random
import string

import re
from django.conf import settings
from django.db import models

from PIL import Image as PilImage, ImageDraw, ImageFont
import imagehash
import easy_thumbnails.files
from django.template.defaultfilters import striptags

from apa.utils import get_datetime, get_tz, to_datetime, CaptchaSineWarp
from newapa.models import RandomPack, RandomPackImage


class AntiDos(models.Model):
    ip_address = models.CharField(primary_key=True, max_length=24)
    last_access = models.IntegerField()
    hits_count = models.IntegerField()

    class Meta:
        db_table = 'anti_dos'


class BannedImages(models.Model):
    md5sum = models.CharField(primary_key=True, max_length=32)
    datetime = models.DateTimeField()

    class Meta:
        db_table = 'banned_images'


class BannedCookie(models.Model):
    cookie_id = models.CharField(max_length=64, db_index=True)
    datetime = models.DateTimeField(auto_now_add=True)


class CapLog(models.Model):
    keyword = models.CharField(max_length=32)
    comment_id = models.IntegerField(primary_key=True)
    datetime = models.IntegerField()

    class Meta:
        db_table = 'cap_log'


class Captcha(models.Model):
    image_name = models.CharField(primary_key=True, max_length=32)
    image_file = models.ImageField(upload_to='capture/base/', null=True)
    keyword = models.CharField(max_length=32)
    image_id = models.CharField(max_length=12, null=True, editable=False)
    last_updated = models.IntegerField(editable=False)
    num_used = models.IntegerField(editable=False, default=0)

    class Meta:
        db_table = 'capture'
        
    def __unicode__(self):
        return self.keyword
        
    def save(self, *args, **kwargs):
        if not self.image_name and self.image_file:
            self.image_name = os.path.basename(str(self.image_file))
        if not self.last_updated:
            self.invalidate(save=False)
        return super(Captcha, self).save(*args, **kwargs)
    
    def invalidate(self, save=False):
        self.last_updated = to_datetime()
        if save:
            self.save()
            
    def get_twisted_img(self):
        src_img = PilImage.open(self.image_file)
        pil_map = PilImage.new("RGBA", src_img.size, 0)
        random_grid = map(lambda x: (int(random.random() * 256), int(random.random() * 256), int(random.random() * 256), int(random.random() * 32 + 160)), [1] * src_img.size[0] * src_img.size[1])
        pil_map.putdata(random_grid)

        twisted_img = CaptchaSineWarp().render(src_img).convert('RGBA')
        return PilImage.composite(twisted_img, pil_map, pil_map)


class CheckedIp(models.Model):
    ip_address = models.CharField(primary_key=True, max_length=24)
    datetime = models.CharField(max_length=24, blank=True, null=True)

    class Meta:
        db_table = 'checked_ip'


class ComNoUp(models.Model):
    comment_id = models.IntegerField(primary_key=True)
    down = models.SmallIntegerField()

    class Meta:
        db_table = 'com_no_up'


class Comment(models.Model):
    comment_id = models.AutoField(primary_key=True)
    poster_id = models.IntegerField()
    cookie_id = models.CharField(max_length=64)
    image = models.ForeignKey('Image', max_length=12, blank=True, null=True, db_column='image_id')
    root_id = models.IntegerField()
    parent_id = models.IntegerField()
    title = models.ForeignKey('Title', db_column='title_id', null=True)
    datetime = models.IntegerField()
    rating = models.SmallIntegerField(db_index=True)
    picrand = models.SmallIntegerField()
    tcrc = models.IntegerField()
    captxt = models.CharField(max_length=16)
    text = models.TextField(blank=True, null=True)
    source = models.TextField(blank=True, null=True)
    deleted = models.BooleanField(default=False, db_index=True)

    class Meta:
        db_table = 'comments'

    def get_datetime(self):
        return get_datetime(self.datetime)

    def get_comments(self, new_on_top=False):
        comments = Comment.objects.filter(root_id=self.pk).exclude(pk=self.pk)
        comments = comments.exclude(deleted=True)
        comments = comments.exclude(rating__lt=0)
        comments = comments.select_related('image', 'title')
        ordering = new_on_top and '-datetime' or 'datetime'
        return comments.order_by(ordering)

    def is_necropost(self):
        try:
            last_cmt = Comment.objects.filter(root_id=self.pk).exclude(pk=self.pk).order_by('-datetime')[0]
        except IndexError:
            return False
        else:
            three_months_ago = to_datetime() - 90 * 86400
            return last_cmt.datetime < three_months_ago

    def get_picrand(self):
        if self.picrand:
            return RandomPackImage.objects.get(pk=self.picrand)
        else:
            return None

    def is_post(self):
        return self.parent_id == 0 or self.parent_id == self.root_id
    
    def get_page_title(self):
        if self.title and self.title.title and self.title.title.strip():
            return self.title.title
        else:
            txt = striptags(self.text)
            words = txt.split(" ")
            title = ""
            for i,w in enumerate(words[:7]):
                if len(title) + len(w) < 150:
                    title += " " + w
            return title[:150].strip()


class Cookies(models.Model):
    cookie_id = models.CharField(primary_key=True, max_length=6)
    creation_date = models.IntegerField()
    datetime = models.IntegerField()
    ban_votes = models.IntegerField()
    ua_crc = models.IntegerField()
    provider_crc = models.IntegerField()
    rnd_code = models.IntegerField()
    ip_address = models.CharField(max_length=23)

    class Meta:
        db_table = 'cookies'


class Image(models.Model):
    text_id = models.CharField(primary_key=True, max_length=12)
    entry_id = models.IntegerField()
    datetime = models.IntegerField()
    x_size = models.SmallIntegerField()
    y_size = models.SmallIntegerField()
    extension = models.CharField(max_length=5, db_column='extencion')
    md5sum = models.CharField(max_length=32)
    img_hash = models.CharField(max_length=255, null=True, editable=False, db_index=True)
    no_big_image = models.IntegerField(blank=True, null=True)
    poster_ip = models.CharField(max_length=23)
    uses = models.IntegerField(default=0)
    deleted = models.BooleanField(default=False)
    banned = models.BooleanField(default=False)

    class Meta:
        db_table = 'images'

    def get_datetime(self):
        return get_datetime(self.datetime)

    def get_path(self):
        str_dt = self.get_datetime().strftime("%Y%m/%d")
        return "%s/%s.%s" % (str_dt, self.text_id, self.extension or "jpg")

    def get_full_path(self):
        return os.path.join("images", self.get_path())

    def get_thumb_path(self):
        return os.path.join("thumbs", self.get_path())

    _preview_path = None
    def get_preview_path(self):
        if not self._preview_path:
            path = os.path.join("previews", self.get_path())
            if os.path.exists(os.path.join(settings.MEDIA_ROOT, path)):
                self._preview_path = path
        return self._preview_path

    def get_absolute_path(self):
        return os.path.join(settings.MEDIA_ROOT, self.get_full_path())

    def save(self, *args, **kwargs):
        if not self.img_hash:
            pil_img = PilImage.open(self.get_absolute_path())
            self.img_hash = imagehash.dhash(pil_img, 16)

        if self.get_datetime() > datetime.datetime.now(tz=get_tz()) - datetime.timedelta(0, 60):
            found_img = None
            try:
                found_img = Image.objects.filter(md5sum=self.md5sum).exclude(pk=self.pk)[0]
            except IndexError:
                pass

            try:
                found_img = Image.objects.filter(img_hash=self.img_hash).exclude(pk=self.pk)[0]
            except IndexError:
                pass

            if found_img:
                if self.get_absolute_path() != found_img.get_absolute_path():
                    os.remove(self.get_absolute_path())
                return found_img

        super(Image, self).save(*args, **kwargs)
        return self

    def generate_name(self, filename):
        if '.' not in filename:
            filename += ".jpg"

        ext = filename.rsplit('.')[-1].lower()

        if ext not in {"jpg", "jpeg", "gif", "png"}:
            ext = "jpg"

        new_fname = ''.join(random.sample(string.ascii_letters + string.digits, 12))
        return new_fname, ext

    def invalidate_datetime(self):
        if not self.datetime:
            self.datetime = to_datetime()

    def save_image(self, f):
        """

        :param f: UploadedFile
        :return:
        """
        self.invalidate_datetime()

        dt = datetime.datetime.fromtimestamp(self.datetime, tz=get_tz())

        today_path = os.path.join(dt.strftime("%Y%m"), dt.strftime("%d"))
        path = os.path.join('images', today_path)
        self.text_id, ext = self.generate_name(f.name)

        while os.path.exists(os.path.join(settings.MEDIA_ROOT, path, "%s.%s" % (self.text_id, ext))):
            self.text_id, ext = self.generate_name(f.name)

        final_fname = "%s.%s" % (self.text_id, ext)
        final_path = os.path.join(path, final_fname)
        full_final_path = os.path.join(settings.MEDIA_ROOT, final_path)

        hash = hashlib.md5()

        try:
            os.makedirs(os.path.dirname(full_final_path))
        except OSError:
            print
            pass

        with open(full_final_path, 'wb+') as destination:
            for chunk in f.chunks():
                destination.write(chunk)
                hash.update(chunk)

        img = PilImage.open(full_final_path)
        self.x_size, self.y_size = img.size

        self.extension = final_path.rsplit('.')[-1]
        self.md5sum = hash.hexdigest()

        thumber = easy_thumbnails.files.get_thumbnailer(open(full_final_path), relative_name=final_path)

        thumb = thumber.generate_thumbnail({'size': (200, 0), 'crop': 'smart', 'sharpen': True})
        try:
            os.makedirs(os.path.join(settings.MEDIA_ROOT, 'thumbs', today_path))
        except OSError:
            pass
        thumb.image.save(os.path.join(settings.MEDIA_ROOT, 'thumbs', today_path, final_fname))

        preview = thumber.generate_thumbnail({'size': (600, 600)})
        try:
            os.makedirs(os.path.join(settings.MEDIA_ROOT, 'previews', today_path))
        except OSError:
            pass

        preview_img = self.apply_watermark(preview.image)
        preview_img.save(os.path.join(settings.MEDIA_ROOT, 'previews', today_path, final_fname))

        self.apply_watermark(img).save(full_final_path)

    def apply_watermark(self, img):
        FONT = os.path.join(settings.STATIC_ROOT, 'Lato-Bold.ttf')
        HEIGHT = 16
        img = img.convert('RGB')
        with_watermark = PilImage.new('RGBA', (img.size[0], img.size[1] + HEIGHT), (0, 0, 0, 0))

        text = "APACHAN.NET"
        size = 8
        n_font = ImageFont.truetype(FONT, size)
        n_width, n_height = n_font.getsize(text)

        while n_height < HEIGHT:
            size += 1
            n_font = ImageFont.truetype(FONT, size)
            n_width, n_height = map(lambda i: i+2, n_font.getsize(text))

        draw = ImageDraw.Draw(with_watermark, 'RGBA')
        draw.rectangle((0, with_watermark.size[1] - HEIGHT) + with_watermark.size, fill=(0, 0, 0, 255))
        draw.text((with_watermark.size[0] - n_width, with_watermark.size[1] - (HEIGHT + n_height) / 2), text, font=n_font)

        with_watermark.paste(img, (0, 0))

        return with_watermark


class Inbox(models.Model):
    number = models.IntegerField(primary_key=True)
    datetime = models.IntegerField(blank=True, null=True)
    pass_field = models.CharField(db_column='pass', max_length=32, blank=True, null=True)  # Field renamed because it was a Python reserved word.
    text = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'inbox'


class IpCountryTable(models.Model):
    start_ip = models.IntegerField(primary_key=True)
    end_ip = models.IntegerField()
    country_code = models.CharField(max_length=2)

    class Meta:
        db_table = 'ip_country_table'


class Lenta(models.Model):
    category = models.ForeignKey('newapa.Category', on_delete=models.DO_NOTHING, db_column='category')
    root = models.OneToOneField(Comment, primary_key=True, db_column='root_id')
    sticker = models.SmallIntegerField(db_index=True)
    drowner = models.SmallIntegerField(db_index=True)
    roulette = models.SmallIntegerField()
    poll = models.SmallIntegerField()
    hidden = models.SmallIntegerField(db_index=True)
    replies = models.IntegerField()
    rating = models.IntegerField(default=0, editable=False, db_index=True)
    datetime = models.IntegerField(db_index=True)

    class Meta:
        db_table = 'lenta'
        index_together = [
            ["drowner", "hidden"],
            ["drowner", "hidden", "category"],
            ["drowner", "hidden", "datetime"],
            ["drowner", "hidden", "rating"],
            ["drowner", "hidden", "category", "sticker", "datetime"],
        ]

    def get_datetime(self):
        return get_datetime(self.datetime)


class Members(models.Model):
    member_id = models.AutoField(primary_key=True)
    rights = models.SmallIntegerField()
    last_view = models.IntegerField()
    last_visit = models.IntegerField()
    login = models.CharField(max_length=16)
    password = models.CharField(max_length=32)

    class Meta:
        db_table = 'members'


class Polls(models.Model):
    comment_id = models.IntegerField(primary_key=True)
    vote1 = models.SmallIntegerField(blank=True, null=True)
    vote2 = models.SmallIntegerField(blank=True, null=True)
    vote3 = models.SmallIntegerField(blank=True, null=True)
    vote4 = models.SmallIntegerField(blank=True, null=True)
    vote5 = models.SmallIntegerField(blank=True, null=True)

    class Meta:
        db_table = 'polls'


class ShowAsAd(models.Model):
    datetime = models.IntegerField()
    comment_id = models.IntegerField(primary_key=True)

    class Meta:
        db_table = 'show_as_ad'


class Spammers(models.Model):
    ip_address = models.CharField(primary_key=True, max_length=23)
    datetime = models.IntegerField()
    reason = models.TextField()

    class Meta:
        db_table = 'spammers'


class Sticker(models.Model):
    root_id = models.IntegerField(primary_key=True)
    category = models.IntegerField()

    class Meta:
        db_table = 'sticker'
        unique_together = (('category', 'root_id'),)


class Title(models.Model):
    title_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=80)

    class Meta:
        db_table = 'titles'

    def __unicode__(self):
        return self.title


class Votes(models.Model):
    comment_id = models.IntegerField()
    cookie_id = models.CharField(max_length=6)
    br_crc = models.IntegerField()
    ip_part = models.IntegerField()
    datetime = models.IntegerField()
    value = models.SmallIntegerField()

    class Meta:
        db_table = 'votes'
        unique_together = (('comment_id', 'cookie_id'),)


class WrongLogins(models.Model):
    ip_addr = models.CharField(primary_key=True, max_length=23)
    last_attempt = models.IntegerField()
    attempts_count = models.SmallIntegerField()

    class Meta:
        db_table = 'wrong_logins'
