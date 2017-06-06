# coding=utf-8
import os

from django.core.management.base import BaseCommand

from apa.models import Image
from newapa.models import Category


class Command(BaseCommand):
    help = 'Creates Django models for categories'

    def handle(self, *args, **options):
        cats = [
            "b;0;Бред;Психи и маньяки интернета. <br/><small class=\"text-danger\">Для постинга гомосятины, пиздостраданий и политоты предназначены, соответственно, Помойка, ЕОТ и Политота. В /b/ за это выдаётся бан.</small>",
            "c;1;Общий;Умиротворение, душевность, понимание.",
            "i;2;Политота; Ватопатриоты и либерофашисты.",
            "r;3;Request; Крики о помощи.",
            "vk;4;Вконтакте; Всё, что касается социальных сетей и тупого трололо в них.",
            "a;5;Ня-Ня;",
            "gay;6;Гей-гетто; Зона толерантности и мультикультурализма.",
            #"b7;7;Бред+",
            "med;8;Медиа; Игры, Кино, Музыка.",
            "prg;9;Программирование; и говнокодинг",
            "eot;10;Есть Одна Тян; О бабах. Фап-контент и пиздострадания.",
            # "all;11;Все в одном",
            "new;12;Новости; Пусть будет.",
        ]

        Category.objects.all().delete()
        for cat_data in cats:
            code, pk, name, desc = cat_data.split(';')
            Category.objects.create(pk=pk, code=code, name=name, description=desc.strip())