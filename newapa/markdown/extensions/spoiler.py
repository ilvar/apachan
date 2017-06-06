from __future__ import absolute_import
from __future__ import unicode_literals

from markdown import Extension
from markdown import util
from markdown.inlinepatterns import Pattern


class SpoilerPattern(Pattern):
    def handleMatch(self, m):
        el = util.etree.Element("span")
        el.set('class', 'spoiler')
        el.text = util.AtomicString(m.group(2))
        return el


class SpoilerExtension(Extension):

    def extendMarkdown(self, md, md_globals):
        SPOILER_RE = r'\[[sS][pP][oO][iI][lL][eE][rR]:(.*?)\]'

        spoiler = SpoilerPattern(SPOILER_RE, md)
        md.inlinePatterns['spoiler'] = spoiler


def makeExtension(*args, **kwargs):
    return SpoilerExtension(*args, **kwargs)
