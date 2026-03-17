from django.core.management.base import BaseCommand
from shop.models import Product, Category
from core.models import TeamMember


PRODUCT_IMAGES = {
    'termico-bipolar-20a': 'media/products/Térmico_bipolar_20A_NDzLJBK_h2vgfc',
    'cable-unipolar-25mm-100m': 'media/products/Cable_unipolar_2_QwGKd86.5mm__x_100m_ksodj0',
    'griferia-monocomando-cocina': 'media/products/Grifería_monocomando_cocina_gXfTezs_x7i460',
    'cano-pvc-110mm-4m': 'media/products/Caño_PVC_110mm_x_4m_wJl1VNy_qzvf7y',
    'rodillo-antigota-22cm': 'media/products/Rodillo_antigota_22cm_OgNsjMg_uabpao',
    'membrana-liquida-20l': 'media/products/Membrana_líquida_20L_5R4KCuY_dyvnws',
    'pintura-latex-interior-20l': 'media/products/Pintura_látex_interior_20L_7eqyN02_klh4mt',
    'arena-gruesa-m3': 'media/products/Arena_gruesa_x_m3_Fo7MHOw_mjdxgq',
    'ladrillo-hueco-12x18x33': 'media/products/Ladrillo_hueco_12x18x33_KmwLbbH_no7zqu',
    'hierro-construccion-8mm': 'media/products/Hierro_de_construcción__8mm__x_12m_ii7pe0y_bh4tef',
    'cemento-portland-50kg': 'media/products/Cemento_Portlan_50kg_7e3vLlM_kzt9bb',
    'atornillador-inalambrico-12v': 'media/products/Atornillador_inalámbrico_12V_1COD2AU_rhiozy',
    'sierra-caladora-600w': 'media/products/Sierra_caladora_600W_xko6jJh_odrt7x',
    'amoladora-angular-850w': 'media/products/amoladora-angular-850w01_zkbAjh0_kwv29e',
    'taladro-percutor-750w': 'media/products/Taladro_percutor_13mm_750W_whTrWg7_zvdmqr',
    'alicate-universal-8': 'media/products/Alicate_universal_8_guuhrju_vln4bh',
    'cinta-metrica-5m': 'media/products/Cinta_métrica_5m_lZv1flf_lcp8ox',
    'llave-francesa-10': 'media/products/llave-francesa-10_FedkHAP_m5fve5',
    'destornillador-phillips-ph2': 'media/products/destornillador_filip_j2HCDBe_jpgni3',
    'martillo-carpintero-500g': 'media/products/martillo-carpintero-500g_cDRGvRk_2xazauY_s8dwa5',
}

CATEGORY_IMAGES = {
    'electricidad': 'media/categories/catalogo_porductos_electricos_tPXfrVP_pv5omy',
    'herramientas-electricas': 'media/categories/ctalago_herramientas_electricas_MRZULsS_eyq5pw',
    'herramientas-manuales': 'media/categories/categoria_herramientas_manuales_22S8DYa_chn2po',
    'materiales-construccion': 'media/categories/categoria_materiales_construccion_FJl3ciV_owo0xg',
    'pinturas-revestimientos': 'media/categories/categoria_pintura_y_revestimiento_iIn4dN4_ahnzsg',
    'plomeria': 'media/categories/categoria_plomeria_vXeTpUe_juzccf',
}

TEAM_IMAGES = {
    'Ing. Carlos Méndez': 'media/team/Ing_0whSLOW._Carlos_Méndez_ygputu',
    'Arq. Elena Rossi': 'media/team/Arq_tDMeGUS._Elena_Rossi_sce8ea',
    'Luis García': 'media/team/Luis_García_BBobksI_vkz3pw',
    'Ing. Roberto Blanco': 'media/team/Ing_m01RdOb._Roberto_Blanco_x2ncqg',
    'Dra. Marina Silva': 'media/team/Dra_RxcG5jB._Marina_Silva_dqukpd',
    'Héctor Torres': 'media/team/Héctor_Torres_LJZMtur_u3ucua',
}


class Command(BaseCommand):
    help = 'Asigna las rutas de Cloudinary a productos, categorías y equipo'

    def handle(self, *args, **options):
        assigned = 0

        # Productos
        self.stdout.write('\n--- Productos ---')
        for slug, image_path in PRODUCT_IMAGES.items():
            try:
                product = Product.objects.get(slug=slug)
                product.image = image_path
                product.save(update_fields=['image'])
                assigned += 1
                self.stdout.write(f'  OK: {product.name}')
            except Product.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'  No encontrado: {slug}'))

        # Categorías
        self.stdout.write('\n--- Categorías ---')
        for slug, image_path in CATEGORY_IMAGES.items():
            try:
                cat = Category.objects.get(slug=slug)
                cat.image = image_path
                cat.save(update_fields=['image'])
                assigned += 1
                self.stdout.write(f'  OK: {cat.name}')
            except Category.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'  No encontrado: {slug}'))

        # Equipo
        self.stdout.write('\n--- Equipo ---')
        for name, photo_path in TEAM_IMAGES.items():
            try:
                member = TeamMember.objects.get(name=name)
                member.photo = photo_path
                member.save(update_fields=['photo'])
                assigned += 1
                self.stdout.write(f'  OK: {member.name}')
            except TeamMember.DoesNotExist:
                # Crear el miembro si no existe
                member = TeamMember.objects.create(
                    name=name,
                    role=TEAM_ROLES.get(name, ''),
                    photo=photo_path,
                    order=list(TEAM_IMAGES.keys()).index(name) + 1
                )
                assigned += 1
                self.stdout.write(f'  Creado: {member.name}')

        self.stdout.write(self.style.SUCCESS(f'\nTotal asignadas: {assigned}'))


TEAM_ROLES = {
    'Ing. Carlos Méndez': 'Director de Logística',
    'Arq. Elena Rossi': 'Especialista de Corralón',
    'Luis García': 'Jefe de Ventas Industriales',
    'Ing. Roberto Blanco': 'Gerente de Operaciones',
    'Dra. Marina Silva': 'Head of Customer Experience',
    'Héctor Torres': 'Control de Calidad & Inventario',
}
