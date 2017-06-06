from django.conf.urls import url

from inbox.views import MyInboxesListView, InboxView

urlpatterns = [
    url(r'^$', MyInboxesListView.as_view(), name='inbox_list'),
    url(r'^(?P<slug>\w+)/', InboxView.as_view(), name='inbox')
]