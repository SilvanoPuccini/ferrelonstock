import stripe
import mercadopago
from decimal import Decimal
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from orders.models import Order
from .models import Payment

stripe.api_key = settings.STRIPE_SECRET_KEY


@login_required
def payment_select(request, order_id):
    order = get_object_or_404(Order, pk=order_id, user=request.user)
    if order.payment_status == 'paid':
        return redirect('orders:order_detail', order_id=order.pk)
    return render(request, 'payments/payment_select.html', {
        'order': order,
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
    })


@login_required
def stripe_checkout(request, order_id):
    order = get_object_or_404(Order, pk=order_id, user=request.user)

    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'clp',
                'unit_amount': int(order.total),
                'product_data': {
                    'name': f'Pedido #{order.pk} - FerrelonStock',
                },
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url=request.build_absolute_uri(
            reverse('payments:stripe_success', args=[order.pk])
        ) + '?session_id={CHECKOUT_SESSION_ID}',
        cancel_url=request.build_absolute_uri(
            reverse('payments:payment_cancel', args=[order.pk])
        ),
        metadata={
            'order_id': order.pk,
        }
    )

    return redirect(session.url)


@login_required
def stripe_success(request, order_id):
    order = get_object_or_404(Order, pk=order_id, user=request.user)
    session_id = request.GET.get('session_id')

    if session_id:
        session = stripe.checkout.Session.retrieve(session_id)
        if session.payment_status == 'paid':
            Payment.objects.update_or_create(
                order=order,
                defaults={
                    'provider': 'stripe',
                    'transaction_id': session.payment_intent,
                    'status': 'completed',
                    'amount': Decimal(str(order.total)),
                }
            )
            order.status = 'preparing'
            order.payment_status = 'paid'
            order.save()
            messages.success(request, _('¡Pago realizado con éxito!'))

    return redirect('orders:order_detail', order_id=order.pk)


@login_required
def mp_checkout(request, order_id):
    order = get_object_or_404(Order, pk=order_id, user=request.user)

    sdk = mercadopago.SDK(settings.MP_ACCESS_TOKEN)

    preference_data = {
        'items': [
            {
                'title': f'Pedido #{order.pk} - FerrelonStock',
                'quantity': 1,
                'unit_price': float(order.total),
                'currency_id': 'ARS',
            }
        ],
        'back_urls': {
            'success': request.build_absolute_uri(
                reverse('payments:mp_success', args=[order.pk])
            ),
            'failure': request.build_absolute_uri(
                reverse('payments:payment_cancel', args=[order.pk])
            ),
            'pending': request.build_absolute_uri(
                reverse('payments:mp_success', args=[order.pk])
            ),
        },
        'external_reference': str(order.pk),
    }

    preference = sdk.preference().create(preference_data)
    init_point = preference['response'].get('sandbox_init_point', preference['response'].get('init_point'))

    return redirect(init_point)


@login_required
def mp_success(request, order_id):
    order = get_object_or_404(Order, pk=order_id, user=request.user)
    payment_status = request.GET.get('status')
    payment_id = request.GET.get('payment_id', '')

    if payment_status == 'approved':
        Payment.objects.update_or_create(
            order=order,
            defaults={
                'provider': 'mercadopago',
                'transaction_id': payment_id,
                'status': 'completed',
                'amount': Decimal(str(order.total)),
            }
        )
        order.status = 'preparing'
        order.payment_status = 'paid'
        order.save()
        messages.success(request, _('¡Pago realizado con éxito con Mercado Pago!'))
    elif payment_status == 'pending':
        Payment.objects.update_or_create(
            order=order,
            defaults={
                'provider': 'mercadopago',
                'transaction_id': payment_id,
                'status': 'pending',
                'amount': Decimal(str(order.total)),
            }
        )
        messages.info(request, _('Tu pago está pendiente de confirmación.'))
    else:
        order.payment_status = 'failed'
        order.save()
        messages.error(request, _('El pago no fue aprobado. Intentá con otro método.'))

    return redirect('orders:order_detail', order_id=order.pk)


@login_required
def payment_cancel(request, order_id):
    order = get_object_or_404(Order, pk=order_id, user=request.user)
    messages.warning(request, _('El pago fue cancelado. Podés intentar de nuevo.'))
    return redirect('payments:payment_select', order_id=order.pk)
