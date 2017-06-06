# coding=utf-8
import datetime
import random
import time

import markdown as markdown
import micawber
import re
import requests
import ipware.ip

from django import forms
from django.conf import settings
from django.core.files.base import ContentFile
from django.db.models import F
from django.template.defaultfilters import striptags

import apa.utils
from apa.models import Comment, Image, Title, Lenta, Captcha
from logs.models import Log
from newapa.models import RandomPack, Category


class BannedImageException(Exception):
    pass


class ImageGetter:
    cleaned_data = {}

    def get_img_rnd(self, rnd_field, rnd_generator, request):
        if self.cleaned_data[rnd_field]:
            result_img = None
            rnd = rnd_generator(self.cleaned_data[rnd_field])
        else:
            if self.cleaned_data['url']:
                response = requests.get(self.cleaned_data['url'])
                f = ContentFile(response.content, response.url.split('/')[-1])
            else:
                f = self.cleaned_data['upload']
            img = Image(**self.get_img_params(request))
            img.save_image(f)
            result_img = img.save()

            if result_img.banned:
                Log.write(Log.TYPE_VALIDATION, "This image is banned", request, request.POST)
                raise BannedImageException("This image is banned")

            Image.objects.filter(pk=result_img.pk).update(uses=F('uses') + 1)

            rnd = 0
        return result_img, rnd

    def get_session(self, request):
        return request.COOKIES[settings.SESSION_COOKIE_NAME]

    def get_img_params(self, request):
        return {
            'entry_id': 0,
            'poster_ip': ipware.ip.get_real_ip(request) or ipware.ip.get_ip(request) or "127.0.0.1"
        }


class TextValidationError(forms.ValidationError):
    pass


class TextProcessor():
    request = None
    cleaned_data = {}

    def clean_all(self, image_fields):
        if self.request.banned:
            Log.write(Log.TYPE_VALIDATION, "You are banned", self.request, self.request.POST)
            raise forms.ValidationError(u"Вы забанены")

        if self.request.wait_to_post:
            Log.write(Log.TYPE_VALIDATION, "You cannot post yet", self.request, self.request.POST)
            raise forms.ValidationError(u"Вы еще не можете оставлять посты")

        if image_fields and not any(self.cleaned_data.get(f) for f in image_fields):
            Log.write(Log.TYPE_VALIDATION, "Please provice an image", self.request, self.request.POST)
            raise forms.ValidationError(u"Необходимо указать картинку")

        text = self.cleaned_data.get('message', "").strip()
        if not text.strip():
            Log.write(Log.TYPE_VALIDATION, "Text is empty", self.request, self.request.POST)
            raise TextValidationError(u"Необходимо ввести текст")

        if len(text.strip()) > 2048:
            Log.write(Log.TYPE_VALIDATION, "text too long", self.request, self.request.POST)
            raise TextValidationError(u"Слишком много текста")

        if not self.request.user.is_staff:
            text_tokens = set(apa.utils.tokenize_text(text))
            yesterday_ts = apa.utils.to_datetime(datetime.datetime.now()) - 86400
            existing_messages = Comment.objects.filter(cookie_id=self.request.cookie_id, datetime__gte=yesterday_ts)
            for em in existing_messages:
                em_tokens = set(apa.utils.tokenize_text(em.text))
                diff = text_tokens.difference(em_tokens)
                if float(len(diff)) / len(text_tokens) < 0.2:
                    # More than 80% of text repeats
                    Log.write(Log.TYPE_VALIDATION, "Possible post duplicate", self.request, self.request.POST)
                    raise TextValidationError(u"Вы уже отправляли похожий пост недавно.")

            # lang, confidence = apa.utils.detect_language(text)
            # text_size = len(text_tokens)
            # word_len = len(text) / text_size
            # if lang != 'russian' or (text_size > 10 and confidence < text_size / 5) or text_size == 0 or word_len > 10:
            #     Log.write(Log.TYPE_VALIDATION, "Post does not look russian", self.request, self.request.POST)
            #     raise TextValidationError(u"Непонятно, пишите по-русски. И докажите, что вы не робот.")

        try:
            self.render_md(text)
        except RuntimeError, e:
            Log.write(Log.TYPE_VALIDATION, "Text exception: %s" % e, self.request, self.request.POST)
            raise TextValidationError(u"Некорректный текст")

        self.cleaned_data['message'] = text

        return self.cleaned_data

    def render_md(self, text):
        return markdown.markdown(text, [
            'newapa.markdown.extensions.links_proxy',
            'newapa.markdown.extensions.spoiler',
        ])

    def process(self, text):
        text = striptags(text)
        
        micawber_providers = micawber.bootstrap_basic()
        (_, extracted) = micawber.extract(text, micawber_providers)
        alt_title = None

        for url, data in extracted.items():
            text = re.sub("(\s|^)%s(\s|$)" % re.escape(url),
                          "\\1<a href=\"%(url)s\" target=\"_blank\">![%(title)s](%(thumbnail_url)s)</a>\\2" % data,
                          text)
            alt_title = data['title']

        md = self.render_md(text)

        return md, alt_title
    
    def get_random_captcha(self):
        return Captcha.objects.all().order_by('?')[0]


class NewThreadForm(forms.Form, ImageGetter, TextProcessor):
    title = forms.CharField(label=u'Заголовок (опционально)', required=False, max_length=255)
    category = forms.ModelChoiceField(label=u'Категория', required=True, queryset=Category.objects.none())
    message = forms.CharField(label=u'Сообщение (обязательно)', required=True, widget=forms.Textarea(attrs={"rows": 6}))
    roulette = forms.BooleanField(label=u'Рулетка-Тред (нельзя удалять свои сообщения)', required=False)
    upload = forms.ImageField(label=u'Или Изображение (Не больше 2х мегабайт)', required=False)
    url = forms.URLField(label=u'Или URL картинки сюда', required=False)

    def __init__(self, request, *args, **kwargs):
        self.request = request

        super(NewThreadForm, self).__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.all().order_by('name')

    def clean(self):
        return self.clean_all(['upload', 'url', 'roulette'])

    def get_random_random_pack(self):
        return random.choice(RandomPack.objects.all()).images.order_by('?')[0].pk

    def save(self):
        img, rnd = self.get_img_rnd('roulette', lambda any: self.get_random_random_pack(), self.request)
        content, alt_title = self.process(self.cleaned_data['message'])

        comment = Comment.objects.create(
            poster_id=0,
            cookie_id=self.get_session(self.request),
            image=img,
            root_id=0,
            parent_id=0,
            title=Title.objects.create(
                title=self.cleaned_data['title'] or alt_title or ""),
            datetime=apa.utils.to_datetime(),
            rating=-1,
            picrand=rnd,
            tcrc=0,
            captxt=self.get_random_captcha().keyword,
            source=self.cleaned_data['message'],
            text=content
        )
        Lenta.objects.create(
            category=self.cleaned_data.get('category', 6),
            root=comment,
            sticker=0,
            drowner=0,
            roulette=self.cleaned_data['roulette'],
            poll=0,
            hidden=1,
            replies=0,
            datetime=comment.datetime
        )
        return comment


class NewCommentForm(forms.Form, ImageGetter, TextProcessor):
    title = forms.CharField(label=u'Заголовок (опционально)', required=False, max_length=255)
    message = forms.CharField(label=u'Сообщение (обязательно)', required=True, widget=forms.Textarea(attrs={"rows": 6}))
    do_not_raise = forms.BooleanField(label=u'Не поднимать', required=False)
    upload = forms.ImageField(label=u'Изображение (Не больше 2х мегабайт)', required=False)
    url = forms.URLField(label=u'Или URL картинки сюда', required=False)
    random = forms.ModelChoiceField(label=u'Или рандом', queryset=RandomPack.objects.none(), required=False)
    parent = forms.IntegerField(widget=forms.HiddenInput, required=False)

    def __init__(self, request, *args, **kwargs):
        self.request = request

        super(NewCommentForm, self).__init__(*args, **kwargs)

        self.fields['random'].queryset = RandomPack.objects.all().order_by('title')

    def clean(self):
        return self.clean_all([])

    def save(self, thread):
        try:
            img, rnd = self.get_img_rnd('random', lambda rnd: rnd.images.order_by('?')[0].pk, self.request)
        except AttributeError:
            img, rnd = None, 0
        content, alt_title = self.process(self.cleaned_data['message'])

        kwargs = {}
        if not self.cleaned_data.get('do_not_raise'):
            kwargs.update({"datetime": apa.utils.to_datetime()})

        Lenta.objects.filter(root=thread).update(replies=F('replies') + 1, **kwargs)

        title = Title.objects.create(title=self.cleaned_data['title'] or alt_title or "")
        return Comment.objects.create(
            poster_id=0,
            cookie_id=self.get_session(self.request),
            image=img,
            root_id=thread.pk,
            parent_id=self.cleaned_data.get("parent") or thread.pk,
            title=title,
            datetime=apa.utils.to_datetime(),
            rating=-1,
            picrand=rnd,
            tcrc=0,
            captxt=self.get_random_captcha().keyword,
            source=self.cleaned_data['message'],
            text=content
        )
