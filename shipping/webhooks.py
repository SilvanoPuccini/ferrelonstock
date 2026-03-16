import json
import hmac
import hashlib
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
from .models import Shipment, ShipmentEvent, Carrier


def verify_webhook_secret(request):
    """Verifica el token de autenticación del webhook."""
    token = request.headers.get('X-Webhook-Secret', '')
    if not token:
        token = request.GET.get('secret', '')
    return token == settings.SHIPPING_WEBHOOK_SECRET


# =====================================================
# WEBHOOK GENÉRICO (para testing y carriers sin API)
# =====================================================

@csrf_exempt
@require_POST
def generic_webhook(request):
    """
    Webhook genérico que acepta actualizaciones de estado.
    
    POST /shipping/webhook/update/
    Headers: X-Webhook-Secret: tu-secret
    Body JSON:
    {
        "tracking_number": "AND-2026-001234",
        "status": "in_transit",
        "description": "Paquete en tránsito hacia destino",
        "location": "Centro de distribución CABA"
    }
    
    Status válidos: preparing, picked_up, in_transit, out_for_delivery, delivered, failed, returned
    """
    if not verify_webhook_secret(request):
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    tracking_number = data.get('tracking_number', '')
    status = data.get('status', '')
    description = data.get('description', '')
    location = data.get('location', '')

    if not tracking_number or not status:
        return JsonResponse({'error': 'tracking_number and status required'}, status=400)

    valid_statuses = ['preparing', 'picked_up', 'in_transit', 'out_for_delivery', 'delivered', 'failed', 'returned']
    if status not in valid_statuses:
        return JsonResponse({'error': f'Invalid status. Valid: {valid_statuses}'}, status=400)

    try:
        shipment = Shipment.objects.get(tracking_number=tracking_number)
    except Shipment.DoesNotExist:
        return JsonResponse({'error': 'Shipment not found'}, status=404)

    # Actualizar estado del shipment
    shipment.status = status
    if status == 'delivered':
        shipment.delivered_at = timezone.now()
    shipment.save()

    # Crear evento
    ShipmentEvent.objects.create(
        shipment=shipment,
        status=status,
        description=description or f'Estado actualizado: {status}',
        location=location,
    )

    # Sincronizar estado del pedido
    order = shipment.order
    if status == 'delivered':
        order.status = 'delivered'
    elif status in ['in_transit', 'out_for_delivery', 'picked_up']:
        order.status = 'shipped'
    elif status in ['failed', 'returned']:
        order.status = 'shipped'  # Se mantiene como shipped pero el shipment dice failed
    order.save()

    return JsonResponse({
        'ok': True,
        'order_id': order.pk,
        'shipment_status': shipment.get_status_display(),
        'order_status': order.get_status_display(),
    })


# =====================================================
# WEBHOOK ANDREANI
# =====================================================

@csrf_exempt
@require_POST
def andreani_webhook(request):
    """
    Webhook para notificaciones de Andreani.
    Andreani envía un POST con el estado del envío.
    
    Docs: https://developers.andreani.com/
    
    Mapeo de estados Andreani → FerrelonStock:
    - Pendiente de ingreso → preparing
    - En distribución → in_transit
    - En camino → out_for_delivery
    - Entregado → delivered
    - No entregado → failed
    - Devuelto → returned
    """
    if not verify_webhook_secret(request):
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    # Mapeo de estados Andreani
    andreani_status_map = {
        'pendiente_ingreso': 'preparing',
        'ingresado': 'picked_up',
        'en_distribucion': 'in_transit',
        'en_camino': 'out_for_delivery',
        'entregado': 'delivered',
        'no_entregado': 'failed',
        'devuelto': 'returned',
    }

    tracking = data.get('numero_envio', data.get('tracking_number', ''))
    andreani_status = data.get('estado', data.get('status', '')).lower().replace(' ', '_')
    description = data.get('descripcion', data.get('description', ''))
    location = data.get('sucursal', data.get('location', ''))

    if not tracking:
        return JsonResponse({'error': 'tracking number required'}, status=400)

    status = andreani_status_map.get(andreani_status, '')
    if not status:
        return JsonResponse({'error': f'Unknown Andreani status: {andreani_status}'}, status=400)

    try:
        shipment = Shipment.objects.get(tracking_number=tracking)
    except Shipment.DoesNotExist:
        return JsonResponse({'error': 'Shipment not found'}, status=404)

    shipment.status = status
    if status == 'delivered':
        shipment.delivered_at = timezone.now()
    shipment.save()

    ShipmentEvent.objects.create(
        shipment=shipment,
        status=status,
        description=description or f'Andreani: {andreani_status}',
        location=location,
    )

    order = shipment.order
    if status == 'delivered':
        order.status = 'delivered'
    elif status in ['in_transit', 'out_for_delivery', 'picked_up']:
        order.status = 'shipped'
    order.save()

    return JsonResponse({'ok': True, 'status': status})


# =====================================================
# WEBHOOK OCA
# =====================================================

@csrf_exempt
@require_POST
def oca_webhook(request):
    """
    Webhook para notificaciones de OCA.
    
    Docs: https://developers.oca.com.ar/
    
    Mapeo de estados OCA → FerrelonStock:
    """
    if not verify_webhook_secret(request):
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    oca_status_map = {
        'imposicion': 'picked_up',
        'en_distribucion': 'in_transit',
        'en_camino': 'out_for_delivery',
        'entregado': 'delivered',
        'no_entregado': 'failed',
        'devuelto_destino': 'returned',
    }

    tracking = data.get('numero_pieza', data.get('tracking_number', ''))
    oca_status = data.get('estado', data.get('status', '')).lower().replace(' ', '_')
    description = data.get('motivo', data.get('description', ''))
    location = data.get('sucursal', data.get('location', ''))

    if not tracking:
        return JsonResponse({'error': 'tracking number required'}, status=400)

    status = oca_status_map.get(oca_status, '')
    if not status:
        return JsonResponse({'error': f'Unknown OCA status: {oca_status}'}, status=400)

    try:
        shipment = Shipment.objects.get(tracking_number=tracking)
    except Shipment.DoesNotExist:
        return JsonResponse({'error': 'Shipment not found'}, status=404)

    shipment.status = status
    if status == 'delivered':
        shipment.delivered_at = timezone.now()
    shipment.save()

    ShipmentEvent.objects.create(
        shipment=shipment,
        status=status,
        description=description or f'OCA: {oca_status}',
        location=location,
    )

    order = shipment.order
    if status == 'delivered':
        order.status = 'delivered'
    elif status in ['in_transit', 'out_for_delivery', 'picked_up']:
        order.status = 'shipped'
    order.save()

    return JsonResponse({'ok': True, 'status': status})
