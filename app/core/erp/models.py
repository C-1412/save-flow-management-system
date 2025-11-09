from datetime import datetime

from django.db import models
from django.forms import model_to_dict

from config.settings import MEDIA_URL, STATIC_URL
from core.erp.choices import gender_choices
from core.models import BaseModel


class Producto(models.Model):
    name = models.CharField(max_length=150, verbose_name='Nombre', unique=True)
    precio_compra = models.FloatField(null=True, blank=True)
    precio_venta = models.FloatField(null=False, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def ganancia(self):
        # Si no existe precio_compra, devuelve un guion.
        if not self.precio_compra:
            return "-"
        return self.precio_venta - self.precio_compra

    def stock_actual_almacen(self):
        """
        Recorre los flujos en orden cronológico y calcula el stock del almacén.
         - 'AA' (Ajuste Almacén): se reinicia el stock.
         - 'EA' (Entrada Almacén): se suma la cantidad.
         - 'ST' (Salida a Tienda): se resta la cantidad (transferencia a tienda).
        """
        stock = 0
        for f in self.flujo_set.order_by('created_at'):
            if f.tipo == 'AA':
                stock = f.cantidad
            elif f.tipo == 'EA':
                stock += f.cantidad
            elif f.tipo == 'ST':
                stock -= f.cantidad
        return stock

    def stock_actual_tienda(self):
        """
        Recorre los flujos en orden cronológico y calcula el stock de la tienda.
         - 'AT' (Ajuste Tienda): se reinicia el stock.
         - 'ST' (Salida a Tienda): se suma la cantidad (producto recibido desde el almacén).
         - 'V'  (Venta): se resta la cantidad.
        """
        stock = 0
        for f in self.flujo_set.order_by('created_at'):
            if f.tipo == 'AT':
                stock = f.cantidad
            elif f.tipo == 'ST':
                stock += f.cantidad
            elif f.tipo == 'V':
                stock -= f.cantidad
        return stock

    def toJSON(self):
        item = model_to_dict(self)
        item['created_at'] = self.created_at.strftime('%Y-%m-%d')
        item['ganancia'] = self.ganancia()
        item['stock_actual_almacen'] = self.stock_actual_almacen()
        item['stock_actual_tienda'] = self.stock_actual_tienda()
        return item

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['id']


class Flujo(models.Model):
    TIPO_CHOICES = (
        ('EA', 'Entrada Almacén'),
        ('ST', 'Salida a Tienda'),
        ('AA', 'Ajuste Almacén'),
        ('AT', 'Ajuste Tienda'),
        ('V',  'Venta'),
    )
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, verbose_name='Producto')
    cantidad = models.PositiveIntegerField(null=False, blank=False)
    tipo = models.CharField(
        max_length=2,
        choices=TIPO_CHOICES,
        default='EA',
        verbose_name='Tipo de Flujo'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    constancia = models.CharField(max_length=150, null=True, blank=True, verbose_name='Constancia')
    # Nuevo campo para registrar el precio de venta en el momento de la operación
    precio = models.FloatField(null=True, blank=True, verbose_name='Precio de Venta')

    def __str__(self):
        return f"{self.producto.name} - {self.get_tipo_display()}: {self.cantidad}"

    def toJSON(self):
        item = model_to_dict(self)
        item['created_at'] = self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        item['tipo'] = self.get_tipo_display()
        item['producto'] = self.producto.toJSON()
        item['constancia'] = self.constancia
        item['precio'] = self.precio
        return item

    def save(self, *args, **kwargs):
        # Si es una venta y no se ha fijado un precio, se usa el precio actual del producto.
        if self.tipo == 'V' and (self.precio is None or self.precio == 0):
            self.precio = self.producto.precio_venta
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Flujo'
        verbose_name_plural = 'Flujos'
        ordering = ['-created_at']

class Informe(models.Model):
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Creación')
    archivo_pdf = models.FileField(upload_to='informes/', verbose_name='Archivo PDF', null=True, blank=True)

    def __str__(self):
        return f"{self.fecha_creacion.strftime('%Y-%m-%d')}"

    def toJSON(self):
        item = model_to_dict(self, exclude=['archivo_pdf'])
        item['fecha_creacion'] = self.fecha_creacion.strftime('%Y-%m-%d')
        if self.archivo_pdf:
            item['archivo_pdf'] = self.archivo_pdf.url
        return item

    class Meta:
        verbose_name = 'Informe'
        verbose_name_plural = 'Informes'
        ordering = ['-fecha_creacion']

