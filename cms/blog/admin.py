from blog.models import Posts, Category, UserProfile, Comments, PollQuestion, PollOption, PollAnswer, ContactSubmission, Notification, TermsOfService, Event, PostImage, BellSongSuggestion, PrivacyPolicy, MemeOfWeek, Cookie, SiteSettings
from django.contrib import admin
from django.utils.safestring import mark_safe
from django.db import models
import markdown
import re # Import regex module
from unfold_markdown.widgets import MarkdownWidget
from unfold.widgets import UnfoldBooleanSwitchWidget

class PostImageInline(admin.TabularInline):
    model = PostImage
    extra = 5 # Show 5 empty forms for multiple file uploads by default

@admin.register(Posts)
class PostsAdmin(admin.ModelAdmin):
    readonly_fields_base = ('author', 'created_at')
    list_display = ('title', 'author', 'published', 'created_at')
    list_filter = ('published', 'category', 'created_at')
    search_fields = ('title', 'content')
    exclude = ('author',)
    inlines = [PostImageInline] # Use the simple inline

    # V V V ДОБАВЯНЕ НА MARKDOWN ВИДЖЕТ V V V
    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == "content":
            kwargs["widget"] = MarkdownWidget(attrs={"rows": 25})
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    # V V V КОРЕКЦИЯ НА READONLY_FIELDS V V V
    def get_readonly_fields(self, request, obj=None):
        user = request.user
        base_fields = list(self.readonly_fields_base)
        if not user.has_perm('blog.can_allow_posts'):
            base_fields.append('allowed')
        return tuple(base_fields)

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.author = request.user
        super().save_model(request, obj, form, change)

    # V V V КОРЕКЦИЯ НА GET_QUERYSET V V V
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        user = request.user
        if user.is_superuser:
            return qs
        if user.has_perm('blog.can_view_all_pnp_posts'):
            return qs
        if user.has_perm('blog.can_view_all_posts'):
            return qs.filter(published=True)
        if user.has_perm('blog.view_only_posts'):
            return qs.filter(author=user)
        return qs.filter(author=user, published=True)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'short_name')
    search_fields = ('full_name',)

@admin.register(Comments)
class CommentsAdmin(admin.ModelAdmin):
    readonly_fields_base = ('user', 'content' ,'created_at', 'post')
    list_display = ('user', 'content', 'created_at', 'post')
    search_fields = ('user', 'content')

class PollOptionInline(admin.TabularInline):
    model = PollOption
    extra = 4
    max_num = 4
    verbose_name = "Опция"
    verbose_name_plural = "Опции"

@admin.register(PollQuestion)
class PollQuestionAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_date', 'end_date', 'created_at')
    list_filter = ('start_date', 'end_date')
    search_fields = ('title', 'subtitle', 'code')
    inlines = [PollOptionInline]

@admin.register(PollAnswer)
class PollAnswerAdmin(admin.ModelAdmin):
    list_display = ('user', 'question', 'selected_option', 'created_at')
    list_filter = ('created_at', 'question')
    search_fields = ('user__username', 'question__title')
    readonly_fields = ('user', 'question', 'selected_option', 'created_at')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

@admin.register(BellSongSuggestion)
class BellSongSuggestionAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'slot', 'status', 'votes', 'submitted_at', 'embedded_media_display')
    list_filter = ('status', 'slot')
    search_fields = ('title', 'link', 'user__username')
    readonly_fields = ('user', 'submitted_at', 'title', 'link', 'embedded_media_display')
    fieldsets = (
        (None, {
            'fields': ('title', 'link', 'embedded_media_display', 'user', 'submitted_at')
        }),
        ('Настройки на предложението', {
            'fields': ('slot', 'note', 'status', 'votes')
        }),
    )

    def embedded_media_display(self, obj):
        if not obj.link:
            return "Няма линк"

        # More robust YouTube regex
        youtube_match = re.search(r'(?:https?://)?(?:www\.)?(?:m\.)?(?:youtube\.com|youtu\.be)/(?:watch\?v=|embed/|v/|)([a-zA-Z0-9_-]{11})(?:\S+)?', obj.link)
        # More robust Spotify regex for tracks/episodes
        spotify_match = re.search(r'(?:https?://)?(?:www\.)?(?:open\.spotify\.com)/(?:track|episode)/([a-zA-Z0-9]{22})(?:\S+)?', obj.link)

        if youtube_match:
            video_id = youtube_match.group(1)
            youtube_direct_url = f"https://www.youtube.com/watch?v={video_id}"
            return mark_safe(
                f'<a href="{youtube_direct_url}" target="_blank">Гледай в YouTube: {obj.title}</a>'
            )
        elif spotify_match:
            track_id = spotify_match.group(1)
            # Ensure correct embed URL for Spotify
            return mark_safe(f'<iframe src="https://open.spotify.com/embed/track/{track_id}" width="300" height="152" frameborder="0" allowtransparency="true" allow="encrypted-media"></iframe>')
        else:
            return f'<a href="{obj.link}" target="_blank">{obj.link}</a> (Неподдържан формат)'

    embedded_media_display.short_description = "Медия"

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('text', 'enabled', 'created_at')
    list_filter = ('enabled', 'created_at')
    search_fields = ('text',)
    readonly_fields = ('created_at',)

@admin.register(ContactSubmission)
class ContactSubmissionAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'submitted_at')
    list_filter = ('submitted_at',)
    search_fields = ('name', 'email', 'message')
    readonly_fields = ('name', 'email', 'message', 'submitted_at', 'user')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

@admin.register(TermsOfService)
class TermsOfServiceAdmin(admin.ModelAdmin):
    list_display = ('user', 'content_preview', 'date')
    list_filter = ('date',)
    search_fields = ('user__username', 'content')

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == "content":
            kwargs["widget"] = MarkdownWidget()
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if not hasattr(obj, 'user') or not obj.user:
            obj.user = request.user
        super().save_model(request, obj, form, change)

    def content_preview(self, obj):
        if obj.content:
            html = markdown.markdown(obj.content)
            return mark_safe(html[:150] + "..." if len(html) > 150 else html)
        return "-"
    content_preview.short_description = 'Преглед'

@admin.register(PrivacyPolicy)
class PrivacyPolicyAdmin(admin.ModelAdmin):
    list_display = ('user', 'content_preview', 'date')
    list_filter = ('date',)
    search_fields = ('user__username', 'content')

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == "content":
            kwargs["widget"] = MarkdownWidget()
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if not hasattr(obj, 'user') or not obj.user:
            obj.user = request.user
        super().save_model(request, obj, form, change)

    def content_preview(self, obj):
        if obj.content:
            html = markdown.markdown(obj.content)
            return mark_safe(html[:150] + "..." if len(html) > 150 else html)
        return "-"
    content_preview.short_description = 'Преглед'

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_datetime', 'location', 'category', 'attendees_text', 'published', 'created_at')
    list_filter = ('published', 'category', 'start_datetime')
    search_fields = ('title', 'description', 'location', 'attendees_text')
    readonly_fields = ('created_at',)
    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == "description":
            kwargs["widget"] = MarkdownWidget(attrs={"rows": 10})
        return super().formfield_for_dbfield(db_field, request, **kwargs)

@admin.register(PostImage)
class PostImageAdmin(admin.ModelAdmin):
    list_display = ('post', 'image_preview') # Add image_preview to list_display
    list_filter = ('post',)
    readonly_fields = ('image_preview',) # Make image_preview readonly on the change form

    def image_preview(self, obj):
        if obj.image:
            # Assuming MEDIA_URL is correctly configured, adjust width/height as needed
            return mark_safe(f'<img src="{obj.image.url}" style="max-width: 150px; max-height: 150px;" />')
        return "Няма изображение"
    image_preview.short_description = "Преглед на изображението"

@admin.register(MemeOfWeek)
class MemeOfWeekAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'image_preview', 'is_approved', 'votes', 'created_at')
    list_filter = ('is_approved', 'created_at')
    search_fields = ('title', 'user__username')
    readonly_fields = ('user', 'created_at', 'image_preview')
    exclude = ('voted_by',)

    def image_preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" style="max-width: 150px; max-height: 150px;" />')
        return "Няма изображение"
    image_preview.short_description = "Изображение"

@admin.register(Cookie.ConsentRecord)
class ConsentRecordAdmin(admin.ModelAdmin):
    list_display = ('user_display', 'ip_address', 'consent_status', 'timestamp', 'policy_version')
    list_filter = ('consent_status', 'policy_version')
    search_fields = ('ip_address', 'user__username')
    readonly_fields = ('user', 'ip_address', 'consent_status', 'timestamp', 'policy_version')

    def has_add_permission(self, request):
        return False # Records are created via API, not admin

    def has_change_permission(self, request, obj=None):
        return False # Records should not be changeable

    def user_display(self, obj):
        return obj.user.username if obj.user else "Анонимен"
    user_display.short_description = "Потребител"

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'maintenance_mode', 'enable_bell_suggestions', 'enable_weekly_poll', 'enable_meme_of_the_week')

    def __str__(self):
        return "Настройки на сайта"

    def changelist_view(self, request, extra_context=None):
        from django.http import HttpResponseRedirect
        from django.urls import reverse

        obj, created = SiteSettings.objects.get_or_create(pk=1)
        return HttpResponseRedirect(reverse('admin:blog_sitesettings_change', args=(obj.pk,)))

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if isinstance(db_field, models.BooleanField):
            kwargs["widget"] = UnfoldBooleanSwitchWidget()
        return super().formfield_for_dbfield(db_field, request, **kwargs)