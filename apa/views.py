# coding=utf-8
import base64
import datetime
import random

from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.db.models import F
from django.db.models import Q
from django.http import Http404
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import View
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic import TemplateView

from apa.forms import NewThreadForm, NewCommentForm, BannedImageException, TextValidationError
from apa.models import Lenta, Comment, Image, BannedCookie, Captcha
from apa.utils import enforce_captcha, to_datetime, get_tz
from karma.models import CommentTransaction, LikeTransaction, CatTransaction
from newapa.models import Category, RandomLogo, Favorite, ModerationLog, DisLike


class HomeView(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        data = super(HomeView, self).get_context_data(**kwargs)
        try:
            data['logo'] = RandomLogo.objects.all().order_by('?')[0]
        except IndexError:
            data['logo'] = None
        return data


class FeedView(ListView):
    template_name = 'feed.html'

    context_object_name = 'thread_list'
    paginate_by = 50

    def dispatch(self, request, *args, **kwargs):
        self.request = request

        cat_code = kwargs.get("cat")
        if cat_code:
            self.category = Category.objects.get(code=cat_code)
        else:
            self.category = None

        return super(FeedView, self).dispatch(request, *args, **kwargs)

    def get_generic_queryset(self):
        posts = Lenta.objects.select_related('category', 'root', 'root__image', 'root__title')
        posts = posts.order_by('-sticker', '-datetime')
        return posts.filter(hidden=0).filter(drowner=0)

    def get_queryset(self):
        posts = self.get_generic_queryset()
        if self.category:
            posts = posts.filter(category_id=self.category.pk)
        return posts

    def get_context_data(self, **kwargs):
        context = super(FeedView, self).get_context_data(**kwargs)
        context['form'] = self.get_form()
        context['category'] = self.category
        return context

    _form = None

    def get_form(self):
        if not self._form:
            initial = {}
            if self.category:
                initial.update({'category': self.category})

            self._form = NewThreadForm(request=self.request, data=self.request.POST or None, files=self.request.FILES or None, initial=initial)
        return self._form

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            try:
                thread = form.save()
            except BannedImageException:
                messages.error(request, u'Эта картинка забанена.')
                return HttpResponseRedirect('/%s.html' % (self.category and self.category.code or "all"))
            except IOError:
                messages.error(request, u'Эта картинка не картинка.')
                return HttpResponseRedirect('/%s.html' % (self.category and self.category.code or "all"))

            messages.success(request, u'Решите капчу в течение минуты.')
            return HttpResponseRedirect(reverse('captcha', args=[thread.pk]))
        else:
            return self.get(request, *args, **kwargs)


class BestFeedView(FeedView):
    def get_queryset(self):
        posts = self.get_generic_queryset()
        return posts.order_by('-rating')


class AllFeedView(FeedView):
    def get_queryset(self):
        posts = Lenta.objects.select_related('root', 'root__image', 'root__title')
        posts = posts.order_by('-datetime')
        posts = posts.filter(hidden=0).filter(drowner=0)

        if self.kwargs['filtering']:
            cats = self.request.session.get('categories')
            if cats:
                posts = posts.filter(category_id__in=cats)

        return posts.prefetch_related('category')

    def post(self, request, *args, **kwargs):
        if request.POST.get('action') == 'save':
            self.request.session['categories'] = request.POST.getlist('topics')
            return HttpResponseRedirect(reverse('feed_my'))

        return super(AllFeedView, self).post(request, *args, **kwargs)

    def get_selected_categories(self):
        cats = list(Category.objects.all())
        selected_cats = self.request.session.get('categories', [])
        if selected_cats:
            return [c for c in cats if str(c.pk) in selected_cats]
        else:
            return cats

    def get_context_data(self, **kwargs):
        data = super(AllFeedView, self).get_context_data(**kwargs)

        selected_categories = self.get_selected_categories()

        data.update({
            'selected_categories': self.kwargs['filtering'] and selected_categories,
        })
        return data


class MyFeedView(FeedView):
    def get_queryset(self):
        if not self.request.cookie_id:
            return Lenta.objects.none()
        
        q = Q(root__cookie_id=self.request.cookie_id) | Q(root__cookie_id=self.request.cookie_id[:6])
        posts = self.get_generic_queryset().filter(q)
        return posts.order_by('-datetime')


class RepliesFeedView(FeedView):
    template_name = 'comments_feed.html'

    def get_queryset(self):
        if not self.request.cookie_id:
            return Comment.objects.none()
    
        q = Q(cookie_id=self.request.cookie_id) | Q(cookie_id=self.request.cookie_id[:6])
        my_posts = Comment.objects.filter(Q(parent_id=0) | Q(parent_id=F('root_id'))).filter(q)
        my_post_ids = list(my_posts.values_list('pk', flat=True))
        posts = Comment.objects.all().select_related('image', 'title')
        posts = posts.filter(root_id__in=my_post_ids, deleted=False)
        return posts.order_by('-datetime')


class FavoritesFeedView(FeedView):
    template_name = 'comments_feed.html'

    def get_queryset(self):
        if not self.request.cookie_id:
            return Comment.objects.none()
    
        fav_posts = Favorite.objects.filter(cookie_id=self.request.cookie_id)
        posts = Comment.objects.all().select_related('image', 'title')
        posts = posts.filter(pk__in=list(fav_posts.values_list('comment_id', flat=True)))
        return posts.order_by('-datetime')


class GalleryView(FeedView):
    template_name = 'gallery.html'
    context_object_name = 'images_list'
    paginate_by = 48

    def get_queryset(self):
        return Image.objects.exclude(deleted=True).exclude(banned=True).order_by('-datetime')


class ThreadView(DetailView):
    template_name = 'thread.html'
    context_object_name = 'thread'

    def get_queryset(self):
        qs = Comment.objects.filter(parent_id=0).select_related('image', 'title')
        qs = qs.filter(deleted=0)
        return qs

    def dispatch(self, request, *args, **kwargs):
        self.request = request

        if not self.request.session.get("user_since"):
            self.request.session["user_since"] = datetime.datetime.now().toordinal()

        return super(ThreadView, self).dispatch(request, *args, **kwargs)

    _form = None

    def get_form(self):
        if not self._form:
            self._form = NewCommentForm(request=self.request, data=self.request.POST or None, files=self.request.FILES or None)
        return self._form

    def get_context_data(self, **kwargs):
        context = super(ThreadView, self).get_context_data(**kwargs)
        context['form'] = self.get_form()
        try:
            obj = self.get_object()
            context['lenta'] = obj.lenta
        except ObjectDoesNotExist:
            raise Http404
           
        ret_link = self.request.GET.get("return")
        if ret_link:
            context['return_name'] = u"поток"
            for c in Category.objects.all():
                if "/%s.html" % c.code == ret_link:
                    context['return_name'] = c.name
        
        context['comments'] = obj.get_comments(self.request.session.get("new_top"))
            
        return context

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            try:
                thread = self.get_queryset().get(pk=kwargs['pk'])
            except Comment.DoesNotExist:
                raise Http404

            if thread.is_necropost():
                messages.error(request, u'Некропост запрещен.')
                return HttpResponseRedirect('/%s.html' % thread.pk)

            try:
                c = form.save(thread)
            except BannedImageException:
                messages.error(request, u'Эта картинка забанена.')
                return HttpResponseRedirect('/%s.html' % thread.pk)
            except IOError:
                messages.error(request, u'Эта картинка не картинка.')
                return HttpResponseRedirect('/%s.html' % thread.pk)

            CommentTransaction.create(c.pk)

            messages.success(request, u'Решите капчу в течение минуты.')
            return HttpResponseRedirect(reverse('captcha', args=[c.pk]))
        else:
            return self.get(request, *args, **kwargs)


class PreviewView(DetailView):
    template_name = 'pic.html'
    context_object_name = 'pic'

    def get_queryset(self):
        return Image.objects.filter(deleted=False)

    def get_context_data(self, **kwargs):
        data = super(PreviewView, self).get_context_data(**kwargs)
        posts = Comment.objects.select_related('image', 'title')
        posts = posts.filter(image_id=self.get_object().pk)
        data.update({
            'thread_list': posts.order_by('-datetime')
        })
        return data


class FavoriteCommentView(View):
    def post(self, request, *args, **kwargs):
        comment = Comment.objects.get(comment_id=kwargs['pk'])
        Favorite.objects.get_or_create(comment_id=comment.pk, cookie_id=request.cookie_id)

        messages.success(request, u"Добавлено в избранное")

        return HttpResponseRedirect(reverse('thread', kwargs={'pk': comment.root_id or comment.lenta.pk}) + "#comment-%s" % comment.pk)


class ChangeCategoryView(View):
    def post(self, request, *args, **kwargs):
        comment = Comment.objects.get(comment_id=kwargs['pk'])
        
        if request.wallet and request.wallet.can_cat():
            CatTransaction.create(
                comment_id=comment.pk,
                from_cookie=request.wallet.cookie_id,
                is_staff=request.user.is_staff,
                new_cat=request.POST['category']
            )
            messages.success(request, u"Подвинуто!")
        else:
            messages.error(request, u"Недостаточно бабла!")
    
        return HttpResponseRedirect(
            reverse('thread', kwargs={'pk': comment.root_id or comment.lenta.pk}) + "#comment-%s" % comment.pk)
        

class LikeCommentView(View):
    def post(self, request, *args, **kwargs):
        comment = Comment.objects.get(comment_id=kwargs['pk'])

        if request.wallet and request.wallet.can_like():
            LikeTransaction.create(
                comment_id=comment.pk,
                from_cookie=request.wallet.cookie_id,
                is_staff=request.user.is_staff
            )
            messages.success(request, u"Потрачено!")
        else:
            messages.error(request, u"Недостаточно бабла!")

        return HttpResponseRedirect(reverse('thread', kwargs={'pk': comment.root_id or comment.lenta.pk}) + "#comment-%s" % comment.pk)


class DisLikeCommentView(View):
    def post(self, request, *args, **kwargs):
        comment = Comment.objects.get(comment_id=kwargs['pk'])

        path = reverse('thread', kwargs={'pk': comment.root_id or comment.lenta.pk}) + "#comment-%s" % comment.pk
        action = request.POST.get('action')

        if action == "hide":
            DisLike.objects.get_or_create(
                comment_id=comment.pk,
                cookie_id=request.cookie_id
            )

            request.session.setdefault("dislikes", [])
            request.session['dislikes'] = request.session['dislikes'] + [comment.pk]
            request.session.save()
    
            messages.success(request, u"Пост скрыт")

        if action == "alert":
            send_mail(
                u'Жалобы на сообщение', 'http://apachan.net/%s' % path, 'robot@apachan.net',
                ['apazhe.net@gmail.com'], fail_silently=False
            )

            DisLike.objects.get_or_create(
                comment_id=comment.pk,
                cookie_id=request.cookie_id
            )

            request.session.setdefault("dislikes", [])
            request.session['dislikes'] = request.session['dislikes'] + [comment.pk]
            request.session.save()

            messages.success(request, u"Модераторы уведомлены")

        return HttpResponseRedirect(path)


class ModerateCommentView(View):
    def post(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return Http404()

        comment = Comment.objects.filter(comment_id=kwargs['pk'])
        image = Image.objects.filter(comment__pk=kwargs['pk'])
        lenta = Lenta.objects.filter(root_id=kwargs['pk'])

        real_comment = comment.get()
        root_lenta = Lenta.objects.filter(root_id=real_comment.root_id)

        action = request.POST.get('action')
        if action == "unhide":
            lenta.update(hidden=0)

        if action == "hide":
            lenta.update(hidden=1)

        if action == "not_on_top":
            lenta.update(sticker=0)

        if action == "on_top":
            lenta.update(sticker=1)

        if action == "change_cat":
            lenta.update(category=request.POST['category'])

        if action.startswith("delete"):
            lenta.update(drowner=1)
            comment.update(deleted=True)

            week_ago = to_datetime(datetime.datetime.now() - datetime.timedelta(1))

            image_comments = Comment.objects.filter(image_id=real_comment.image_id, datetime__gte=week_ago)
            image_comment_ids = list(image_comments.values_list('pk', flat=True))

            user_comments = Comment.objects.filter(cookie_id=real_comment.cookie_id, datetime__gte=week_ago)
            user_comments_ids = list(user_comments.values_list('pk', flat=True))

            if action == "delete_ban":
                BannedCookie.objects.get_or_create(cookie_id=real_comment.cookie_id)
                user_comments.update(deleted=True)
                Lenta.objects.filter(root_id__in=user_comments_ids, datetime__gte=week_ago).update(drowner=True)

            if action == "delete_ban_image":
                image.update(deleted=True, banned=True)

                user_comments.update(deleted=True)
                Lenta.objects.filter(root_id__in=user_comments_ids, datetime__gte=week_ago).update(drowner=True)

                image_comments.update(deleted=True)
                Lenta.objects.filter(root_id__in=image_comment_ids, datetime__gte=week_ago).update(drowner=True)

                BannedCookie.objects.get_or_create(cookie_id=real_comment.cookie_id)

            if not real_comment.root_id or real_comment.root_id == real_comment.pk:
                # Complete thread
                field = "root_id"
            else:
                field = "comment_id"

            CommentTransaction.cancel(**{field: real_comment.pk})
            LikeTransaction.cancel(**{field: real_comment.pk})

            replies = Comment.objects.filter(root_id=real_comment.root_id).exclude(comment_id=real_comment.root_id)
            root_lenta.update(replies=replies.exclude(deleted=True).count())

        ModerationLog.objects.create(
            moderator = unicode(request.user),
            action = action,
            comment_id = real_comment.pk
        )

        return HttpResponseRedirect(reverse('thread', kwargs={'pk': real_comment.root_id or real_comment.lenta.pk}))
    
    
class CaptchaCommentView(DetailView):
    template_name = 'captcha.html'
    
    def dispatch(self, request, *args, **kwargs):
        self.request = request
        return super(CaptchaCommentView, self).dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        if not self.request.cookie_id:
            return  Comment.objects.none()
        
        unpublished_comments = Comment.objects.filter(rating__lt=0)
        my_comments = unpublished_comments.filter(cookie_id__in = [self.request.cookie_id, self.request.cookie_id[:6]])
        minute_ago = to_datetime(datetime.datetime.now(get_tz()) - datetime.timedelta(0, 600))
        return my_comments.filter(datetime__gte=minute_ago)
    
    def get_context_data(self, **kwargs):
        context = super(CaptchaCommentView, self).get_context_data(**kwargs)
        context['post_captcha'] = self.request.session.get('post_captcha')
        context['captcha_options'] = self.request.session.get('captcha_options', [])
        context['token'] = random.randint(0, 1000000)
        return context
    
    def get(self, request, *args, **kwargs):
        enforce_captcha(request)
        return super(CaptchaCommentView, self).get(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        comment = self.get_object()
        if self.request.session.get('post_captcha') == self.request.POST.get('captcha'):
            Comment.objects.filter(pk=comment.pk).update(rating=0)
            c = Comment.objects.filter(pk=comment.pk)[0]
            if not c.dont_raise:
                Lenta.objects.filter(root=c.root_id).update(datetime=to_datetime())
            Lenta.objects.filter(root_id=comment.pk).update(hidden=0)
            Lenta.objects.filter(root_id=comment.root_id).update(replies=F('replies') + 1)

            messages.success(request, u'Камент запощен.')
            return HttpResponseRedirect('/%s.html#comment-%s' % (comment.root_id or comment.pk, comment.pk))
        else:
            messages.error(request, u'Неверная капча. Попробуйте еще раз.')
            return HttpResponseRedirect(reverse('captcha', args=[comment.pk]))


class CaptchaView(View):
    def get(self, request, *args, **kwargs):
        cpt = request.session.get('post_captcha')
        if cpt:
            captcha = Captcha.objects.get(keyword=cpt)
        else:
            captcha = Captcha.objects.all()[0]

        captcha_img = captcha.get_twisted_img()

        response = HttpResponse(content_type="image/png")
        captcha_img.save(response, "PNG")
        return response


class RedirectorView(View):
    rot13 = dict(zip("ABCDEFGHIJKLMabcdefghijklmNOPQRSTUVWXYZnopqrstuvwxyz", "NOPQRSTUVWXYZnopqrstuvwxyzABCDEFGHIJKLMabcdefghijklm"))
    
    def get(self, request, *args, **kwargs):
        param_url = request.GET.get("url")
        try:
            if param_url:
                decoded_url = base64.b64decode(param_url)
            else:
                decoded_url = "http://" + "".join(map(lambda c: self.rot13.get(c, c), request.GET.get("w", "")))
        except:
            decoded_url = "/"

        try:
            return HttpResponseRedirect(decoded_url.decode('utf8'))
        except:
            messages.error(request, u"Поломанный URL, сообщите автору поста")
            return HttpResponseRedirect('/')
