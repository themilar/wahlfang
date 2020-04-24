from django.urls import path
from django.contrib.auth import views as auth_views

from vote import forms
from vote import views

urlpatterns = [
    path('', views.index, name='index'),
    path('vote', views.vote, name='vote'),
    path('upload_application', views.upload_application, name='upload-application'),
    path('view_application/<pk>', views.view_application, name='view-application')
]

# account management stuff
urlpatterns += [
    path('code', views.code_authentication),
    path('login', auth_views.LoginView.as_view(
        authentication_form=forms.TokenAuthenticationForm,
        template_name='vote/login.html'
    ), name='login'),
    path('logout', auth_views.LogoutView.as_view(
        next_page='index',
    ), name='logout')
]
