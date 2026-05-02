"""Команда загрузки демонстрационных данных для витрины и страницы /shop/lab2/."""
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from shop.models import (
    Brand,
    Category,
    Favorite,
    Order,
    OrderItem,
    Product,
    Promotion,
)

User = get_user_model()

DEMO_PREFIX = '[Демо]'


class Command(BaseCommand):
    help = 'Создаёт тестовые категории, бренды, пользователей, товары, акции и заказы для показа лаб. 2.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Удалить старые демо-данные (товары с заголовком [Демо]) и создать заново.',
        )

    def handle(self, *args, **options):
        force = options['force']
        if Product.objects.filter(title__startswith=DEMO_PREFIX).exists() and not force:
            self.stdout.write(
                self.style.WARNING(
                    'Демо-данные уже есть. Запусти с --force чтобы пересоздать, '
                    'или открой /shop/ и /shop/lab2/.',
                ),
            )
            return

        with transaction.atomic():
            if force:
                self._purge_demo()

            cat_coats, _ = Category.objects.get_or_create(name='Верхняя одежда')
            cat_shoes, _ = Category.objects.get_or_create(name='Обувь')
            cat_access, _ = Category.objects.get_or_create(name='Аксессуары')

            br_zara, _ = Brand.objects.get_or_create(name='Zara')
            br_uni, _ = Brand.objects.get_or_create(name='Uniqlo')
            br_vint, _ = Brand.objects.get_or_create(name='Vintage')

            seller1 = self._get_or_create_user(
                email='demo-seller1@example.com',
                username='demo_seller1',
                name='Оля (продавец)',
                password='demo123',
            )
            seller2 = self._get_or_create_user(
                email='demo-seller2@example.com',
                username='demo_seller2',
                name='Макс (продавец)',
                password='demo123',
            )
            buyer = self._get_or_create_user(
                email='demo-buyer@example.com',
                username='demo_buyer',
                name='Катя (покупатель)',
                password='demo123',
            )

            now = timezone.now()
            old_warehouse = now - timedelta(days=45)
            mid_warehouse = now - timedelta(days=10)
            recent_created = now - timedelta(days=5)
            old_created = now - timedelta(days=60)

            specs = [
                {
                    'title': f'{DEMO_PREFIX} Пальто бежевое',
                    'price': Decimal('3200.00'),
                    'seller': seller1,
                    'category': cat_coats,
                    'brand': br_zara,
                    'condition': Product.Condition.LIKE_NEW,
                    'storage_tier': Product.StorageTier.STANDARD,
                    'warehouse_received_at': old_warehouse,
                    'created_offset': recent_created,
                },
                {
                    'title': f'{DEMO_PREFIX} Куртка джинсовая',
                    'price': Decimal('2100.50'),
                    'seller': seller1,
                    'category': cat_coats,
                    'brand': br_uni,
                    'condition': Product.Condition.GOOD,
                    'storage_tier': Product.StorageTier.EXPRESS,
                    'warehouse_received_at': old_warehouse,
                    'created_offset': old_created,
                },
                {
                    'title': f'{DEMO_PREFIX} Кроссовки белые',
                    'price': Decimal('1890.00'),
                    'seller': seller2,
                    'category': cat_shoes,
                    'brand': br_zara,
                    'condition': Product.Condition.NEW,
                    'storage_tier': Product.StorageTier.STANDARD,
                    'warehouse_received_at': mid_warehouse,
                    'created_offset': recent_created,
                },
                {
                    'title': f'{DEMO_PREFIX} Ботинки кожаные',
                    'price': Decimal('4500.00'),
                    'seller': seller2,
                    'category': cat_shoes,
                    'brand': br_vint,
                    'condition': Product.Condition.GOOD,
                    'storage_tier': Product.StorageTier.STANDARD,
                    'warehouse_received_at': None,
                    'created_offset': recent_created,
                },
                {
                    'title': f'{DEMO_PREFIX} Шарф шерстяной',
                    'price': Decimal('450.00'),
                    'seller': seller1,
                    'category': cat_access,
                    'brand': br_uni,
                    'condition': Product.Condition.LIKE_NEW,
                    'storage_tier': Product.StorageTier.EXPRESS,
                    'warehouse_received_at': old_warehouse,
                    'created_offset': now - timedelta(days=3),
                },
                {
                    'title': f'{DEMO_PREFIX} Рюкзак городской',
                    'price': Decimal('1200.00'),
                    'seller': seller2,
                    'category': cat_access,
                    'brand': br_zara,
                    'condition': Product.Condition.GOOD,
                    'storage_tier': Product.StorageTier.STANDARD,
                    'warehouse_received_at': now - timedelta(days=35),
                    'created_offset': recent_created,
                },
            ]

            products = []
            for spec in specs:
                off = spec.pop('created_offset')
                p = Product.objects.create(
                    title=spec['title'],
                    description='Автоматически создано командой seed_demo.',
                    size='M',
                    price=spec['price'],
                    condition=spec['condition'],
                    status=Product.Status.FOR_SALE,
                    storage_tier=spec['storage_tier'],
                    seller=spec['seller'],
                    category=spec['category'],
                    brand=spec['brand'],
                    warehouse_received_at=spec['warehouse_received_at'],
                    source_url='https://example.com/demo-product',
                )
                Product.objects.filter(pk=p.pk).update(created_at=off)
                p.refresh_from_db()
                products.append(p)

            Promotion.objects.get_or_create(
                title=f'{DEMO_PREFIX} Весенняя распродажа',
                defaults={
                    'discount_percent': 15,
                    'starts_at': now - timedelta(days=1),
                    'ends_at': now + timedelta(days=7),
                },
            )
            Promotion.objects.get_or_create(
                title=f'{DEMO_PREFIX} Прошлогодняя акция',
                defaults={
                    'discount_percent': 25,
                    'starts_at': now - timedelta(days=400),
                    'ends_at': now - timedelta(days=300),
                },
            )
            Promotion.objects.get_or_create(
                title=f'{DEMO_PREFIX} Скоро: лето',
                defaults={
                    'discount_percent': 10,
                    'starts_at': now + timedelta(days=10),
                    'ends_at': now + timedelta(days=20),
                },
            )

            p1, p2 = products[0], products[1]
            Favorite.objects.get_or_create(user=buyer, product=p1)
            Favorite.objects.get_or_create(user=buyer, product=products[2])
            Favorite.objects.get_or_create(user=seller1, product=products[3])

            order = Order.objects.create(
                user=buyer,
                status=Order.Status.PAID,
                total_price=p1.price + p2.price,
            )
            Order.objects.filter(pk=order.pk).update(created_at=timezone.now())
            OrderItem.objects.create(order=order, product=p1, price=p1.price)
            OrderItem.objects.create(order=order, product=p2, price=p2.price)

            Order.objects.create(
                user=buyer,
                status=Order.Status.DONE,
                total_price=Decimal('500.00'),
            )

        self.stdout.write(self.style.SUCCESS('Готово: демо-данные загружены.'))
        self.stdout.write('  Каталог: /shop/')
        self.stdout.write('  Лаб. 2:  /shop/lab2/')
        self.stdout.write('  Логины (пароль demo123): demo-seller1@, demo-seller2@, demo-buyer@example.com')

    def _purge_demo(self):
        buyer = User.objects.filter(email='demo-buyer@example.com').first()
        if buyer:
            Order.objects.filter(user=buyer).delete()
            Favorite.objects.filter(user=buyer).delete()
        seller1 = User.objects.filter(email='demo-seller1@example.com').first()
        if seller1:
            Favorite.objects.filter(user=seller1).delete()
        Product.objects.filter(title__startswith=DEMO_PREFIX).delete()
        Promotion.objects.filter(title__startswith=DEMO_PREFIX).delete()

    def _get_or_create_user(self, *, email, username, name, password):
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': username,
                'name': name,
                'role': User.Role.USER,
            },
        )
        if created:
            user.set_password(password)
            user.save()
        return user
