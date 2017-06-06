from django import template


def is_faved(comment, request):
    return comment.comment_id in request.fav_ids

register = template.Library()
register.filter('is_faved', is_faved)