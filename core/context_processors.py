from django.conf import settings


def languages(request):
    return {
        'LANGUAGES': settings.LANGUAGES,
    }


def categories_nav(request):
    from shop.models import Category, Brand
    return {
        'categories_nav': Category.objects.all(),
        'brands_nav': Brand.objects.all(),
    }
