from rest_framework import viewsets, generics, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView  # За ръчно POST управление
from rest_framework.response import Response  # За връщане на отговор
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta
import random
from django.db.models import Count, Q, Max

# Импортиране на модели и сериализатори
from .models import Posts, Comments, PollQuestion, PollAnswer, PollOption, ContactSubmission, Notification, Event, TermsOfService
from .serializer import (
    PostSerializer, RegisterSerializer, CommentSerializer,
    PollQuestionSerializer, UserPollStatusSerializer, PollAnswerSerializer,
    PollStatisticsSerializer, ContactSubmissionSerializer, NotificationSerializer, EventSerializer, TermsOfServiceSerializer
)
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
    permission_classes = [IsAuthenticated]

    def post(self, request, post_pk): # Now accepts post_pk
        post = get_object_or_404(Posts, id=post_pk) # Use post_pk

        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            comment = serializer.save(user=request.user, post=post)
            return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def get_next_sunday_deadline():
    now = timezone.now()
    # Sunday is 6, Monday is 0
    days_until_sunday = (6 - now.weekday() + 7) % 7
    deadline = (now + timedelta(days=days_until_sunday)).replace(hour=23, minute=59, second=59, microsecond=0)
    if deadline <= now:  # If it's Sunday but past the deadline, set for next week
        deadline += timedelta(weeks=1)
    return deadline

class WeeklyPollViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'submit':
            return PollAnswerSerializer
        elif self.action == 'statistics':
            return PollStatisticsSerializer
        return UserPollStatusSerializer

    @action(detail=False, methods=['get'])
    def status(self, request):
        user = request.user
        
        # The week starts on Monday (weekday()==0) and ends on Sunday (weekday()==6)
        today = timezone.now().date()
        start_of_week = today - timedelta(days=today.weekday())

        latest_answer = PollAnswer.objects.filter(user=user, created_at__gte=start_of_week).order_by('-created_at').first()

        if latest_answer:
            # User has answered this week
            deadline = get_next_sunday_deadline()
            correct_option = PollOption.objects.filter(question=latest_answer.question, is_correct=True).first()

            result_data = {
                'is_locked': True,
                'unlocks_at': deadline,
                'question': PollQuestionSerializer(latest_answer.question).data,
                'last_result': {
                    'questionId': latest_answer.question.id,
                    'selected': latest_answer.selected_option.key,
                    'correct': correct_option.key if correct_option else None,
                }
            }
            serializer = UserPollStatusSerializer(result_data)
            return Response(serializer.data)
        else:
            # User has not answered this week, give them the latest question
            newest_question = PollQuestion.objects.filter(is_active=True).order_by('-created_at').first()

            if not newest_question:
                return Response({"detail": "No active poll questions available."}, status=status.HTTP_404_NOT_FOUND)

            result_data = {
                'is_locked': False,
                'unlocks_at': None,
                'question': PollQuestionSerializer(newest_question).data,
                'last_result': None
            }
            serializer = UserPollStatusSerializer(result_data)
            return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def submit(self, request):
        user = request.user
        
        today = timezone.now().date()
        start_of_week = today - timedelta(days=today.weekday())
        if PollAnswer.objects.filter(user=user, created_at__gte=start_of_week).exists():
            return Response({"detail": "You have already answered this week's poll."}, status=status.HTTP_403_FORBIDDEN)

        serializer = PollAnswerSerializer(data=request.data)
        if serializer.is_valid():
            question = serializer.validated_data['question']
            selected_option = serializer.validated_data['selected_option']

            if selected_option.question != question:
                return Response({"detail": "The selected option does not belong to this question."}, status=status.HTTP_400_BAD_REQUEST)

            PollAnswer.objects.create(
                user=user,
                question=question,
                selected_option=selected_option
            )

            correct_option = PollOption.objects.filter(question=question, is_correct=True).first()
            deadline = get_next_sunday_deadline()
            
            result_data = {
                 'is_locked': True,
                'unlocks_at': deadline,
                'question': PollQuestionSerializer(question).data,
                'last_result': {
                    'questionId': question.id,
                    'selected': selected_option.key,
                    'correct': correct_option.key if correct_option else None,
                }
            }
            response_serializer = UserPollStatusSerializer(result_data)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def statistics(self, request):
        # Leaderboard: Top 10 users with most correct answers
        leaderboard = User.objects.annotate(
            correct_answers=Count('pollanswer', filter=Q(pollanswer__selected_option__is_correct=True))
        ).filter(correct_answers__gt=0).order_by('-correct_answers')[:10]

        # Recent Participants: 10 most recent unique users, annotated with their last answer time
        recent_participants = User.objects.annotate(
            last_answered=Max('pollanswer__created_at')
        ).filter(last_answered__isnull=False).order_by('-last_answered')[:10]

        data = {
            'leaderboard': leaderboard,
            'recent_participants': recent_participants
        }
        
        serializer = PollStatisticsSerializer(data)
        return Response(serializer.data)


class ContactFormSubmitView(APIView):
    permission_classes = [AllowAny] # Allow anyone to submit

    def post(self, request, *args, **kwargs):
        serializer = ContactSubmissionSerializer(data=request.data)
        if serializer.is_valid():
            # If user is authenticated, link the submission to them
            if request.user.is_authenticated:
                serializer.save(user=request.user)
            else:
                serializer.save()
            return Response({"detail": "Съобщението е изпратено успешно!"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class NotificationListView(generics.ListAPIView):
    queryset = Notification.objects.filter(enabled=True).order_by('-created_at')
    serializer_class = NotificationSerializer
    permission_classes = [AllowAny]


class EventListView(generics.ListAPIView):
    queryset = Event.objects.filter(published=True).order_by('start_datetime')
    serializer_class = EventSerializer
    permission_classes = [AllowAny]


class TermsOfServiceView(generics.GenericAPIView):
    serializer_class = TermsOfServiceSerializer
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        # Fetch the latest Terms of Service entry
        latest_tos = TermsOfService.objects.order_by('-date').first()
        if latest_tos:
            serializer = self.get_serializer(latest_tos)
            return Response(serializer.data)
        return Response({"detail": "No Terms of Service found."}, status=status.HTTP_404_NOT_FOUND)