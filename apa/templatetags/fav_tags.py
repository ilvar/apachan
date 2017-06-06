from django import template


def is_liked(comment, request):
    return comment.comment_id in request.like_ids

register = template.Library()
register.filter('is_liked', is_liked)