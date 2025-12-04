from blog.models import Posts, Category
from django.contrib import admin
#from django.contrib.auth.models import User


@admin.register(Posts)
class PostsAdmin(admin.ModelAdmin):
    readonly_fields_base = ('author', 'created_at')
    list_display = ('title', 'author', 'published', 'created_at')
    list_filter = ('published', 'category', 'created_at')
    search_fields = ('title', 'content')
    exclude = ('author',)


    # V V V КОРЕКЦИЯ НА READONLY_FIELDS V V V
    def get_readonly_fields(self, request, obj=None):
        user = request.user
        base_fields = list(self.readonly_fields_base)  # ['author', 'created_at']

        # Ако потребителят НЯМА разрешение да одобрява, полето 'allowed' става read-only
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

        # 1. Суперпотребителите виждат всичко
        if user.is_superuser:
            return qs

        # 2. Може да вижда ВСИЧКИ публикации (без филтър за published)
        if user.has_perm('blog.can_view_all_posts'):
            return qs.filter(published=True)

        # 3. Може да вижда ВСИЧКИ (публикувани и непубликувани)
        if user.has_perm('blog.can_view_all_pnp_posts'):
            return qs

        # 4. Може да вижда САМО своите (дори чернови)
        if user.has_perm('blog.view_only_posts'):
            return qs.filter(author=user)

        # 5. Резервен случай: Потребителят вижда само своите ПУБЛИКУВАНИ постове
        return qs.filter(author=user, published=True)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'short_name')
    search_fields = ('full_name',)