from rest_framework import viewsets, generics, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Q, Max
from django.contrib.auth.models import User
from .models import Posts, Comments, PollQuestion, PollAnswer, PollOption, ContactSubmission, Notification, Event, TermsOfService, BellSongSuggestion, PrivacyPolicy, MemeOfWeek, Cookie, SiteSettings
from .serializer import (
    PostSerializer, RegisterSerializer, CommentSerializer,
    PollQuestionSerializer, UserPollStatusSerializer, PollAnswerSerializer,
    PollStatisticsSerializer, ContactSubmissionSerializer, NotificationSerializer,
    EventSerializer, TermsOfServiceSerializer, BellSongSuggestionSerializer,
    PrivacyPolicySerializer, MemeOfWeekSerializer, ConsentRecordSerializer, SiteSettingsSerializer
)

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

class PostViewSet(viewsets.ModelViewSet):
    queryset = Posts.objects.filter(published=True, allowed=True).order_by('-created_at')
    serializer_class = PostSerializer
    http_method_names = ['get', 'head', 'options']

class MemeOfWeekViewSet(viewsets.ModelViewSet):
    serializer_class = MemeOfWeekSerializer
    http_method_names = ['get', 'post', 'head', 'options']

    def get_queryset(self):
        if self.action == 'list':
            return MemeOfWeek.objects.filter(is_approved=True).order_by('-votes', '-created_at')
        return MemeOfWeek.objects.all()

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            self.permission_classes = [AllowAny]
        else:
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    def perform_create(self, serializer):
        site_settings, created = SiteSettings.objects.get_or_create(pk=1)
        if not site_settings.enable_meme_of_the_week:
            raise PermissionDenied("Feature 'Meme of the Week' is currently disabled.")
        serializer.save(user=self.request.user)

class RegisterView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    queryset = User.objects.all()
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        site_settings, created = SiteSettings.objects.get_or_create(pk=1)
        if not site_settings.enable_user_registration:
            return Response(
                {"detail": "User registration is currently disabled."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().post(request, *args, **kwargs)

class BellSongSuggestionCreateAPIView(generics.CreateAPIView):
    queryset = BellSongSuggestion.objects.all()
    serializer_class = BellSongSuggestionSerializer
    permission_classes = [IsAuthenticated]
    def perform_create(self, serializer):
        site_settings, created = SiteSettings.objects.get_or_create(pk=1)
        if not site_settings.enable_bell_suggestions:
            raise PermissionDenied("Feature 'Bell Suggestions' is currently disabled.")
        serializer.save(user=self.request.user, status='pending')

class ApprovedBellSongListView(generics.ListAPIView):
    queryset = BellSongSuggestion.objects.filter(status='approved').order_by('-votes', '-submitted_at')
    serializer_class = BellSongSuggestionSerializer
    permission_classes = [AllowAny]

    def get_serializer_context(self):
        return {'request': self.request}

class BellSongVoteView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, pk):
        song = get_object_or_404(BellSongSuggestion, pk=pk)
        if song.status != 'approved':
            return Response({'detail': 'You can only vote on approved songs.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if user has already voted
        if request.user in song.voted_by.all():
            return Response({'detail': 'You have already voted for this song.'}, status=status.HTTP_400_BAD_REQUEST)

        # Add user to voters and increment vote count
        song.voted_by.add(request.user)
        song.votes += 1
        song.save(update_fields=['votes'])
        
        # Pass context to serializer to access the request
        serializer = BellSongSuggestionSerializer(song, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

class MemeVoteView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, pk):
        meme = get_object_or_404(MemeOfWeek, pk=pk)
        if not meme.is_approved:
            return Response({'detail': 'You can only vote on approved memes.'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if user has already voted
        if request.user in meme.voted_by.all():
            return Response({'detail': 'You have already voted for this meme.'}, status=status.HTTP_400_BAD_REQUEST)

        # Add user to voters and increment vote count
        meme.voted_by.add(request.user)
        meme.votes += 1
        meme.save(update_fields=['votes'])

        # Pass context to serializer to access the request
        serializer = MemeOfWeekSerializer(meme, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class CommentList(generics.ListAPIView):
    serializer_class = CommentSerializer
    http_method_names = ['get', 'post', 'options', 'head']
    def get_queryset(self):
        post_id = self.kwargs.get('post_pk')
        if not post_id:
            return Comments.objects.none()
        post = get_object_or_404(Posts, id=post_id)
        return Comments.objects.filter(post=post).order_by('-created_at')

class AddCommentAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, post_pk):
        post = get_object_or_404(Posts, id=post_pk)
        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            comment = serializer.save(user=request.user, post=post)
            return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
        site_settings, created = SiteSettings.objects.get_or_create(pk=1)
        if not site_settings.enable_weekly_poll:
            return Response({"detail": "Polls feature is currently disabled."}, status=status.HTTP_404_NOT_FOUND)

        user = request.user
        now = timezone.now()
        
        active_question = PollQuestion.objects.filter(start_date__lte=now, end_date__gte=now).first()

        if not active_question:
            return Response({"detail": "No active poll questions available at this time."}, status=status.HTTP_404_NOT_FOUND)

        latest_answer = PollAnswer.objects.filter(user=user, question=active_question).first()

        if latest_answer:
            correct_option = PollOption.objects.filter(question=active_question, is_correct=True).first()
            data = {
                'is_locked': True,
                'unlocks_at': active_question.end_date,
                'question': active_question,
                'last_result': {
                    'questionId': active_question.id,
                    'selected': latest_answer.selected_option.key,
                    'correct': correct_option.key if correct_option else None
                }
            }
            return Response(UserPollStatusSerializer(data).data)
        else:
            data = {
                'is_locked': False,
                'unlocks_at': None,
                'question': active_question,
                'last_result': None
            }
            return Response(UserPollStatusSerializer(data).data)

    @action(detail=False, methods=['post'])
    def submit(self, request):
        site_settings, created = SiteSettings.objects.get_or_create(pk=1)
        if not site_settings.enable_weekly_poll:
            return Response({"detail": "Polls feature is currently disabled."}, status=status.HTTP_403_FORBIDDEN)

        user = request.user
        now = timezone.now()

        serializer = PollAnswerSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        question = serializer.validated_data['question']
        selected_option = serializer.validated_data['selected_option']
        
        active_question = PollQuestion.objects.filter(
            id=question.id, 
            start_date__lte=now, 
            end_date__gte=now
        ).first()

        if not active_question:
            return Response({"detail": "This poll is not currently active."}, status=status.HTTP_403_FORBIDDEN)

        if selected_option.question != active_question:
            return Response({"detail": "The selected option does not belong to this question."}, status=status.HTTP_400_BAD_REQUEST)

        if PollAnswer.objects.filter(user=user, question=active_question).exists():
            return Response({"detail": "You have already answered this poll."}, status=status.HTTP_403_FORBIDDEN)
        
        PollAnswer.objects.create(user=user, question=active_question, selected_option=selected_option)

        correct_option = PollOption.objects.filter(question=active_question, is_correct=True).first()
        data = {
            'is_locked': True,
            'unlocks_at': active_question.end_date,
            'question': active_question,
            'last_result': {
                'questionId': active_question.id,
                'selected': selected_option.key,
                'correct': correct_option.key if correct_option else None
            }
        }
        return Response(UserPollStatusSerializer(data).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def statistics(self, request):
        leaderboard = User.objects.annotate(
            correct_answers=Count('pollanswer', filter=Q(pollanswer__selected_option__is_correct=True))
        ).filter(correct_answers__gt=0).order_by('-correct_answers')[:10]
        recent_participants = User.objects.annotate(
            last_answered=Max('pollanswer__created_at')
        ).filter(last_answered__isnull=False).order_by('-last_answered')[:10]
        serializer = PollStatisticsSerializer({
            'leaderboard': leaderboard,
            'recent_participants': recent_participants
        })
        return Response(serializer.data)

class ContactFormSubmitView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = ContactSubmissionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user if request.user.is_authenticated else None)
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
    def get(self, request):
        tos = TermsOfService.objects.order_by('-date').first()
        if tos:
            return Response(self.get_serializer(tos).data)
        return Response({"detail": "No Terms of Service found."}, status=status.HTTP_404_NOT_FOUND)

class PrivacyPolicyView(generics.GenericAPIView):
    serializer_class = PrivacyPolicySerializer
    permission_classes = [AllowAny]
    def get(self, request):
        pp = PrivacyPolicy.objects.order_by('-date').first()
        if pp:
            return Response(self.get_serializer(pp).data)
        return Response({"detail": "No Privacy Policy found."}, status=status.HTTP_404_NOT_FOUND)

class ConsentRecordCreateView(generics.CreateAPIView):
    queryset = Cookie.ConsentRecord.objects.all()
    serializer_class = ConsentRecordSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        ip_address = get_client_ip(self.request)
        serializer.save(user=user, ip_address=ip_address)

class SiteStatusView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    serializer_class = SiteSettingsSerializer

    def get_object(self):
        obj, created = SiteSettings.objects.get_or_create(pk=1)
        return obj

