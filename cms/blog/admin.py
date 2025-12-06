from blog.models import Posts, Category, UserProfile, Comments
from django.contrib import admin
#from django.contrib.auth.models import User
from unfold_markdown.widgets import MarkdownWidget

@admin.register(Posts)
class PostsAdmin(admin.ModelAdmin):
    readonly_fields_base = ('author', 'created_at')
    list_display = ('title', 'author', 'published', 'created_at')
    list_filter = ('published', 'category', 'created_at')
    search_fields = ('title', 'content')
    exclude = ('author',)


    # V V V ДОБАВЯНЕ НА MARKDOWN ВИДЖЕТ V V V
    def formfield_for_dbfield(self, db_field, request, **kwargs):
        # Проверяваме дали текущото поле е 'content'
        if db_field.name == "content":
            # Прилагаме UnfoldMarkdownWidget за Markdown форматиране
            kwargs["widget"] = MarkdownWidget(
                # Можете да коригирате размера на полето тук
                attrs={"rows": 25}
            )
        # Връщаме стандартния виджет за всички останали полета
        return super().formfield_for_dbfield(db_field, request, **kwargs)


    # V V V КОРЕКЦИЯ НА READONLY_FIELDS V V V
    def get_readonly_fields(self, request, obj=None):
        user = request.user
        base_fields = list(self.readonly_fields_base)

        # Ако потребителят НЯМА разрешение да одобрява, полето 'allowed' става read-only
        if not user.has_perm('blog.can_allow_posts'):
            # Предполагам, че 'allowed' е полето за одобрение/публикуване
            base_fields.append('allowed')

        return tuple(base_fields)

    def save_model(self, request, obj, form, change):
        # Задаваме автора само при първоначално създаване
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

@admin.register(Comments)
class CommentsAdmin(admin.ModelAdmin):
    readonly_fields_base = ('user', 'content' ,'created_at', 'post')
    list_display = ('user', 'content', 'created_at', 'post')
    search_fields = ('user', 'content')
