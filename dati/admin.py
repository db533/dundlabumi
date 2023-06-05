from django.contrib import admin

# Register your models here.
from .models import OutboundEmail, Tag, WPID, Redirect, Click, List, UserModel , LogEntry, Pageview, DesiredSize # UserPageview, UserTag, UserLink ,

admin.site.register(UserModel)
admin.site.register(OutboundEmail)
admin.site.register(Tag)
admin.site.register(WPID)
admin.site.register(Redirect)
admin.site.register(Pageview)
admin.site.register(Click)
#admin.site.register(UserPageview)
#admin.site.register(UserLink)
admin.site.register(List)
admin.site.register(LogEntry)
#admin.site.register(UserTag)
admin.site.register(DesiredSize)
