# coding=utf-8
import datetime

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import DetailView
from django.views.generic import ListView

from inbox.models import Inbox, Message


class MyInboxes():
    def get_queryset(self):
        my_inboxes = Inbox.objects.filter(cookie_id=self.request.cookie_id)
        month_ago = datetime.datetime.now() - datetime.timedelta(30)
        return my_inboxes.filter(updated__gte=month_ago).order_by('-updated')


class MyInboxesListView(MyInboxes, ListView):
    template_name = 'inbox/list.html'
    context_object_name = 'inbox_list'

    def post(self, *args, **kwargs):
        if self.request.wait_to_post or self.request.banned:
            messages.error(self.request, u'Вам запрещено постить.')
            return HttpResponseRedirect(reverse('inbox_list'))

        action = self.request.POST.get('action')
        if action == 'create':
            inbox = Inbox.objects.create(cookie_id=self.request.cookie_id)
            messages.success(self.request, u'Создан инбокс с кодом %s, раздайте этот код собеседникам.' % inbox.code)
            return HttpResponseRedirect(reverse('inbox_list'))

        msg = self.request.POST.get('message', '').strip()
        code = self.request.POST.get('code', '').strip()
        if action == 'reply' and msg and code:
            inbox = Inbox.objects.get(code=code)
            
            m = Message.objects.create(
                inbox=inbox,
                cookie_id=self.request.cookie_id,
                message=msg
            )
            Inbox.objects.filter(code=inbox.code).update(updated=m.created)
            
            messages.success(self.request, u'Вы написали в инбокс с кодом %s.' % inbox.code)
            return HttpResponseRedirect(reverse('inbox_list'))

        messages.error(self.request, u'Не понял.')
        return HttpResponseRedirect(reverse('inbox_list'))


class InboxView(MyInboxes, DetailView):
    template_name = 'inbox/inbox.html'
    context_object_name = 'inbox'
    slug_field = 'code'

    def post(self, *args, **kwargs):
        if self.request.POST.get('action') == 'mark_read':
            self.get_object().mark_read()
            messages.success(self.request, u'Все сообщения отмечены как прочитанные')

        return HttpResponseRedirect(reverse('inbox_list'))