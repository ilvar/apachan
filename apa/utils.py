import datetime
import random
import time

import math
import pytz
import nltk
import nltk.corpus
from PIL import Image


def get_tz():
    return pytz.timezone('Europe/Moscow')


def get_datetime(dt):
    return datetime.datetime.fromtimestamp(dt, tz=get_tz())


def to_datetime(dt=None):
    dt = dt or datetime.datetime.now(get_tz())
    return int(time.mktime(dt.timetuple()))


def tokenize_text(text):
    tokens = nltk.wordpunct_tokenize(text)
    words = [word.lower() for word in tokens]
    return words


def _calculate_languages_ratios(text):
    languages_ratios = {}
    words = set(tokenize_text(text))

    # Compute per language included in nltk number of unique stopwords appearing in analyzed text
    for language in nltk.corpus.stopwords.fileids():
        stopwords_set = set(nltk.corpus.stopwords.words(language))
        words_set = words
        common_elements = words_set.intersection(stopwords_set)

        languages_ratios[language] = len(common_elements)  # language "score"

    return languages_ratios


def detect_language(text):
    ratios = _calculate_languages_ratios(text)

    most_rated_language = max(ratios, key=ratios.get)

    return most_rated_language, ratios[most_rated_language]


class CaptchaWarpBase():
    """Abstract base class for image warping. Subclasses define a
       function that maps points in the output image to points in the input image.
       This warping engine runs a grid of points through this transform and uses
       PIL's mesh transform to warp the image.
       """
    filtering = Image.BILINEAR
    resolution = 10

    def getTransform(self, image):
        """Return a transformation function, subclasses should override this"""
        return lambda x, y: (x, y)

    def render(self, image):
        r = self.resolution
        xPoints = image.size[0] / r + 2
        yPoints = image.size[1] / r + 2
        f = self.getTransform(image)

        # Create a list of arrays with transformed points
        xRows = []
        yRows = []
        for j in xrange(yPoints):
            xRow = []
            yRow = []
            for i in xrange(xPoints):
                x, y = f(i*r, j*r)

                # Clamp the edges so we don't get black undefined areas
                x = max(0, min(image.size[0]-1, x))
                y = max(0, min(image.size[1]-1, y))

                xRow.append(x)
                yRow.append(y)
            xRows.append(xRow)
            yRows.append(yRow)

        # Create the mesh list, with a transformation for
        # each square between points on the grid
        mesh = []
        for j in xrange(yPoints-1):
            for i in xrange(xPoints-1):
                mesh.append((
                    # Destination rectangle
                    (i*r, j*r,
                     (i+1)*r, (j+1)*r),
                    # Source quadrilateral
                    (xRows[j  ][i  ], yRows[j  ][i  ],
                     xRows[j+1][i  ], yRows[j+1][i  ],
                     xRows[j+1][i+1], yRows[j+1][i+1],
                     xRows[j  ][i+1], yRows[j  ][i+1]),
                    ))

        return image.transform(image.size, Image.MESH, mesh, self.filtering)


class CaptchaSineWarp(CaptchaWarpBase):
    """Warp the image using a random composition of sine waves"""

    def __init__(self,
                 amplitudeRange = (3, 6.5),
                 periodRange    = (0.04, 0.1),
                 ):
        self.amplitude = random.uniform(*amplitudeRange)
        self.period = random.uniform(*periodRange)
        self.offset = (random.uniform(0, math.pi * 2 / self.period),
                       random.uniform(0, math.pi * 2 / self.period))

    def getTransform(self, image):
        return (lambda x, y,
                a = self.amplitude,
                p = self.period,
                o = self.offset:
                (math.sin( (y+o[0])*p )*a + x,
                 math.sin( (x+o[1])*p )*a + y))


def enforce_captcha(request):
    from apa.models import Captcha

    captchas = list(Captcha.objects.all().order_by('?').values_list('keyword', flat=True))[:9]
    request.session['post_captcha'] = captchas[0]
    
    random.shuffle(captchas)
    
    request.session['captcha_options'] = captchas
    request.session.save()