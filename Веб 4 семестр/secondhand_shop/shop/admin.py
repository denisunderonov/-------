"""Настройки Django Admin для приложения shop."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.http import HttpResponse
from reportlab.pdfgen import canvas

from .models import (
    User,
    Category,
    Brand,
    Product,
    Promotion,
    Order,
    OrderItem,
    Favorite,
    Message,
)


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = (
        'email',
        'display_profile_name',
        'username',
        'role',
        'is_staff',
        'is_active',
        'date_joined',
    )
    list_display_links = ('email', 'display_profile_name')
    list_filter = ('role', 'is_staff', 'is_active', 'is_superuser', 'date_joined')
    search_fields = ('email', 'username', 'name', 'first_name', 'last_name')
    date_hierarchy = 'date_joined'
    filter_horizontal = ('groups', 'user_permissions')
    readonly_fields = ('date_joined', 'last_login')
    raw_id_fields = ()

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Персональные данные', {'fields': ('username', 'name', 'role')}),
        ('Права доступа', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        ('Группы и права', {'fields': ('groups', 'user_permissions')}),
        ('Даты', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': ('email', 'username', 'name', 'role', 'password1', 'password2'),
            },
        ),
    )

    @admin.display(description='Имя в магазине')
    def display_profile_name(self, obj):
        return obj.name or '—'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'products_count')
    list_display_links = ('name',)
    search_fields = ('name',)

    @admin.display(description='Товаров')
    def products_count(self, obj):
        return obj.products.count()


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'products_count')
    list_display_links = ('name',)
    search_fields = ('name',)

    @admin.display(description='Товаров')
    def products_count(self, obj):
        return obj.products.count()


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'seller_email',
        'brand',
        'category',
        'price',
        'condition',
        'status',
        'short_description',
        'storage_tier',
        'warehouse_received_at',
        'created_at',
    )
    list_display_links = ('title', 'seller_email')
    list_filter = ('condition', 'status', 'storage_tier', 'category', 'brand')
    search_fields = (
        'title',
        'description',
        'size',
        'seller__email',
        'seller__name',
        'brand__name',
        'category__name',
    )
    date_hierarchy = 'created_at'
    raw_id_fields = ('seller',)
    readonly_fields = ('created_at',)
    actions = ('mark_as_for_sale', 'export_to_pdf')

    @admin.display(description='Email продавца')
    def seller_email(self, obj):
        return obj.seller.email

    @admin.display(description='Описание (фрагмент)')
    def short_description(self, obj):
        text = (obj.description or '').strip()
        if not text:
            return '—'
        return text[:80] + ('…' if len(text) > 80 else '')

    @admin.action(description='Сделать выбранные товары доступными к продаже')
    def mark_as_for_sale(self, request, queryset):
        updated = queryset.update(status=Product.Status.FOR_SALE)
        self.message_user(request, f'Обновлено товаров: {updated}')

    @admin.action(description='Экспортировать выбранные товары в PDF')
    def export_to_pdf(self, request, queryset):
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="products_export.pdf"'
        pdf = canvas.Canvas(response)
        y = 800

        pdf.setFont('Helvetica-Bold', 12)
        pdf.drawString(40, y, 'Экспорт выбранных товаров')
        y -= 30
        pdf.setFont('Helvetica', 10)

        for product in queryset.select_related('seller', 'category', 'brand'):
            line = (
                f'#{product.pk} | {product.title} | {product.price} | '
                f'{product.category.name} | {product.brand.name} | {product.seller.email}'
            )
            pdf.drawString(40, y, line[:115])
            y -= 20
            if y < 60:
                pdf.showPage()
                y = 800
                pdf.setFont('Helvetica', 10)

        pdf.save()
        return response


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ('title', 'discount_percent', 'starts_at', 'ends_at', 'is_current_display')
    list_filter = ('starts_at', 'ends_at')
    date_hierarchy = 'starts_at'
    search_fields = ('title',)

    @admin.display(description='Сейчас активна', boolean=True)
    def is_current_display(self, obj):
        return obj.is_current()


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    raw_id_fields = ('product',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'buyer_display',
        'status',
        'total_price',
        'items_count_display',
        'created_at',
    )
    list_display_links = ('id', 'buyer_display')
    list_filter = ('status', 'created_at')
    search_fields = ('user__email', 'user__name', 'user__username')
    date_hierarchy = 'created_at'
    raw_id_fields = ('user',)
    readonly_fields = ('created_at',)
    inlines = (OrderItemInline,)

    @admin.display(description='Покупатель')
    def buyer_display(self, obj):
        return f'{obj.user.name} <{obj.user.email}>'

    @admin.display(description='Позиций в заказе')
    def items_count_display(self, obj):
        if obj.pk:
            return obj.items.count()
        return '—'


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'product', 'price')
    list_display_links = ('id',)
    list_filter = ('order__status',)
    search_fields = (
        'product__title',
        'order__user__email',
        'order__user__name',
    )
    raw_id_fields = ('order', 'product')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'product_title')
    list_display_links = ('id',)
    list_filter = ('product__category', 'product__brand')
    search_fields = (
        'user__email',
        'user__name',
        'product__title',
        'product__brand__name',
    )
    raw_id_fields = ('user', 'product')

    @admin.display(description='Товар')
    def product_title(self, obj):
        return obj.product.title


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'sender', 'receiver', 'content_preview', 'created_at')
    list_display_links = ('id',)
    list_filter = ('created_at',)
    date_hierarchy = 'created_at'
    search_fields = (
        'content',
        'sender__email',
        'receiver__email',
        'sender__name',
        'receiver__name',
    )
    raw_id_fields = ('sender', 'receiver')
    readonly_fields = ('created_at',)

    @admin.display(description='Текст (фрагмент)')
    def content_preview(self, obj):
        text = (obj.content or '').strip()
        if not text:
            return '—'
        return text[:60] + ('…' if len(text) > 60 else '')
