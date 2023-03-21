"""stats URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path('admin/', admin.site.urls),
]

from django.views.generic import RedirectView
from django.urls import include
urlpatterns += [
    path('', RedirectView.as_view(url='dati/', permanent=True)),
    path('dati/', include('dati.urls')),

]

from django.conf import settings
from django.conf.urls.static import static
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


from dati.views import SendTemplateMailView , render_image2, link, page, SendTemplateMailTestView, login_view, get_auth_token

urlpatterns += [
      path('send/render_image2/<int:id>',render_image2, name='render_image2'),
      path('page/<int:id>',page, name='pageview'),
      path('link/<int:id>',link, name='link'),
      path('send', SendTemplateMailView.as_view(), name='send_template'),
      path('sendtest', SendTemplateMailTestView.as_view(), name='send_test_template'),
      path('login', login_view, name='login_view'),
      path('api-token-auth/', obtain_auth_token, name='api_token_auth'),
      path('get-auth-token/', get_auth_token, name='get_auth_token'),

]

