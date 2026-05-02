"""Модели данных интернет-магазина."""
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.utils import timezone


class User(AbstractUser):
    """Пользователь: вход по email, имя и роль для магазина."""

    class Role(models.TextChoices):
        USER = 'user', 'Пользователь'
        ADMIN = 'admin', 'Администратор'

    email = models.EmailField('email', unique=True)
    name = models.CharField('имя', max_length=150)
    role = models.CharField(
        'роль',
        max_length=20,
        choices=Role.choices,
        default=Role.USER,
    )
    favorite_products = models.ManyToManyField(
        'Product',
        through='Favorite',
        through_fields=('user', 'product'),
        related_name='favorite_users',
        verbose_name='избранные товары',
        blank=True,
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = 'пользователь'
        verbose_name_plural = 'пользователи'

    def __str__(self):
        return f'{self.name} <{self.email}>'


class Category(models.Model):
    """Справочник категорий одежды."""

    name = models.CharField('название', max_length=100, unique=True)

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('shop:category_products', kwargs={'pk': self.pk})


class Brand(models.Model):
    """Справочник брендов."""

    name = models.CharField('название', max_length=100, unique=True)

    class Meta:
        verbose_name = 'бренд'
        verbose_name_plural = 'бренды'
        ordering = ['name']

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    """Запросы к товарам: общая логика для менеджера и цепочки ORM."""

    def for_sale(self):
        return self.filter(status=self.model.Status.FOR_SALE)


class ProductManager(models.Manager.from_queryset(ProductQuerySet)):
    """
    Собственный менеджер модели Product.

    Пример: выборка «давно на складе» для маркетинговой скидки по дате warehouse_received_at.
    """

    def warehouse_discount_candidates(self, *, min_days_on_shelf=30):
        cutoff = timezone.now() - timedelta(days=min_days_on_shelf)
        return (
            self.get_queryset()
            .for_sale()
            .filter(
                warehouse_received_at__isnull=False,
                warehouse_received_at__lte=cutoff,
            )
        )


class Product(models.Model):
    """Товар: объявление продавца в каталоге."""

    class Condition(models.TextChoices):
        NEW = 'new', 'Новое'
        LIKE_NEW = 'like_new', 'Как новое'
        GOOD = 'good', 'Хорошее'
        FAIR = 'fair', 'Удовлетворительное'

    class Status(models.TextChoices):
        FOR_SALE = 'for_sale', 'В продаже'
        SOLD = 'sold', 'Продано'
        MODERATION = 'moderation', 'На модерации'

    class StorageTier(models.TextChoices):
        STANDARD = 'standard', 'Обычное хранение'
        EXPRESS = 'express', 'Ускоренная отгрузка'

    objects = ProductManager()

    title = models.CharField('название', max_length=255)
    description = models.TextField('описание', blank=True)
    size = models.CharField('размер', max_length=50, blank=True)
    price = models.DecimalField('цена', max_digits=10, decimal_places=2)
    condition = models.CharField(
        'состояние',
        max_length=20,
        choices=Condition.choices,
        default=Condition.GOOD,
    )
    status = models.CharField(
        'статус',
        max_length=20,
        choices=Status.choices,
        default=Status.MODERATION,
    )
    storage_tier = models.CharField(
        'тип хранения',
        max_length=20,
        choices=StorageTier.choices,
        default=StorageTier.STANDARD,
    )
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name='продавец',
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='products',
        verbose_name='категория',
    )
    brand = models.ForeignKey(
        Brand,
        on_delete=models.PROTECT,
        related_name='products',
        verbose_name='бренд',
    )
    created_at = models.DateTimeField('дата размещения', auto_now_add=True)
    warehouse_received_at = models.DateTimeField(
        'дата поступления на склад',
        null=True,
        blank=True,
        help_text='В БД хранится момент времени (UTC с учётом USE_TZ). '
        'По разнице с текущим моментом (timezone.now()) считаем «сколько дней на складе» для скидок.',
    )
    photo = models.ImageField(
        'фото товара',
        upload_to='products/photos/',
        blank=True,
        null=True,
    )
    quality_report = models.FileField(
        'файл проверки качества',
        upload_to='products/reports/',
        blank=True,
        null=True,
    )
    source_url = models.URLField(
        'ссылка на источник',
        blank=True,
    )

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('shop:product_detail', kwargs={'pk': self.pk})

    def days_on_shelf(self):
        """Сколько полных суток товар лежит на складе (если дата склада задана)."""
        if not self.warehouse_received_at:
            return None
        now = timezone.now()
        delta = now - self.warehouse_received_at
        return max(0, delta.days)


class Promotion(models.Model):
    """
    Акция: интервал действий в БД (starts_at, ends_at).
    Активность проверяем относительно timezone.now() — «сейчас по часовому поясу проекта».
    """

    title = models.CharField('название', max_length=200)
    discount_percent = models.PositiveSmallIntegerField('скидка, %', default=10)
    starts_at = models.DateTimeField('начало')
    ends_at = models.DateTimeField('окончание')

    class Meta:
        verbose_name = 'акция'
        verbose_name_plural = 'акции'
        ordering = ['-starts_at']

    def __str__(self):
        return self.title

    def is_current(self):
        now = timezone.now()
        return self.starts_at <= now <= self.ends_at


class Order(models.Model):
    """Заказ покупателя."""

    class Status(models.TextChoices):
        NEW = 'new', 'Новый'
        PAID = 'paid', 'Оплачен'
        SHIPPED = 'shipped', 'Отправлен'
        DONE = 'done', 'Выполнен'
        CANCELLED = 'cancelled', 'Отменён'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name='покупатель',
    )
    status = models.CharField(
        'статус',
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
    )
    total_price = models.DecimalField(
        'сумма',
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
    )
    created_at = models.DateTimeField('дата создания', auto_now_add=True)

    class Meta:
        verbose_name = 'заказ'
        verbose_name_plural = 'заказы'
        ordering = ['-created_at']

    def __str__(self):
        return f'Заказ №{self.pk}' if self.pk else 'Заказ'


class OrderItem(models.Model):
    """Строка заказа: товар и цена на момент покупки."""

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='заказ',
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='order_items',
        verbose_name='товар',
    )
    price = models.DecimalField('цена в заказе', max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = 'позиция заказа'
        verbose_name_plural = 'позиции заказов'
        constraints = [
            models.UniqueConstraint(
                fields=('order', 'product'),
                name='unique_order_product',
            ),
        ]

    def __str__(self):
        return f'{self.order_id}: {self.product_id}'


class Favorite(models.Model):
    """Избранное: связь пользователь — товар."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='пользователь',
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='favorited_by',
        verbose_name='товар',
    )

    class Meta:
        verbose_name = 'избранное'
        verbose_name_plural = 'избранное'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'product'),
                name='unique_favorite_user_product',
            ),
        ]

    def __str__(self):
        return f'{self.user} → {self.product}'


class Message(models.Model):
    """Сообщение между пользователями."""

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        verbose_name='отправитель',
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_messages',
        verbose_name='получатель',
    )
    content = models.TextField('текст сообщения')
    created_at = models.DateTimeField('дата отправки', auto_now_add=True)

    class Meta:
        verbose_name = 'сообщение'
        verbose_name_plural = 'сообщения'
        ordering = ['-created_at']

    def __str__(self):
        if self.pk:
            return f'Сообщение №{self.pk}'
        return 'Сообщение'
