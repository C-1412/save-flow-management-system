from django import forms
from django.forms import ModelForm
from django.core.exceptions import ValidationError

from core.erp.models import Producto, Flujo, Informe

class ProductoForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs['autofocus'] = True

    class Meta:
        model = Producto
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Ingrese un nombre', 'class': 'form-control'}),
            'precio_compra': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
            'precio_venta': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
        }

    def save(self, commit=True):
        data = {}
        form = super()
        try:
            if form.is_valid():
                form.save(commit=commit)
            else:
                data['error'] = form.errors
        except Exception as e:
            data['error'] = str(e)
        return data

class FlujoForm(ModelForm):

    class Meta:
        model = Flujo
        # Excluimos el campo 'precio' para que se asigne automáticamente en el modelo.
        fields = ['producto', 'cantidad', 'tipo', 'constancia']
        widgets = {
            'producto': forms.Select(attrs={'class': 'form-control', 'style': 'width: 100%'}),
            'cantidad': forms.NumberInput(attrs={'min': '1', 'class': 'form-control'}),
            'constancia': forms.TextInput(attrs={'placeholder': 'Ingrese un justificante', 'class': 'form-control'}),
            'tipo': forms.RadioSelect(),  # Se muestran los códigos y descripciones
        }

    def clean(self):
        """
        Validaciones:
         - Para 'ST' (Salida a Tienda): se debe tener suficiente stock en almacén.
         - Para 'V' (Venta): se debe tener suficiente stock en tienda.
         - Se valida que la cantidad sea mayor a 0.
         
         En el caso de una actualización, se remueve el efecto previo para evaluar la nueva operación.
        """
        cleaned_data = super().clean()
        producto = cleaned_data.get('producto')
        cantidad = cleaned_data.get('cantidad')
        tipo = cleaned_data.get('tipo')

        if not producto or not cantidad or not tipo:
            return cleaned_data

        if cantidad <= 0:
            raise ValidationError("La cantidad debe ser mayor a 0.")

        if tipo == 'ST':
            if self.instance.pk:
                if self.instance.product == producto:
                    stock_almacen = producto.stock_actual_almacen()
                    if self.instance.tipo == 'ST':
                        stock_almacen += self.instance.cantidad
                else:
                    stock_almacen = producto.stock_actual_almacen()
            else:
                stock_almacen = producto.stock_actual_almacen()

            if stock_almacen < cantidad:
                raise ValidationError("No hay suficiente stock en el almacén para transferir a tienda.")

        if tipo == 'V':
            if self.instance.pk:
                if self.instance.product == producto:
                    stock_tienda = producto.stock_actual_tienda()
                    if self.instance.tipo == 'V':
                        stock_tienda += self.instance.cantidad
                else:
                    stock_tienda = producto.stock_actual_tienda()
            else:
                stock_tienda = producto.stock_actual_tienda()

            if stock_tienda < cantidad:
                raise ValidationError("No hay suficiente stock en la tienda para realizar la venta.")

        return cleaned_data

    def save(self, commit=True):
        data = {}
        form = super()
        try:
            if form.is_valid():
                form.save(commit=commit)
            else:
                data['error'] = form.errors
        except Exception as e:
            data['error'] = str(e)
        return data

class InformeForm(forms.ModelForm):
    class Meta:
        model = Informe
        fields = ['archivo_pdf']
        widgets = {
            'archivo_pdf': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
        }