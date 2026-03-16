from django.http import HttpResponse
from django.template.loader import render_to_string
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Order

try:
    from xhtml2pdf import pisa
    HAS_PISA = True
except ImportError:
    HAS_PISA = False


@login_required
def download_invoice(request, order_id):
    order = get_object_or_404(Order, pk=order_id, user=request.user)
    items = order.items.select_related('product').all()

    context = {
        'order': order,
        'items': items,
    }

    if HAS_PISA:
        html = render_to_string('orders/invoice_pdf.html', context)
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="factura-{order.pk:04d}.pdf"'
        pisa.CreatePDF(html, dest=response)
        return response
    else:
        html = render_to_string('orders/invoice_pdf.html', context)
        response = HttpResponse(html, content_type='text/html')
        return response
