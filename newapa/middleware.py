from newapa.models import Favorite


class FavoritesMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.fav_ids = set()

        if request.cookie_id:
            request.fav_ids = set(Favorite.objects.filter(cookie_id=request.cookie_id).values_list('comment_id', flat=True))

        response = self.get_response(request)
        return response
