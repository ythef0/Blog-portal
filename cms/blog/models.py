from django.contrib.auth.models import User
from django.db import models
from django.db.models import BooleanField


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
    banner = models.TextField(max_length=100)
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

class BellRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    likes = models.IntegerField(default=0)
    yt_id = models.CharField(max_length=25)
    approved = models.BooleanField(default=False)

    def __str__(self):
        return self.yt_id

class MemeOfWeek(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    location = models.TextField(blank=False)
    likes = models.IntegerField(default=0)
    approved = models.BooleanField(default=True)

    def __str__(self):
        return self.location

CLASS_CHOICES = (
    ('8a', '8 А'),
    ('8b', '8 Б'),
    ('8v', '8 В'),

    ('9a', '9 А'),
    ('9b', '9 Б'),
    ('9v', '9 В'),

    ('10a', '10 А'),
    ('10b', '10 Б'),
    ('10v', '10 В'),

    ('11a', '11 А'),
    ('11b', '11 Б'),
    ('11v', '11 В'),

    ('12a', '12 А'),
    ('12b', '12 Б'),)

TYPE_CHOICES = (
    ('8a', '8 А'),
    ('8b', '8 Б'),
    ('8v', '8 В'),

    ('9a', '9 А'),
    ('9b', '9 Б'),
    ('9v', '9 В'),

    ('10a', '10 А'),
    ('10b', '10 Б'),
    ('10v', '10 В'),

    ('11a', '11 А'),
    ('11b', '11 Б'),
    ('11v', '11 В'),

    ('12a', '12 А'),
    ('12b', '12 Б'),
    ('teacher', 'TEACHER'))

class UserProfile(models.Model):
    # Първият елемент в tuples е стойността, която се запазва в базата данни (напр. '10a')
    # Вторият елемент е стойността, която се показва на потребителя (напр. '10 А')
    class_name = models.CharField(
        max_length=5,  # Максимална дължина на стойността ('10v')
        choices=CLASS_CHOICES,  # ❗ Използваме choices
        blank=True,
        null=True,
        verbose_name="Клас"
    )

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
        policy_version = models.CharField(max_length=10, default='v1.0')  # Трябва да се променя ръчно

        # Опционални (за бъдещето)
        analytical_accepted = models.BooleanField(default=False)
        marketing_accepted = models.BooleanField(default=False)

        def __str__(self):
            return f"Consent: {self.consent_status} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"


class PollQuestion(models.Model):
    title = models.CharField(max_length=255, verbose_name="Заглавие")
    subtitle = models.CharField(max_length=255, blank=True, null=True, verbose_name="Подзаглавие")
    code = models.TextField(verbose_name="Код")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Създаден на")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Въпрос за анкета"
        verbose_name_plural = "Въпроси за анкети"
        ordering = ['-created_at']


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

class TermsOfUser(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False, verbose_name="Автор")
    content = models.TextField(null=False)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.content} качено на : {self.user.username}"


