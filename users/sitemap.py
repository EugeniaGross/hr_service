from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class UserViewSitemap(Sitemap):

    def items(self):
        return [
            "users:company_registration",
            "users:login",
            "users:password_reset"
        ]

    def location(self, obj):
        return reverse(obj)

    def changefreq(self, obj):
        return "newer"
