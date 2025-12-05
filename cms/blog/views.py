#from django.shortcuts import render

from rest_framework import viewsets, generics, serializers
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Posts, Comments
from .serializer import PostSerializer, RegisterSerializer, CommentSerializer
from django.contrib.auth.models import User

class PostViewSet(viewsets.ModelViewSet):
    queryset = Posts.objects.filter(published=True, allowed=True).order_by('-created_at')
    serializer_class = PostSerializer
    http_method_names = ['get', 'head', 'options']


class RegisterView(generics.CreateAPIView):
    # Разрешава достъп на всеки (тъй като се регистрира)
    permission_classes = [AllowAny]
    queryset = User.objects.all()
    serializer_class = RegisterSerializer




class CommentList(generics.ListAPIView):
    serializer_class = CommentSerializer

    def get_queryset(self):
        # Взимаме post_id от URL параметрите
        post_id = self.kwargs.get('post_id')

        # ❗ Филтрираме queryset-а по ID на поста
        if post_id:
            return Comments.objects.filter(post_id=post_id).order_by('-created_at')

        return Comments.objects.all()

class CommentCreate(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        post_id = self.kwargs.get('post_id')
        return Comments.objects.filter(post_id=post_id).order_by('-created_at')

    def perform_create(self, serializer):
        # 1. Вземаме ID-то на поста от URL параметъра
        post_id = self.kwargs['post_pk']

        # 2. Вземаме обекта на поста (ако приемем, че моделът ви се казва Posts)
        # ❗ ВАЖНО: Трябва да импортирате Posts модела (напр. from .models import Posts)

        try:
            post_instance = Posts.objects.get(id=post_id)
        except Posts.DoesNotExist:
            # Може да хвърлите 404 грешка, ако постът не съществува
            raise serializers.ValidationError("Постът не е намерен.")

        # 3. Запазваме коментара, като автоматично подаваме user и post:
        serializer.save(
            user=self.request.user,  # Взема потребителя от JWT токена
            post=post_instance  # Подава обекта на поста
        )