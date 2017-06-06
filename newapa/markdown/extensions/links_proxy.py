from __future__ import absolute_import
from __future__ import unicode_literals

import base64

from markdown import Extension
from markdown.inlinepatterns import LinkPattern, AutolinkPattern, LINK_RE, AUTOLINK_RE


class LinkProxyPattern(LinkPattern):
    def sanitize_url(self, url):
        url = super(LinkProxyPattern, self).sanitize_url(url)
        return "/go.php?url=" + base64.b64encode(url.encode("utf8"))


class AutoLinkProxyPattern(AutolinkPattern):
    def handleMatch(self, m):
        el = super(AutoLinkProxyPattern, self).handleMatch(m)
        el.set('href', "/go.php?url=" + base64.b64encode(el.get('href', "").encode("utf8")))
        return el


class LinksProxyExtension(Extension):

    def extendMarkdown(self, md, md_globals):
        proxy_link = LinkProxyPattern(LINK_RE, md)
        md.inlinePatterns['link'] = proxy_link

        proxy_auto_link = AutoLinkProxyPattern(AUTOLINK_RE, md)
        md.inlinePatterns['autolink'] = proxy_auto_link

        SHORTLINK_RE = r'(https?://[^\s]+)'

        proxy_auto_link_short = AutoLinkProxyPattern(SHORTLINK_RE, md)
        md.inlinePatterns['autolink_short'] = proxy_auto_link_short


def makeExtension(*args, **kwargs):
    return LinksProxyExtension(*args, **kwargs)
