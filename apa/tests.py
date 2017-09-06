import os

from PIL import Image
from django.conf import settings
from django.test import TestCase, Client

from apa.models import Lenta, Comment, Captcha
from newapa.models import RandomLogo, Category, RandomPack, RandomPackImage


class FeedsTestCase(TestCase):
    def setUp(self):
        RandomLogo.objects.all().delete()
        Category.objects.all().delete()
        Lenta.objects.all().delete()
        Comment.objects.all().delete()

        RandomPack.objects.all().delete()
        RandomPackImage.objects.all().delete()
        Captcha.objects.all().delete()

        self.rp = RandomPack.objects.create(title="rp1")
        self.rpi = RandomPackImage.objects.create(pack=self.rp, image="test.jpg")

        try:
            os.makedirs(settings.MEDIA_ROOT, 0777)
        except OSError:
            pass

        img = Image.new('RGB', (100, 100))
        img.save(open(os.path.join(settings.MEDIA_ROOT, 'test_captcha.png'), 'w'), 'png')

        self.captcha = Captcha.objects.create(
            image_name="fooblya",
            image_file="test_captcha.png",
            keyword="blyat",
            last_updated=100000,
            num_used=0
        )

        cookie_id = "abcdef12345"

        self.cat = Category.objects.create(number=1, code="b", name="Bread", description="")
        self.comment1 = Comment.objects.create(
            poster_id=1,
            cookie_id=cookie_id,
            root_id=0,
            parent_id=0,
            datetime=100000,
            rating=0,
            picrand=0,
            tcrc=0,
            captxt="bazzinga",
            text="foo bar",
            source="foo bar"
        )
        self.comment2 = Comment.objects.create(
            poster_id=1,
            cookie_id=cookie_id,
            root_id=self.comment1.pk,
            parent_id=self.comment1.pk,
            datetime=100000,
            rating=0,
            picrand=0,
            tcrc=0,
            captxt="bazzinga",
            text="foo bar",
            source="foo bar"
        )
        self.post1 = Lenta.objects.create(
            category=self.cat,
            root=self.comment1,
            sticker=0,
            drowner=0,
            roulette=0,
            poll=0,
            hidden=0,
            replies=0,
            rating=0,
            datetime=1000000
        )

    def tearDown(self):
        pass

    def test_home_no_logo(self):
        r = self.client.get('/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['logo'], None)

    def test_home_with_logo(self):
        logo = RandomLogo.objects.create(image='test')

        r = self.client.get('/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['logo'], logo)

    def test_all(self):
        r = self.client.get('/all.html')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['category'], None)
        self.assertEqual(len(r.context['object_list']), 1)
        self.assertEqual(r.context['object_list'][0], self.post1)

    def test_b(self):
        r = self.client.get('/b.html')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['category'], self.cat)
        self.assertEqual(len(r.context['object_list']), 1)
        self.assertEqual(r.context['object_list'][0], self.post1)

    def test_nonexistent(self):
        r = self.client.get('/nonexistent.html')
        self.assertEqual(r.status_code, 404)

    def test_post(self):
        r = self.client.get('/%s.html' % self.post1.pk)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['object'], self.comment1)

    def test_non_post(self):
        r = self.client.get('/%s.html' % self.comment2.pk)
        self.assertEqual(r.status_code, 404)

    def test_create_all(self):
        data = dict(
            title="test 1",
            category=self.cat.pk,
            message="foo\n\nbarge",
            roulette=True
        )

        self.assertEqual(len(self.client.get('/b.html').context['object_list']), 1)

        r = self.client.post('/b.html', data)
        self.assertEqual(r.status_code, 302)

        last_comment = Comment.objects.all().order_by('-pk').first()
        cap_url = '/cap_%s.php' % last_comment.pk
        self.assertEqual(r['Location'], cap_url)

        c1 = self.client.get(cap_url)
        self.assertEqual(c1.status_code, 200)
        self.assertEqual(c1.context['object'], last_comment)

        token = c1.context['object']
        ci = self.client.get('/captcha.php?dt=%s' % token)
        self.assertEqual(ci.status_code, 200)
        self.assertEqual(ci['Content-Type'], 'image/png')

        self.assertEqual(len(self.client.get('/b.html').context['object_list']), 1)

        c2 = self.client.post(cap_url, {'captcha': self.captcha.keyword})
        self.assertEqual(c2.status_code, 302)

        self.assertEqual(len(self.client.get('/b.html').context['object_list']), 2)
