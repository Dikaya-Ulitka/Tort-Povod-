from django import forms
from .models import Order, OrderItem, Product, CartItem
from datetime import date, timedelta


from django import forms
from .models import Order
from datetime import date, timedelta


class OrderForm(forms.ModelForm):
    order_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        label="Дата заказа",
        required=True,
        help_text="Выберите дату не раньше чем через 3 дня.",
    )

    messenger_contact = forms.CharField(
        required=True,
        label="Контакт в мессенджере",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    class Meta:
        model = Order
        fields = [
            "customer_name",
            "phone",
            "messenger",
            "messenger_contact",
            "order_date",
            "comment",
        ]

    def clean_order_date(self):
        """Проверка: дата заказа не может быть раньше, чем через 3 дня"""
        order_date = self.cleaned_data.get("order_date")

        if not order_date:
            raise forms.ValidationError("Пожалуйста, выберите дату заказа.")

        if order_date < date.today() + timedelta(days=3):
            raise forms.ValidationError(
                "Дата заказа должна быть не раньше чем через 3 дня."
            )

        return order_date


class CartAddProductForm(forms.Form):
    """Форма добавления товара в корзину"""

    quantity = forms.IntegerField(
        min_value=1,
        label="Количество",
        initial=1,
    )
    override = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.HiddenInput(),
    )


class CartUpdateForm(forms.ModelForm):
    """Форма обновления количества товара в корзине"""

    class Meta:
        model = CartItem
        fields = ["quantity"]
