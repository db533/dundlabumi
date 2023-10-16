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
from django.views.generic import RedirectView
from django.urls import include
from dati.views import *
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.authtoken.views import obtain_auth_token
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('', RedirectView.as_view(url='http://dundlabumi.lv/', permanent=True)),
    path('admin/', admin.site.urls),
    path('dati/', include('dati.urls')),
    path('send/render_image2/<int:id>',render_image2, name='render_image2'),
    path('page/<int:id>',page, name='pageview'),
    path('non_product_page/<int:id>',non_product_page, name='non_product_pageview'),
    path('link/<int:id>',link, name='link'),
    path('send', SendTemplateMailView.as_view(), name='send_template'),
    path('sendtest', SendTemplateMailTestView.as_view(), name='send_test_template'),
    path('login', login_view, name='login_view'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),  # Add logout view
    path('api-token-auth/', obtain_auth_token, name='api_token_auth'),
    path('get-auth-token/', get_auth_token, name='get_auth_token'),
    path('user/<int:user_id>', user_details, name='user_details'),
    path('user-list/', user_list, name='user_list'),
    path('named-user-list/', named_user_list, name='named_user_list'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('redirect-details/', redirect_details, name='redirect_details'),
    path('redirect-product-details/', redirect_product_details, name='redirect_product_details'),
    path('tag_bar_charts/', tag_count_bar_charts, name='tag_bar_chart_data'),
    path('type_and_colour_bar_charts/', type_and_colour_bar_charts, name='type_and_colour_bar_charts'),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


