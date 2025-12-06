from rest_framework import viewsets, generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView # За ръчно POST управление
from rest_framework.response import Response # За връщане на отговор
from django.shortcuts import get_object_or_404

# Импортиране на модели и сериализатори
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
    http_method_names = ['get', 'post', 'options', 'head']

    def get_queryset(self):
        post_id = self.kwargs.get('post_pk')

        # 1. Ако липсва post_id, връщаме празен QuerySet, за да не показваме всички
        if not post_id:
            return Comments.objects.none()

            # 2. Опитваме се да намерим поста, за да се уверим, че съществува
        # Ако постът не съществува, get_object_or_404 ще хвърли 404 Not Found.
        post = get_object_or_404(Posts, id=post_id)

        # 3. Връщаме филтрирания QuerySet
        return Comments.objects.filter(post=post).order_by('-created_at')


class AddCommentAPIView(APIView):
    # 🛡️ Изисква Access Token (JWT)
    permission_classes = [IsAuthenticated]

    def post(self, request, post_id): # Аргументът трябва да е post_id

        # 1. Валидация на Пост
        post = get_object_or_404(Posts, id=post_id)

        # 2. Извличане на съдържанието
        content = request.data.get('content')

        if not content or len(content.strip()) == 0:
            return Response({'content': 'Comment content cannot be empty.'}, status=status.HTTP_400_BAD_REQUEST)

        # 3. Създаване на Коментара
        try:
            comment = Comments.objects.create(
                user=request.user,              # Взема се от JWT токена
                post=post,                      # Взема се от URL параметъра
                content=content                 # Взема се от тялото на заявката
            )
        except Exception as e:
            print(f"Error creating comment: {e}")
            return Response({'detail': 'Internal server error during comment creation.'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 4. Подготовка на отговора
        # Тъй като не използваме сериализатор, връщаме го ръчно
        comment_data = {
            'id': comment.id,
            'post_id': comment.post.id,
            'username': comment.user.username,
            'content': comment.content,
            'created_at': comment.created_at.isoformat().replace('+00:00', 'Z')
        }

        return Response(comment_data, status=status.HTTP_201_CREATED)