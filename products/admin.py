from django.contrib import admin
from django.core.exceptions import ValidationError
from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    list_display = ("indented_name", "slug", "full_slug_path", "parent", "theme", "is_active")
    list_filter = ("is_active", "theme")
    search_fields = ("name", "slug")
    list_select_related = ("parent",)
    raw_id_fields = ("parent",)

    def indented_name(self, obj):
        depth = len(obj.get_ancestors())
        prefix = "\u2003" * depth  # em-space indentation
        return f"{prefix}{obj.name}"
    indented_name.short_description = "Name"

    def full_slug_path(self, obj):
        return obj.get_full_slug_path()
    full_slug_path.short_description = "Full Path"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("parent")

    def save_model(self, request, obj, form, change):
        try:
            obj.clean()
        except ValidationError as e:
            from django.contrib import messages
            messages.error(request, str(e.message))
            return
        super().save_model(request, obj, form, change)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "category", "stock", "is_active")
    list_filter = ("is_active",)
    list_select_related = ("category", "category__parent")
