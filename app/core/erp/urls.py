from django.urls import path
from core.erp.views.producto.views import *
from core.erp.views.flujo.views import *
from core.erp.views.informe.views import *


app_name = 'erp'

urlpatterns = [
    
    # producto
    path('producto/list/', ProductoListView.as_view(), name='producto_list'),
    path('producto/add/', ProductoCreateView.as_view(), name='producto_create'),
    path('producto/update/<int:pk>/', ProductoUpdateView.as_view(), name='producto_update'),
    path('producto/delete/<int:pk>/', ProductoDeleteView.as_view(), name='producto_delete'),
    # flujo
    path('flujo/list/', FlujoListView.as_view(), name='flujo_list'),
    path('flujo/add/', FlujoCreateView.as_view(), name='flujo_create'),
    path('flujo/update/<int:pk>/', FlujoUpdateView.as_view(), name='flujo_update'),
    path('flujo/delete/<int:pk>/', FlujoDeleteView.as_view(), name='flujo_delete'),
    # informe
    path('informe/list/', InformeListView.as_view(), name='informe_list'),
    path('informe/add/', InformeCreateView.as_view(), name='informe_create'),
    path('informe/update/<int:pk>/', InformeUpdateView.as_view(), name='informe_update'),
    path('informe/delete/<int:pk>/', InformeDeleteView.as_view(), name='informe_delete'),

    path('informe/tablas/', InformeView.as_view(), name='informe_tablas'),
    path('informe/tablas/pdf/', InformePDF.as_view(), name='informe_tablas_pdf'),
]