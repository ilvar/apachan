# coding=utf-8
import random

from newapa.models import Category


def categories(request):
    cats = list(Category.objects.all())
    selected_cats = request.session.get('categories', [])
    if selected_cats:
        for c in cats:
            c.checked = str(c.pk) in selected_cats

    return {
        'categories': cats,
    }


def search_question(request):
    questions = [
        u"Как отсюда выйти?",
        u"Как покинуть Омск?",
        u"От спички норм будет?",
        u"Есть ли жизнь с обратной стороны эскалатора?",
        u"Женщины с венеры мужчины с владивостока",
        u"Как потушить капусту?",
        u"Сколько дебилов в России?",
    ]
    return {
        'search_question': random.choice(questions),
    }