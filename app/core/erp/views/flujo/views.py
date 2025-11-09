from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from core.erp.forms import FlujoForm
from core.erp.mixins import ValidatePermissionRequiredMixin
from core.erp.models import Flujo

class FlujoListView(LoginRequiredMixin, ValidatePermissionRequiredMixin, ListView):
    model = Flujo
    template_name = 'flujo/list.html'
    permission_required = 'view_flujo'

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
                for i in Flujo.objects.all():
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
        context['title'] = 'Listado de Flujos'
        context['create_url'] = reverse_lazy('erp:flujo_create')
        context['list_url'] = reverse_lazy('erp:flujo_list')
        context['entity'] = 'Flujos'
        return context


class FlujoCreateView(LoginRequiredMixin, ValidatePermissionRequiredMixin, CreateView):
    model = Flujo
    form_class = FlujoForm
    template_name = 'flujo/create.html'
    success_url = reverse_lazy('erp:flujo_list')
    permission_required = 'add_flujo'
    url_redirect = success_url

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        data = {}
        try:
            action = request.POST['action']
            if action == 'add':
                form = self.get_form()
                data = form.save()
            else:
                data['error'] = 'No ha ingresado a ninguna opción'
        except Exception as e:
            data['error'] = str(e)
        return JsonResponse(data)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Creación un Flujo'
        context['entity'] = 'Flujos'
        context['list_url'] = self.success_url
        context['action'] = 'add'
        return context


class FlujoUpdateView(LoginRequiredMixin, ValidatePermissionRequiredMixin, UpdateView):
    model = Flujo
    form_class = FlujoForm
    template_name = 'flujo/create.html'
    success_url = reverse_lazy('erp:flujo_list')
    permission_required = 'change_flujo'
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
        context['title'] = 'Edición un Flujo'
        context['entity'] = 'Flujos'
        context['list_url'] = self.success_url
        context['action'] = 'edit'
        return context


class FlujoDeleteView(LoginRequiredMixin, ValidatePermissionRequiredMixin, DeleteView):
    model = Flujo
    template_name = 'flujo/delete.html'
    success_url = reverse_lazy('erp:flujo_list')
    permission_required = 'delete_flujo'
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
        context['title'] = 'Eliminación de un Flujo'
        context['entity'] = 'Flujos'
        context['list_url'] = self.success_url
        return context
