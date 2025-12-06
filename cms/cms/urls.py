"""
URL configuration for cms project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    # Може да добавите и TokenVerifyView, но не е задължително
)
from blog import views as blog_views

router = DefaultRouter()
router.register('posts', blog_views.PostViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),

    path('api/posts/<int:post_pk>/comments/', blog_views.CommentList.as_view(), name='comment-list'),

    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),

    path('api/posts/<int:post_pk>/comments/add/', blog_views.AddCommentAPIView.as_view(), name='post-comments'),
    # ...


    # ОПРЕСНЯВАНЕ: Взема REFRESH токен, връща нов ACCESS токен
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
