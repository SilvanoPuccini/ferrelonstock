import hashlib
import hmac
import stripe
import mercadopago
from decimal import Decimal
from django.conf import settings
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from orders.models import Order
from orders.emails import send_payment_confirmation
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
        payment_intent_data={
            'metadata': {
                'order_id': order.pk,
            }
        },
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
        # Validar el binding entre la sesión de Stripe y este pedido.
        # Un session_id forjado o perteneciente a otro pedido NUNCA marca pagado.
        metadata = session.metadata if session.metadata else {}
        if (
            metadata.get('order_id') == str(order.pk)
            and session.amount_total == int(order.total)
            and session.payment_status == 'paid'
        ):
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
            # Email al cliente (falla silencioso, nunca rompe el flujo).
            send_payment_confirmation(order)
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

    # El estado real del pago lo cambia SOLO el webhook de MercadoPago.
    # NUNCA se marca pagado ni se crea un Payment a partir de GET params,
    # porque cualquier usuario puede forjarlos (?status=approved).
    if order.payment_status == 'paid':
        messages.success(request, _('¡Pago realizado con éxito con Mercado Pago!'))
    else:
        payment_status = request.GET.get('status')
        if payment_status == 'approved':
            messages.info(request, _('Estamos confirmando tu pago. Te avisaremos cuando esté acreditado.'))
        elif payment_status == 'pending':
            messages.info(request, _('Tu pago está pendiente de confirmación. Te avisaremos cuando se acredite.'))
        else:
            messages.info(request, _('Estamos confirmando tu pago. Si no se acredita, podés intentar con otro método.'))

    return redirect('orders:order_detail', order_id=order.pk)


@login_required
def payment_cancel(request, order_id):
    order = get_object_or_404(Order, pk=order_id, user=request.user)
    messages.warning(request, _('El pago fue cancelado. Podés intentar de nuevo.'))
    return redirect('payments:payment_select', order_id=order.pk)


# =====================================================
# WEBHOOKS FIRMADOS
# =====================================================

def _mark_order_paid(order, provider, transaction_id):
    """Marca el pedido como pagado. Solo debe llamarse desde un webhook verificado."""
    with transaction.atomic():
        Payment.objects.update_or_create(
            order=order,
            defaults={
                'provider': provider,
                'transaction_id': transaction_id,
                'status': 'completed',
                'amount': order.total,
            }
        )
        order.status = 'preparing'
        order.payment_status = 'paid'
        order.save(update_fields=['status', 'payment_status'])

    # Email al cliente (falla silencioso, nunca rompe el webhook).
    send_payment_confirmation(order)


def _resolve_stripe_order(charge):
    """Resuelve el pedido asociado a un objeto Charge de Stripe."""
    metadata = charge.get('metadata') or {}
    order_id = metadata.get('order_id')
    if order_id:
        try:
            return Order.objects.get(pk=order_id)
        except (Order.DoesNotExist, ValueError):
            pass
    payment_intent = charge.get('payment_intent')
    if payment_intent:
        payment = Payment.objects.filter(
            provider='stripe', transaction_id=payment_intent
        ).first()
        if payment:
            return payment.order
    return None


@csrf_exempt
@require_POST
def stripe_webhook(request):
    """
    POST /payments/webhook/stripe/
    Verifica la firma con el secreto del webhook (STRIPE_WEBHOOK_SECRET).
    Maneja: checkout.session.completed, charge.refunded, checkout.session.expired.
    """
    payload = request.body
    sig_header = request.headers.get('Stripe-Signature', '')
    secret = settings.STRIPE_WEBHOOK_SECRET

    if not secret:
        return HttpResponse(status=400)

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, secret)
    except (ValueError, stripe.SignatureVerificationError):
        # Firma inválida: responder 400 para que Stripe reintente/reporte.
        return HttpResponse(status=400)

    event_type = event.get('type')
    data = event.get('data', {}).get('object', {})

    if event_type == 'checkout.session.completed':
        with transaction.atomic():
            metadata = data.get('metadata') or {}
            order_id = metadata.get('order_id')
            if not order_id:
                return HttpResponse(status=200)
            try:
                order = Order.objects.select_for_update().get(pk=order_id)
            except (Order.DoesNotExist, ValueError):
                return HttpResponse(status=200)
            # Validar el monto: no marcar pagado si la sesión no corresponde al pedido.
            if int(data.get('amount_total') or 0) != int(order.total):
                return HttpResponse(status=200)
            _mark_order_paid(order, 'stripe', data.get('payment_intent') or '')
    elif event_type == 'charge.refunded':
        order = _resolve_stripe_order(data)
        if order:
            with transaction.atomic():
                Payment.objects.update_or_create(
                    order=order,
                    defaults={
                        'provider': 'stripe',
                        'status': 'refunded',
                        'amount': order.total,
                    }
                )
                order.payment_status = 'refunded'
                order.save(update_fields=['payment_status'])
    elif event_type == 'checkout.session.expired':
        metadata = data.get('metadata') or {}
        order_id = metadata.get('order_id')
        if order_id:
            try:
                order = Order.objects.select_for_update().get(pk=order_id)
            except (Order.DoesNotExist, ValueError):
                return HttpResponse(status=200)
            if order.payment_status != 'paid':
                order.payment_status = 'failed'
                order.save(update_fields=['payment_status'])

    return HttpResponse(status=200)


def _verify_mp_signature(request):
    """
    Verifica la firma HMAC-SHA256 de un webhook de MercadoPago v2.

    Cadena a firmar (según documentación de MercadoPago):
        id:{data.id};request-id:{x-request-id};ts:{ts};
    El header x-signature trae: ts=<ts>,v1=<hash>
    """
    secret = settings.MP_WEBHOOK_SECRET
    if not secret:
        return False

    x_signature = request.headers.get('x-signature', '')
    if not x_signature:
        return False

    parts = {}
    for item in x_signature.split(','):
        item = item.strip()
        if '=' in item:
            key, value = item.split('=', 1)
            parts[key.strip()] = value.strip()

    ts = parts.get('ts', '')
    v1 = parts.get('v1', '')
    if not ts or not v1:
        return False

    data_id = request.GET.get('data.id', '')
    request_id = request.headers.get('x-request-id', '')

    manifest = f'id:{data_id};request-id:{request_id};ts:{ts};'
    expected = hmac.new(
        secret.encode('utf-8'), manifest.encode('utf-8'), hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected, v1)


@csrf_exempt
@require_POST
def mp_webhook(request):
    """
    POST /payments/webhook/mp/?type=payment&data.id=123
    Verifica la firma (x-signature) con MP_WEBHOOK_SECRET y consulta el pago
    en la API de MercadoPago para obtener su estado real y external_reference.
    """
    if not _verify_mp_signature(request):
        return HttpResponse(status=400)

    data_id = request.GET.get('data.id', '')
    if not data_id:
        return HttpResponse(status=400)

    sdk = mercadopago.SDK(settings.MP_ACCESS_TOKEN)
    payment_response = sdk.payment().get(data_id)
    payment = payment_response.get('response') or {}
    status = payment.get('status', '')
    order_id = payment.get('external_reference', '')

    if not order_id:
        return HttpResponse(status=200)
    try:
        order = Order.objects.select_for_update().get(pk=order_id)
    except (Order.DoesNotExist, ValueError):
        return HttpResponse(status=200)

    if status == 'approved':
        _mark_order_paid(order, 'mercadopago', data_id)
    elif status in ('rejected', 'cancelled', 'charged_back'):
        with transaction.atomic():
            Payment.objects.update_or_create(
                order=order,
                defaults={
                    'provider': 'mercadopago',
                    'status': 'failed',
                    'amount': order.total,
                }
            )
            order.payment_status = 'failed'
            order.save(update_fields=['payment_status'])
    elif status in ('pending', 'in_process', 'authorized'):
        with transaction.atomic():
            Payment.objects.update_or_create(
                order=order,
                defaults={
                    'provider': 'mercadopago',
                    'status': 'pending',
                    'amount': order.total,
                }
            )

    return HttpResponse(status=200)
