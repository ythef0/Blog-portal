from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views as blog_views

# Основен рутер за ViewSet-ове
router = DefaultRouter()
router.register('posts', blog_views.PostViewSet, basename='posts')
router.register('poll', blog_views.WeeklyPollViewSet, basename='poll')

# URL пътища
urlpatterns = [
    # Включване на рутера
    path('', include(router.urls)),

    # Пътища за коментари
    path('posts/<int:post_pk>/comments/', blog_views.CommentList.as_view(), name='comment-list'),
    path('posts/<int:post_pk>/comments/add/', blog_views.AddCommentAPIView.as_view(), name='add-comment'),

    # Път за регистрация
    path('auth/register/', blog_views.RegisterView.as_view(), name='register'),
    
    # Път за контактен формуляр
    path('contact/', blog_views.ContactFormSubmitView.as_view(), name='contact-submit'),

    # Път за известия
    path('notifications/', blog_views.NotificationListView.as_view(), name='notification-list'),
]
