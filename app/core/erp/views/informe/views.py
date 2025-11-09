from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.shortcuts import render
from django.views import View

from django.db.models import F, Sum, ExpressionWrapper, FloatField

from core.erp.forms import InformeForm
from core.erp.mixins import ValidatePermissionRequiredMixin
from core.erp.models import Informe, Flujo, Producto
from django.db.models import Sum
from datetime import date
import calendar
from django.http import HttpResponse
from django.template.loader import render_to_string
from io import BytesIO
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

class InformeListView(LoginRequiredMixin, ValidatePermissionRequiredMixin, ListView):
    model = Informe
    template_name = 'informe/list.html'
    permission_required = 'view_informe'

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        data = {}
        try:
            action = request.POST['action']
            if action == 'searchdata':
                data = []
                position = 1
                for i in Informe.objects.all():
                    item = i.toJSON()
                    item['position'] = position
                    data.append(item)
                    position += 1
            else:
                data['error'] = 'Ha ocurrido un error'
        except Exception as e:
            data['error'] = str(e)
        return JsonResponse(data, safe=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Listado de Informes'
        context['create_url'] = reverse_lazy('erp:informe_create')
        context['list_url'] = reverse_lazy('erp:informe_list')
        context['entity'] = 'Informes'
        return context


class InformeCreateView(LoginRequiredMixin, ValidatePermissionRequiredMixin, CreateView):
    model = Informe
    form_class = InformeForm
    template_name = 'informe/create.html'
    success_url = reverse_lazy('erp:informe_list')
    permission_required = 'add_informe'
    url_redirect = success_url

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        data = {}
        try:
            action = request.POST['action']
            if action == 'add':
                form = self.get_form()
                if form.is_valid():
                    informe = form.save(commit=False)
                    # Asegúrate de que el archivo PDF se guarda correctamente
                    if request.FILES.get('archivo_pdf'):
                        informe.archivo_pdf = request.FILES['archivo_pdf']
                    informe.save()
                    data = {'success': 'Informe guardado correctamente'}
                else:
                    data['error'] = form.errors
            else:
                data['error'] = 'No ha ingresado a ninguna opción'
        except Exception as e:
            data['error'] = str(e)
        return JsonResponse(data, safe=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Creación un Informe'
        context['entity'] = 'Informes'
        context['list_url'] = self.success_url
        context['action'] = 'add'
        return context


class InformeUpdateView(LoginRequiredMixin, ValidatePermissionRequiredMixin, UpdateView):
    model = Informe
    form_class = InformeForm
    template_name = 'informe/create.html'
    success_url = reverse_lazy('erp:informe_list')
    permission_required = 'change_informe'
    url_redirect = success_url

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        data = {}
        try:
            action = request.POST['action']
            if action == 'edit':
                form = self.get_form()
                data = form.save()
            else:
                data['error'] = 'No ha ingresado a ninguna opción'
        except Exception as e:
            data['error'] = str(e)
        return JsonResponse(data)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edición un Informe'
        context['entity'] = 'Informes'
        context['list_url'] = self.success_url
        context['action'] = 'edit'
        return context


class InformeDeleteView(LoginRequiredMixin, ValidatePermissionRequiredMixin, DeleteView):
    model = Informe
    template_name = 'informe/delete.html'
    success_url = reverse_lazy('erp:informe_list')
    permission_required = 'delete_informe'
    url_redirect = success_url

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        data = {}
        try:
            self.object.delete()
        except Exception as e:
            data['error'] = str(e)
        return JsonResponse(data)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Eliminación de un Informe'
        context['entity'] = 'Informes'
        context['list_url'] = self.success_url
        return context

class InformeView(LoginRequiredMixin, ValidatePermissionRequiredMixin, View):
    template_name = 'tablas_informe.html'

    def get(self, request, *args, **kwargs):
        try:
            mes = int(request.GET.get('mes', date.today().month))
            anio = int(request.GET.get('anio', date.today().year))
        except ValueError:
            mes = date.today().month
            anio = date.today().year

        available_months = [
            (1, "Enero"), (2, "Febrero"), (3, "Marzo"), (4, "Abril"),
            (5, "Mayo"), (6, "Junio"), (7, "Julio"), (8, "Agosto"),
            (9, "Septiembre"), (10, "Octubre"), (11, "Noviembre"), (12, "Diciembre")
        ]
        current_year = date.today().year
        available_years = list(range(current_year - 5, current_year + 1))
        weeks = calendar.monthcalendar(anio, mes)
        week_labels = [f"Semana {i+1}" for i in range(len(weeks))]

        data_products = []
        total_money = 0
        total_units_month = 0  # Nuevo: Total de unidades vendidas en el mes

        for producto in Producto.objects.all().order_by('name'):
            week_units_list = []
            week_money_list = []
            for week in weeks:
                valid_days = [dia for dia in week if dia != 0]
                if valid_days:
                    start_date = date(anio, mes, min(valid_days))
                    end_date = date(anio, mes, max(valid_days))
                    qs = Flujo.objects.filter(
                        producto=producto,
                        tipo='V',
                        created_at__date__gte=start_date,
                        created_at__date__lte=end_date
                    )
                    weekly_units = qs.aggregate(total=Sum('cantidad'))['total'] or 0
                    weekly_money = qs.aggregate(
                        total=Sum(ExpressionWrapper(F('cantidad') * F('precio'), output_field=FloatField()))
                    )['total'] or 0
                    week_units_list.append(weekly_units)
                    week_money_list.append(weekly_money)
                else:
                    week_units_list.append(0)
                    week_money_list.append(0)

            sales_qs = Flujo.objects.filter(
                producto=producto,
                tipo='V',
                created_at__year=anio,
                created_at__month=mes
            )
            total_units = sales_qs.aggregate(total=Sum('cantidad'))['total'] or 0  # Unidades vendidas en el mes
            total_money_prod = sales_qs.aggregate(
                total=Sum(ExpressionWrapper(F('cantidad') * F('precio'), output_field=FloatField()))
            )['total'] or 0
            avg_price = total_money_prod / total_units if total_units > 0 else producto.precio_venta

            total_money += total_money_prod
            total_units_month += total_units  # Acumulamos el total de unidades vendidas en el mes

            data_products.append({
                'name': producto.name,
                'price': avg_price,         # Precio promedio de venta en el mes
                'weeks': week_units_list,   # Unidades vendidas por semana
                'weeks_money': week_money_list,  # Dinero ganado por semana
                'total_sold': total_units,  # Total de unidades vendidas en el mes
                'total_money': total_money_prod,
            })

        summary_week_money = [0] * len(weeks)
        for prod in data_products:
            for i, weekly_money in enumerate(prod['weeks_money']):
                summary_week_money[i] += weekly_money
        total_money_month = sum(summary_week_money)

        context = {
            'selected_mes': mes,
            'selected_anio': anio,
            'available_months': available_months,
            'available_years': available_years,
            'week_labels': week_labels,
            'data_products': data_products,
            'summary_week_money': summary_week_money,
            'total_money_month': total_money_month,
            'total_money': total_money,
            'total_units_month': total_units_month,  # Se agrega el total de unidades vendidas
        }
        return render(request, self.template_name, context)

def obtener_contexto_informe(request):
    """Extrae el mismo contexto que se utiliza en la vista HTML."""
    try:
        mes = int(request.GET.get('mes', date.today().month))
        anio = int(request.GET.get('anio', date.today().year))
    except ValueError:
        mes = date.today().month
        anio = date.today().year

    available_months = [
        (1, "Enero"), (2, "Febrero"), (3, "Marzo"), (4, "Abril"),
        (5, "Mayo"), (6, "Junio"), (7, "Julio"), (8, "Agosto"),
        (9, "Septiembre"), (10, "Octubre"), (11, "Noviembre"), (12, "Diciembre")
    ]
    current_year = date.today().year
    available_years = list(range(current_year - 5, current_year + 1))
    weeks = calendar.monthcalendar(anio, mes)
    week_labels = [f"Semana {i+1}" for i in range(len(weeks))]

    data_products = []
    total_money = 0

    for producto in Producto.objects.all().order_by('name'):
        week_units_list = []
        week_money_list = []
        for week in weeks:
            valid_days = [dia for dia in week if dia != 0]
            if valid_days:
                start_date = date(anio, mes, min(valid_days))
                end_date = date(anio, mes, max(valid_days))
                qs = Flujo.objects.filter(
                    producto=producto,
                    tipo='V',
                    created_at__date__gte=start_date,
                    created_at__date__lte=end_date
                )
                weekly_units = qs.aggregate(total=Sum('cantidad'))['total'] or 0
                weekly_money = qs.aggregate(
                    total=Sum(ExpressionWrapper(F('cantidad') * F('precio'), output_field=FloatField()))
                )['total'] or 0
                week_units_list.append(weekly_units)
                week_money_list.append(weekly_money)
            else:
                week_units_list.append(0)
                week_money_list.append(0)

        sales_qs = Flujo.objects.filter(
            producto=producto,
            tipo='V',
            created_at__year=anio,
            created_at__month=mes
        )
        total_units = sales_qs.aggregate(total=Sum('cantidad'))['total'] or 0
        total_money_prod = sales_qs.aggregate(
            total=Sum(ExpressionWrapper(F('cantidad') * F('precio'), output_field=FloatField()))
        )['total'] or 0
        avg_price = total_money_prod / total_units if total_units > 0 else producto.precio_venta

        total_money += total_money_prod

        data_products.append({
            'name': producto.name,
            'price': avg_price,         # Precio promedio de venta en el mes
            'weeks': week_units_list,   # Unidades vendidas por semana
            'weeks_money': week_money_list,  # Dinero ganado por semana
            'total_sold': total_units,  # Total de unidades vendidas en el mes
            'total_money': total_money_prod,
        })

    summary_week_money = [0] * len(weeks)
    for prod in data_products:
        for i, weekly_money in enumerate(prod['weeks_money']):
            summary_week_money[i] += weekly_money
    total_money_month = sum(summary_week_money)

    return {
        'selected_mes': mes,
        'selected_anio': anio,
        'available_months': available_months,
        'available_years': available_years,
        'week_labels': week_labels,
        'data_products': data_products,
        'summary_week_money': summary_week_money,
        'total_money_month': total_money_month,
        'total_money': total_money,
    }


class InformePDF(LoginRequiredMixin, View):
    """
    Vista que genera el informe de ventas en PDF con ReportLab.
    """
    def get(self, request, *args, **kwargs):
        # Obtiene el contexto del informe
        context = obtener_contexto_informe(request)
        
        # Se obtiene el nombre del mes a partir del listado available_months
        mes_num = context['selected_mes']
        mes_nombre = next((nombre for (valor, nombre) in context['available_months'] if valor == mes_num), str(mes_num))
        anio = context['selected_anio']
        
        # Título y nombre de archivo
        titulo_informe = f"Informe de Ventas - {mes_nombre} {anio}"
        nombre_archivo = f"Informe {mes_nombre} {anio}.pdf"

        # Configuramos el documento PDF con márgenes para separar la tabla de los bordes
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=40,
            rightMargin=40,
            topMargin=40,
            bottomMargin=40,
            title=titulo_informe
        )
        styles = getSampleStyleSheet()
        elements = []

        # Agrega el título del informe
        title_paragraph = Paragraph(titulo_informe, styles['Title'])
        elements.append(title_paragraph)
        elements.append(Spacer(1, 20))

        # Construcción de la tabla
        header = ['Producto', 'Precio'] + context['week_labels'] + ['Total Vendidos', 'Total Ganado']
        table_data = [header]

        total_units_month = 0  # Variable para calcular el total de unidades vendidas en el mes

        for prod in context['data_products']:
            total_units_month += prod['total_sold']  # Sumar total de unidades vendidas

            row = [
                prod['name'],
                f"{prod['price']}",
            ] + [f"{venta}" for venta in prod['weeks']] + [
                f"{prod['total_sold']}",
                f"{prod['total_money']}"
            ]
            table_data.append(row)

        # Fila de resumen corregida
        summary_row = ["Resumen por Semana", ""] + [f"{s}" for s in context['summary_week_money']] + [
            f"{total_units_month}",  # Ahora muestra el total de unidades vendidas en el mes
            f"{context['total_money']}"  # Total dinero ganado en el mes
        ]
        table_data.append(summary_row)

        table = Table(table_data, hAlign='CENTER')
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.gray),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('LEFTPADDING', (0,0), (-1,-1), 5),
            ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ]))
        elements.append(table)

        # Construye el PDF
        doc.build(elements)
        pdf = buffer.getvalue()
        buffer.close()

        # Devuelve la respuesta HTTP con el PDF
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'
        response.write(pdf)
        return response