import math

from django.conf import settings
from django.http import HttpResponseNotAllowed
from django.http import HttpResponseRedirect

import apa.utils
from apa.models import BannedCookie


class AnonTrackingMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.is_trusted = request.user.is_authenticated()
        request.wait_to_post = None
        request.cookie_id = request.COOKIES.get(settings.SESSION_COOKIE_NAME)
        request.banned = False
        request.dislikes = request.session.get("dislikes", [])
        request.night_mode = request.session.get("night_mode") == "1"

        if request.GET.get("night") == "1":
            request.session["night_mode"] = "1"
            request.session.save()
            return HttpResponseRedirect(request.path)

        if request.GET.get("night") == "0":
            del request.session["night_mode"]
            request.session.save()
            return HttpResponseRedirect(request.path)

        if request.GET.get("night") == "1":
            request.session["night_mode"] = "1"
            request.session.save()
            return HttpResponseRedirect(request.path)

        if request.GET.get("night") == "0":
            del request.session["night_mode"]
            request.session.save()
            return HttpResponseRedirect(request.path)

        if request.GET.get("night") == "1":
            request.session["night_mode"] = "1"
            request.session.save()
            return HttpResponseRedirect(request.path)

        if request.GET.get("night") == "0":
            del request.session["night_mode"]
            request.session.save()
            return HttpResponseRedirect(request.path)

        if not request.is_trusted:
            user_since = request.session.get("user_since")
            now = apa.utils.to_datetime()

            if not user_since:
                request.session["user_since"] = now
                age = 0
            else:
                last_post = request.session.get("last_post")

                # in seconds
                if last_post and now < int(user_since) - 86400:
                    age = now - last_post
                else:
                    age = now - int(user_since)

            if request.cookie_id:
                bans = BannedCookie.objects.filter(cookie_id=request.cookie_id).exists()
            else:
                bans = False

            if age < settings.FIRST_DAY_DURATION:
                # First day - one post per 30 minutes
                request.wait_to_post = int(math.ceil(float((settings.AGE_TO_POST_MINUTES * 60) - age) / 60))

                if request.method == 'POST' and not request.path.startswith('/admin/login/'):
                    return HttpResponseNotAllowed(permitted_methods=['GET'])

            if bans:
                request.banned = True

                if request.method == 'POST' and not request.path.startswith('/admin/login/'):
                    return HttpResponseNotAllowed(permitted_methods=['GET'])

        response = self.get_response(request)
        return response


class SettingsMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        for setting in ["night_mode", "hide_fully", "new_top", "old_css"]:
            if request.GET.get(setting) == "1":
                request.session[setting] = "1"
                request.session.save()
                return HttpResponseRedirect(request.path)
    
            if request.GET.get(setting) == "0":
                del request.session[setting]
                request.session.save()
                return HttpResponseRedirect(request.path)

        response = self.get_response(request)
        return response
