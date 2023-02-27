from django.contrib import admin

# Register your models here.
from .models import UserModel, OutboundEmail, Tag, WPID, Redirect, Pageview, UserPageview, UserLink, Click, List

admin.site.register(UserModel)
admin.site.register(OutboundEmail)
admin.site.register(Tag)
admin.site.register(WPID)
admin.site.register(Redirect)
admin.site.register(Pageview)
admin.site.register(Click)
admin.site.register(UserPageview)
admin.site.register(UserLink)
admin.site.register(List)
