from rest_framework import serializers
from .models import Posts,UserProfile, CLASS_CHOICES, Comments, PollQuestion, PollOption, PollAnswer, ContactSubmission, Notification, Event
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password

class PostSerializer(serializers.ModelSerializer):
    # 1. Дефинирайте ново поле, което ще извика метод
    author_username = serializers.SerializerMethodField()
    # 2. Може да използвате StringRelatedField за категорията, ако сте я дефинирали като __str__
    category_name = serializers.StringRelatedField(source='category')

    class Meta:
        model = Posts
        fields = (
            'id',
            'category',       # Запазваме ID за бъдещи филтрирания
            'category_name',  # ⬅️ Добавено: Име на категория
            'author',         # Запазваме ID на автора
            'author_username',# ⬅️ Добавено: Потребителско име
            'title',
            'banner',
            'hook',
            'content',
            'created_at',
            'published',
            'allowed'
        )

    # 3. Дефинирайте метода за получаване на потребителското име
    def get_author_username(self, obj):
        # Приемаме, че obj.author е инстанция на User модела
        return obj.author.username

class RegisterSerializer(serializers.ModelSerializer):
    # Поле за избор на клас (използваме choices, но го правим write_only)
    class_name = serializers.ChoiceField(
        choices=CLASS_CHOICES,
        write_only=True,
        required=False,
        error_messages={'invalid_choice': 'Невалиден избор на клас.'}
    )

    # Поле за парола (само за писане и с валидация)
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )

    # Поле за потвърждение на паролата (не се запазва в модела)
    password2 = serializers.CharField(
        write_only=True,
        required=True
    )

    class Meta:
        model = User
        # Включваме class_name в списъка fields, въпреки че не е част от User модела
        fields = ('username', 'password', 'password2', 'email', 'first_name', 'last_name', 'class_name')

        # Правим тези полета задължителни
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'email': {'required': True},
        }

    # Метод за валидация на всички полета
    def validate(self, attrs):
        # Проверка дали паролите съвпадат
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Паролите не съвпадат."})

        # Премахваме password2, тъй като не ни е нужно повече
        attrs.pop('password2')
        return attrs

    # Метод за създаване на обекта (User и UserProfile)
    def create(self, validated_data):
        # 1. Вземаме class_name и го премахваме от validated_data
        class_name = validated_data.pop('class_name', None)

        # 2. Създаваме стандартния User
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name']
        )
        user.set_password(validated_data['password'])
        user.save()

        # 3. Създаваме свързания UserProfile
        UserProfile.objects.create(user=user, class_name=class_name)

        return user


class CommentSerializer(serializers.ModelSerializer):
    # 1. ЕКСПЛИЦИТНО ДЕФИНИРАНО ПОЛЕ
    # post_id е тук, за да вземе стойността 'id' от свързания пост
    username = serializers.CharField(source='user.username', read_only=True)
    post_id = serializers.IntegerField(source='post.id', read_only=True)

    class Meta:
        # 2. Трябва да имате модел
        model = Comments

        # 3. ❗ ТРЯБВА ДА ВКЛЮЧИТЕ post_id в списъка fields!
        # DRF изисква това, защото сте го дефинирали в тялото на класа.
        fields = ['id', 'post_id', 'username', 'content', 'created_at']
        read_only_fields = ['id', 'created_at', 'username', 'post_id']


class PollOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PollOption
        fields = ['id','key', 'text'] 

class PollQuestionSerializer(serializers.ModelSerializer):
    options = PollOptionSerializer(many=True, read_only=True)
    id = serializers.IntegerField(read_only=False)
    class Meta:
        model = PollQuestion
        fields = ['id', 'title', 'subtitle', 'code', 'options']

class PollAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = PollAnswer
        fields = ['question', 'selected_option']


class UserPollStatusSerializer(serializers.Serializer):
    is_locked = serializers.BooleanField()
    unlocks_at = serializers.DateTimeField(allow_null=True)
    last_result = serializers.JSONField(allow_null=True) 
    question = PollQuestionSerializer(allow_null=True)


class LeaderboardEntrySerializer(serializers.ModelSerializer):
    correct_answers = serializers.IntegerField()

    class Meta:
        model = User
        fields = ['id', 'username', 'correct_answers']


class RecentParticipantSerializer(serializers.ModelSerializer):
    last_answered = serializers.DateTimeField()

    class Meta:
        model = User
        fields = ['id', 'username', 'last_answered']


class PollStatisticsSerializer(serializers.Serializer):
    leaderboard = LeaderboardEntrySerializer(many=True)
    recent_participants = RecentParticipantSerializer(many=True)


class ContactSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactSubmission
        fields = ['name', 'email', 'message']


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'text', 'enabled', 'created_at']


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = '__all__'


