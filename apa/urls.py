from django.conf.urls import url

from apa.views import *

urlpatterns = [
    url(r'^$', HomeView.as_view(), name='home'),

    url(r'^my.html$', AllFeedView.as_view(), {'filtering': True}, name='feed_my'),
    url(r'^all.html$', AllFeedView.as_view(), {'filtering': False}, name='feed_all'),
    url(r'^best.php$', BestFeedView.as_view(), name='feed_best'),
    url(r'^mine.php$', MyFeedView.as_view(), name='feed_best'),
    url(r'^replies.php$', RepliesFeedView.as_view(), name='feed_best'),
    url(r'^favorite.php$', FavoritesFeedView.as_view(), name='feed_best'),

    url(r'^images.php$', GalleryView.as_view(), name='gallery'),
    url(r'^pic(?P<pk>\w+).html$', PreviewView.as_view(), name='preview'),
    url(r'^fav_(?P<pk>\d+).php', FavoriteCommentView.as_view(), name='favorite'),
    url(r'^like_(?P<pk>\d+).php', LikeCommentView.as_view(), name='like'),
    url(r'^dislike_(?P<pk>\d+).php', DisLikeCommentView.as_view(), name='dislike'),
    url(r'^moderate_(?P<pk>\d+).php$', ModerateCommentView.as_view(), name='moderate_comment'),
    url(r'^(?P<cat>b|c|r|med|prg|new|i|vk|eot|a|gay).html$', FeedView.as_view(), name='feed_cat'),
    url(r'^(?P<cat>b|c|r|med|prg|new|i|vk|eot|a|gay)/$', FeedView.as_view(), name='feed_cat_short'),
    url(r'^(?P<pk>\d+).html$', ThreadView.as_view(), name='thread'),
    
    url(r'^cap_(?P<pk>\d+).php', CaptchaCommentView.as_view(), name='captcha'),
    url(r'^captcha.php', CaptchaView.as_view(), name='captcha_img'),
    url(r'^go.php', RedirectorView.as_view(), name='redirector'),
]
