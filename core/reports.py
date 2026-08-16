from datetime import timedelta
from decimal import Decimal

from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import DecimalField, ExpressionWrapper, F, Sum
from django.db.models.functions import TruncDate
from django.shortcuts import render
from django.utils import timezone

from orders.models import Order, OrderItem
from shop.models import Product

LINE_TOTAL = ExpressionWrapper(
    F('price') * F('quantity'),
    output_field=DecimalField(max_digits=14, decimal_places=2),
)


def _period_stats(start, end):
    """Count and revenue (items + shipping) for paid orders in [start, end)."""
    orders = Order.objects.filter(
        payment_status='paid',
        created_at__date__gte=start,
        created_at__date__lt=end,
    )
    items_total = (
        OrderItem.objects.filter(
            order__payment_status='paid',
            order__created_at__date__gte=start,
            order__created_at__date__lt=end,
        ).aggregate(total=Sum(LINE_TOTAL))['total'] or Decimal('0')
    )
    shipping_total = orders.aggregate(total=Sum('shipping_price'))['total'] or Decimal('0')
    return {'count': orders.count(), 'revenue': items_total + shipping_total}


@staff_member_required
def sales_report(request):
    today = timezone.localdate()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    paid_orders = Order.objects.filter(payment_status='paid')

    total_orders = Order.objects.count()
    paid_orders_count = paid_orders.count()
    items_total = (
        OrderItem.objects.filter(order__payment_status='paid')
        .aggregate(total=Sum(LINE_TOTAL))['total'] or Decimal('0')
    )
    shipping_total = paid_orders.aggregate(total=Sum('shipping_price'))['total'] or Decimal('0')
    total_revenue = items_total + shipping_total
    avg_order_value = (
        total_revenue / paid_orders_count if paid_orders_count else Decimal('0')
    )

    periods = [
        {
            'label': 'Hoy',
            'start': today,
            **_period_stats(today, today + timedelta(days=1)),
        },
        {
            'label': 'Esta semana',
            'start': week_start,
            **_period_stats(week_start, today + timedelta(days=1)),
        },
        {
            'label': 'Este mes',
            'start': month_start,
            **_period_stats(month_start, today + timedelta(days=1)),
        },
    ]

    top_products = list(
        OrderItem.objects.filter(order__payment_status='paid')
        .values('product__name')
        .annotate(quantity_sold=Sum('quantity'), revenue=Sum(LINE_TOTAL))
        .order_by('-quantity_sold', '-revenue')[:5]
    )

    start_date = today - timedelta(days=13)
    end_date = today + timedelta(days=1)
    day_revenue = {}
    daily_items = (
        OrderItem.objects.filter(
            order__payment_status='paid',
            order__created_at__date__gte=start_date,
            order__created_at__date__lt=end_date,
        )
        .annotate(date=TruncDate('order__created_at'))
        .values('date')
        .annotate(rev=Sum(LINE_TOTAL))
        .values_list('date', 'rev')
    )
    daily_shipping = (
        Order.objects.filter(
            payment_status='paid',
            created_at__date__gte=start_date,
            created_at__date__lt=end_date,
        )
        .annotate(date=TruncDate('created_at'))
        .values('date')
        .annotate(rev=Sum('shipping_price'))
        .values_list('date', 'rev')
    )
    for date, rev in list(daily_items) + list(daily_shipping):
        day_revenue[date] = day_revenue.get(date, Decimal('0')) + (rev or Decimal('0'))
    daily_revenue = [
        (start_date + timedelta(days=i), day_revenue.get(start_date + timedelta(days=i), Decimal('0')))
        for i in range(14)
    ]

    return render(request, 'admin/core/sales_report.html', {
        'title': 'Reporte de ventas',
        'total_orders': total_orders,
        'paid_orders_count': paid_orders_count,
        'total_revenue': total_revenue,
        'avg_order_value': avg_order_value,
        'periods': periods,
        'top_products': top_products,
        'daily_revenue': daily_revenue,
    })


@staff_member_required
def stock_report(request):
    try:
        threshold = int(request.GET.get('threshold', 5))
    except (TypeError, ValueError):
        threshold = 5
    threshold = max(threshold, 0)

    low_stock = (
        Product.objects.filter(stock__lte=threshold)
        .select_related('category', 'brand')
        .order_by('stock', 'name')
    )
    return render(request, 'admin/core/stock_report.html', {
        'title': 'Reporte de stock',
        'threshold': threshold,
        'total_products': Product.objects.count(),
        'low_stock_count': low_stock.count(),
        'low_stock': low_stock,
    })