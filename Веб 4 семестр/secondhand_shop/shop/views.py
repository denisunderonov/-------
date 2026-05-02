from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .forms import ProductForm, PromotionForm
from .models import Brand, Category, Order, Product, Promotion, User


def catalog(request):
    qs = Product.objects.select_related('seller', 'category', 'brand').prefetch_related(
        'favorited_by',
    )
    qs = qs.filter(status=Product.Status.FOR_SALE)
    qs = qs.exclude(condition=Product.Condition.FAIR)

    seller_email = request.GET.get('seller_email', '').strip()
    if seller_email:
        qs = qs.filter(seller__email__icontains=seller_email)

    category_id = request.GET.get('category')
    if category_id:
        qs = qs.filter(category__pk=category_id)

    qs = qs.order_by('price', 'title')

    catalog_url = reverse('shop:catalog')
    return render(
        request,
        'shop/catalog.html',
        {
            'products': qs,
            'categories': Category.objects.all(),
            'catalog_url': catalog_url,
        },
    )


def product_detail(request, pk):
    product = (
        Product.objects.select_related('seller', 'category', 'brand')
        .prefetch_related('favorited_by__user', 'order_items')
        .filter(pk=pk)
        .first()
    )
    if not product:
        return redirect('shop:catalog')
    other_by_seller = product.seller.products.exclude(pk=product.pk).filter(
        status=Product.Status.FOR_SALE,
    )[:6]
    other_in_category = (
        product.category.products.exclude(pk=product.pk)
        .filter(status=Product.Status.FOR_SALE)
        .order_by('-created_at')[:6]
    )
    return render(
        request,
        'shop/product_detail.html',
        {
            'product': product,
            'other_by_seller': other_by_seller,
            'other_in_category': other_in_category,
            'catalog_url': reverse('shop:catalog'),
            'str_demo': str(product),
        },
    )


def category_products(request, pk):
    category = get_object_or_404(Category, pk=pk)
    products = (
        category.products.select_related('seller', 'category', 'brand')
        .filter(status=Product.Status.FOR_SALE)
        .exclude(condition=Product.Condition.FAIR)
        .order_by('-created_at')
    )
    return render(
        request,
        'shop/category_products.html',
        {'category': category, 'products': products},
    )


def lab2_report(request):
    now = timezone.now()
    today = timezone.localdate()

    new_arrivals_since = now - timedelta(days=14)
    new_arrivals_qs = Product.objects.filter(created_at__gte=new_arrivals_since)

    active_promotions = Promotion.objects.filter(starts_at__lte=now, ends_at__gte=now)

    orders_today = Order.objects.filter(created_at__date=today)

    category_with_counts = (
        Category.objects.annotate(product_count=Count('products'))
        .order_by('-product_count', 'name')[:15]
    )

    brand_with_avg = (
        Brand.objects.annotate(avg_price=Avg('products__price'))
        .filter(avg_price__isnull=False)
        .order_by('-avg_price')[:15]
    )

    revenue = Order.objects.filter(
        status__in=(Order.Status.DONE, Order.Status.PAID),
    ).aggregate(total=Sum('total_price'))['total']

    discount_candidates = (
        Product.objects.warehouse_discount_candidates(min_days_on_shelf=30)
        .select_related('seller', 'category', 'brand')
        .prefetch_related('favorited_by')
    )
    users_with_favorite_counts = User.objects.prefetch_related('favorite_products').annotate(
        favorites_count=Count('favorite_products'),
    ).order_by('-favorites_count', 'email')
    contains_demo_qs = Product.objects.filter(title__contains='Демо')
    icontains_demo_qs = Product.objects.filter(title__icontains='демо')
    product_values = list(
        Product.objects.values('id', 'title', 'price').order_by('-id')[:5],
    )
    product_titles = list(
        Product.objects.values_list('title', flat=True).order_by('-id')[:5],
    )
    products_total = Product.objects.count()
    has_active_promotions = active_promotions.exists()

    return render(
        request,
        'shop/lab2_report.html',
        {
            'now': now,
            'today': today,
            'new_arrivals_count': new_arrivals_qs.count(),
            'active_promotions': active_promotions,
            'orders_today_count': orders_today.count(),
            'category_with_counts': category_with_counts,
            'brand_with_avg': brand_with_avg,
            'revenue': revenue or 0,
            'discount_candidates': discount_candidates[:20],
            'users_with_favorite_counts': users_with_favorite_counts,
            'contains_demo_count': contains_demo_qs.count(),
            'icontains_demo_count': icontains_demo_qs.count(),
            'product_values': product_values,
            'product_titles': product_titles,
            'products_total': products_total,
            'has_active_promotions': has_active_promotions,
            'lab2_url': reverse('shop:lab2_report'),
        },
    )


@login_required
def orm_mutation_demo(request):
    if request.method == 'POST':
        updated = Product.objects.filter(
            title__icontains='[Демо]',
            status=Product.Status.MODERATION,
        ).update(status=Product.Status.FOR_SALE)
        Promotion.objects.get_or_create(
            title='[УдалитьDemo] Техническая акция',
            defaults={
                'discount_percent': 1,
                'starts_at': timezone.now(),
                'ends_at': timezone.now() + timedelta(days=1),
            },
        )
        deleted_count, _ = Promotion.objects.filter(
            title__contains='[УдалитьDemo]',
        ).delete()
        return redirect(f"{reverse('shop:lab2_report')}?updated={updated}&deleted={deleted_count}")
    return redirect('shop:lab2_report')


@login_required
def product_create(request):
    form = ProductForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        form.save()
        return redirect('shop:catalog')
    return render(
        request,
        'shop/product_form.html',
        {'form': form, 'title': 'Добавление товара', 'submit_label': 'Создать'},
    )


@login_required
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    form = ProductForm(request.POST or None, request.FILES or None, instance=product)
    if form.is_valid():
        form.save()
        return redirect(product.get_absolute_url())
    return render(
        request,
        'shop/product_form.html',
        {'form': form, 'title': 'Редактирование товара', 'submit_label': 'Сохранить'},
    )


@login_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.delete()
        return redirect('shop:catalog')
    return render(
        request,
        'shop/product_confirm_delete.html',
        {'product': product},
    )


def promotion_list(request):
    promotions = Promotion.objects.order_by('-starts_at')
    return render(request, 'shop/promotion_list.html', {'promotions': promotions})


@login_required
def promotion_create(request):
    form = PromotionForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('shop:promotion_list')
    return render(
        request,
        'shop/promotion_form.html',
        {'form': form, 'title': 'Добавление акции', 'submit_label': 'Создать'},
    )


@login_required
def promotion_update(request, pk):
    promotion = get_object_or_404(Promotion, pk=pk)
    form = PromotionForm(request.POST or None, instance=promotion)
    if form.is_valid():
        form.save()
        return redirect('shop:promotion_list')
    return render(
        request,
        'shop/promotion_form.html',
        {'form': form, 'title': 'Редактирование акции', 'submit_label': 'Сохранить'},
    )


@login_required
def promotion_delete(request, pk):
    promotion = get_object_or_404(Promotion, pk=pk)
    if request.method == 'POST':
        promotion.delete()
        return redirect('shop:promotion_list')
    return render(
        request,
        'shop/promotion_confirm_delete.html',
        {'promotion': promotion},
    )
