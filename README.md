# apachan

Для запуска понадобится mysql, python 2.7, virtualenv и pip.

```
virtualenv ./ENV
source ./ENV/bin/activate
pip install -r requirements.txt
```

В `apachan/settings_local.py` прописываем локальные настройки

```
import os

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'apachan',
        'USER': 'dbuser',
        'PASSWORD': 'dbpass',
    }
}

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

STATIC_ROOT = os.path.join(BASE_DIR, 'static')
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEBUG = True

SECRET_KEY = 'RANDOM STRING'
```

Создаем начальные данные
```
python manage.py createsuperuser (вводим имя, email и пароль)
python manage.py init_cats
```

И запускаем:

```
python manage.py runserver
```

Проект будет доступен по адресу `http://localhost:8000/`, админка `http://localhost:8000/admin/`
