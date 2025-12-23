from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views as blog_views

# Основен рутер за ViewSet-ове
router = DefaultRouter()
router.register('posts', blog_views.PostViewSet, basename='posts')
router.register('poll', blog_views.WeeklyPollViewSet, basename='poll')
router.register('memes', blog_views.MemeOfWeekViewSet, basename='memes')

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

    # Път за събития
    path('events/', blog_views.EventListView.as_view(), name='event-list'),

    # Път за Условия за ползване
    path('terms-of-service/', blog_views.TermsOfServiceView.as_view(), name='terms-of-service'),

    # Път за Политика за поверителност
    path('privacy-policy/', blog_views.PrivacyPolicyView.as_view(), name='privacy-policy'),

    # Път за записване на съгласие за бисквитки
    path('consent/', blog_views.ConsentRecordCreateView.as_view(), name='record-consent'),

    # Път за предложения за песни за звънец
    path('bell-song-suggestions/submit/', blog_views.BellSongSuggestionCreateAPIView.as_view(), name='bell-song-submit'),

    # Bell song voting system URLs
    path('approved-songs/', blog_views.ApprovedBellSongListView.as_view(), name='approved-songs-list'),
    path('songs/<int:pk>/vote/', blog_views.BellSongVoteView.as_view(), name='song-vote'),

    # Meme voting system URL
    path('memes/<int:pk>/vote/', blog_views.MemeVoteView.as_view(), name='meme-vote'),
]
