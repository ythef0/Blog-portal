from django.contrib.auth.models import User
from django.db import models
from django.db.models import BooleanField
from django.utils import timezone
from django.core.exceptions import ValidationError



def post_banner_upload_path(instance, filename):
    return post_media_upload_path(instance, filename, 'banner')

def post_gallery_upload_path(instance, filename):
    return post_media_upload_path(instance, filename, 'gallery')

def meme_upload_path(instance, filename):
    return f'memes/{instance.user.username}/{filename}'

class Category(models.Model):
    full_name = models.CharField(max_length=100)
    short_name = models.SlugField(max_length=100, unique=True)
    def __str__(self):
        return self.full_name

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

class Posts(models.Model):
    title = models.CharField(max_length=100, blank=False)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    banner = models.ImageField(upload_to=post_banner_upload_path, blank=True, null=True)
    hook = models.TextField(max_length=100)
    content = models.TextField(blank=False, )
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    published = BooleanField()
    allowed = models.BooleanField(default=False)

    class Meta:
        permissions = [
            ('view_only_posts', 'View only users posts'),
            ('can_view_all_posts', 'Can view all posts'),
            ('can_view_all_pnp_posts', 'Can view all post if they not published'),
            ('can_allow_posts', 'Can allow posts'),
            ('can_edit_users_post', 'Can edit users posts'),
        ]
        verbose_name = "Публикация"
        verbose_name_plural = "Публикации"

    def __str__(self):
        return self.title

class Comments(models.Model):
    content = models.TextField(blank=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    post = models.ForeignKey(Posts, on_delete=models.CASCADE)

    def __str__(self):
        return self.content


SLOT_CHOICES = (
    ('start_class', 'Начало на час'),
    ('end_class', 'Край на час'),
    ('before_lunch', 'Преди голямо междучасие'),
    ('after_lunch', 'След голямо междучасие'),
    ('morning', 'Сутрешен звънец'), # Default
    ('special', 'Специален повод'),
)

STATUS_CHOICES = (
    ('pending', 'Чакащо одобрение'),
    ('approved', 'Одобрено'),
    ('rejected', 'Отхвърлено'),
)

class BellSongSuggestion(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Потребител")
    title = models.CharField(max_length=255, verbose_name="Заглавие на песента")
    link = models.URLField(max_length=2048, verbose_name="Линк към песента") # Max length for URLs
    slot = models.CharField(max_length=20, choices=SLOT_CHOICES, default='morning', verbose_name="Кога да звучи")
    note = models.TextField(blank=True, null=True, verbose_name="Бележка")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending', verbose_name="Статус")
    submitted_at = models.DateTimeField(auto_now_add=True, verbose_name="Изпратено на")
    voted_by = models.ManyToManyField(User, related_name='voted_songs', blank=True, verbose_name="Гласували потребители")
    votes = models.IntegerField(default=0, verbose_name="Гласове")

    class Meta:
        verbose_name = "Предложение за песен за звънец"
        verbose_name_plural = "Предложения за песни за звънец"
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

class MemeOfWeek(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Потребител")
    title = models.CharField(max_length=100, blank=True, null=True, verbose_name="Заглавие")
    image = models.ImageField(upload_to=meme_upload_path, blank=True, null=True, verbose_name="Изображение")
    is_approved = models.BooleanField(default=False, verbose_name="Одобрено")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата на качване", null=True)
    voted_by = models.ManyToManyField(User, related_name='voted_memes', blank=True, verbose_name="Гласували потребители")
    votes = models.IntegerField(default=0, verbose_name="Гласове")

    class Meta:
        verbose_name = "Меме на седмицата"
        verbose_name_plural = "Мемета на седмицата"
        ordering = ['-created_at']

    def __str__(self):
        if self.title:
            return self.title
        return f"Meme by {self.user.username}"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        # ...
        return f"Профил на {self.user.username}"
# Create your models here.

class Cookie(models.Model):
    class ConsentRecord(models.Model):
        # Данни за потребителя
        user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
        ip_address = models.CharField(max_length=45, blank=True, null=True)  # До 45 за IPv6

        # Резултат
        STATUS_CHOICES = [
            ('INFORMED', 'Информиран (Необходими)'),  # Вашият случай
            ('ACCEPTED', 'Приел'),
            ('REJECTED', 'Отказал'),
        ]
        consent_status = models.CharField(max_length=10, choices=STATUS_CHOICES)

        # Доказателство
        timestamp = models.DateTimeField(auto_now_add=True)
        policy_version = models.CharField(max_length=50, default='v1.0')  # Трябва да се променя ръчно

        def __str__(self):
            return f"Consent: {self.consent_status} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"


class PollQuestion(models.Model):
    title = models.CharField(max_length=255, verbose_name="Заглавие")
    subtitle = models.CharField(max_length=255, blank=True, null=True, verbose_name="Подзаглавие")
    code = models.TextField(verbose_name="Код")
    start_date = models.DateTimeField(verbose_name="Начална дата", default=timezone.now)
    end_date = models.DateTimeField(verbose_name="Крайна дата", default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Създаден на")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Въпрос за анкета"
        verbose_name_plural = "Въпроси за анкети"
        ordering = ['-start_date']


class PollOption(models.Model):
    question = models.ForeignKey(PollQuestion, related_name='options', on_delete=models.CASCADE, verbose_name="Въпрос")
    text = models.CharField(max_length=255, verbose_name="Текст на опция")
    is_correct = models.BooleanField(default=False, verbose_name="Правилен отговор")
    key = models.CharField(max_length=1, choices=[('a', 'A'), ('b', 'B'), ('c', 'C'), ('d', 'D')], verbose_name="Ключ")

    def __str__(self):
        return f"{self.question.title} - {self.text}"

    class Meta:
        verbose_name = "Опция за анкета"
        verbose_name_plural = "Опции за анкети"
        unique_together = ('question', 'key')
        ordering = ['key']


class PollAnswer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Потребител")
    question = models.ForeignKey(PollQuestion, on_delete=models.CASCADE, verbose_name="Въпрос")
    selected_option = models.ForeignKey(PollOption, on_delete=models.CASCADE, verbose_name="Избрана опция")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Отговорено на")

    def __str__(self):
        return f"{self.user.username} answered {self.question.title}"

    class Meta:
        verbose_name = "Отговор на анкета"
        verbose_name_plural = "Отговори на анкети"
        ordering = ['-created_at']


class ContactSubmission(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Потребител")
    name = models.CharField(max_length=100, verbose_name="Име")
    email = models.EmailField(verbose_name="Имейл")
    message = models.TextField(verbose_name="Съобщение")
    submitted_at = models.DateTimeField(auto_now_add=True, verbose_name="Изпратено на")

    def __str__(self):
        return f"Съобщение от {self.name} ({self.email})"

    class Meta:
        verbose_name = "Изпратен контактен формуляр"
        verbose_name_plural = "Изпратени контактни формуляри"
        ordering = ['-submitted_at']


class Notification(models.Model):
    text = models.CharField(max_length=255, verbose_name="Текст на известието")
    enabled = models.BooleanField(default=True, verbose_name="Активирано")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Създадено на")

    def __str__(self):
        return self.text

    class Meta:
        verbose_name = "Известие"
        verbose_name_plural = "Известия"
        ordering = ['-created_at']

class TermsOfService(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False, verbose_name="Автор")
    content = models.TextField(null=False)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.content} качено на : {self.user.username}"

    class Meta:
        verbose_name = "Условие за ползване"
        verbose_name_plural = "Условия за ползване"

class PrivacyPolicy(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False, verbose_name="Автор")
    content = models.TextField(null=False)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.content} качено на : {self.user.username}"

    class Meta:
        verbose_name = "Политика за поверителност"
        verbose_name_plural = "Политики за поверителност"

# Function to define the upload path for post images and banners
def post_media_upload_path(instance, filename, field_type):
    # 'instance' can be a Post object (for banner) or a PostImage object (for gallery images)
    if isinstance(instance, Posts):
        post_id = instance.pk
    elif isinstance(instance, PostImage):
        post_id = instance.post.pk
    else:
        # Fallback or error for unexpected instance type
        post_id = 'unknown' # Or raise an error
        
    return f'posts/{post_id}/{field_type}/{filename}'


class PostImage(models.Model):
    post = models.ForeignKey(Posts, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to=post_gallery_upload_path)

    def __str__(self):
        return f"Image for post: {self.post.title}"

    class Meta:
        verbose_name = "Снимка към публикация"
        verbose_name_plural = "Снимки към публикации"


class Event(models.Model):
    title = models.CharField(max_length=255, verbose_name="Заглавие")
    start_datetime = models.DateTimeField(verbose_name="Начална дата и час")
    end_datetime = models.DateTimeField(blank=True, null=True, verbose_name="Крайна дата и час (по избор)")
    location = models.CharField(max_length=255, verbose_name="Местоположение")
    category = models.CharField(max_length=100, verbose_name="Категория")
    description = models.TextField(verbose_name="Описание")
    attendees_text = models.CharField(max_length=255, verbose_name="Участници (текст)") # To avoid 'attendees' collision
    published = models.BooleanField(default=True, verbose_name="Публикувано")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Създадено на")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Събитие"
        verbose_name_plural = "Събития"
        ordering = ['start_datetime']

class SiteSettings(models.Model):
    maintenance_mode = models.BooleanField(default=False, verbose_name="Режим на поддръжка")

    class Meta:
        verbose_name = "Настройки на сайта"
        verbose_name_plural = "Настройки на сайта"

    def save(self, *args, **kwargs):
        if not self.pk and SiteSettings.objects.exists():
            raise ValidationError('Може да съществува само един обект с настройки на сайта.')
        return super(SiteSettings, self).save(*args, **kwargs)


