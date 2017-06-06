# coding=utf-8
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from newapa.models import RandomPack, RandomPackImage

class Command(BaseCommand):
    help = 'Recreates randompacks existing in 1.0'

    def handle(self, *args, **options):
        pack_names = [u"Общий",  u"Шарик",  u"Будь мужиком",  u"Ракодил",  u"Два чая этому",  u"Пиздолис",
                      u"Котики-няшки",  u"Slowpoke",  u"Пекафэйс",  u"Сoolstory, bro!",  u"Мразиш?",  u"Петросян",
                      u"facepalm.jpg",  u"Биопроблемы",  u"Альфабет",  u"Илита",  u"Пичалька",  u"Eбать, дебил!",
                      u"Варг",  u"Ватник"]

        old_path = os.path.join(settings.MEDIA_ROOT, 'random', '%s')

        RandomPack.objects.all().delete()

        for (i, name) in enumerate(pack_names):
            packnum = i + 1
            pack_path = old_path % packnum

            pack = RandomPack.objects.create(title=name)
            for fname in os.listdir(pack_path):
                fname_clean = fname.decode('ascii', errors='ignore').encode('ascii', errors='ignore')
                RandomPackImage.objects.create(pack=pack, image='/' + os.path.join('random', str(packnum), fname_clean))

            print '%s %s ok' % (packnum, name)