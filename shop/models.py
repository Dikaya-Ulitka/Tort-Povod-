from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from datetime import date, timedelta
import uuid

MESSENGER_CHOICES = [
    ("telegram", "Telegram"),
    ("whatsapp", "WhatsApp"),
    ("viber", "Viber"),
]


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Название")
    slug = models.SlugField(max_length=100, unique=True, verbose_name="URL")

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="products",
        verbose_name="Категория",
    )
    name = models.CharField(max_length=150, verbose_name="Название")
    slug = models.SlugField(max_length=150, unique=True, verbose_name="URL")
    description = models.TextField(blank=True, verbose_name="Описание")
    price = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Цена")
    image = models.ImageField(
        upload_to="products/", blank=True, verbose_name="Изображение"
    )
    min_order_quantity = models.PositiveIntegerField(
        default=1, verbose_name="Минимальное количество для заказа"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата добавления")

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class Cart(models.Model):
    """Модель корзины (сессия для пользователя)"""

    session_key = models.CharField(
        max_length=50, unique=True, verbose_name="Ключ сессии"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    def __str__(self):
        return f"Корзина {self.session_key}"


class CartItem(models.Model):
    """Модель товара в корзине"""

    cart = models.ForeignKey(
        Cart, on_delete=models.CASCADE, related_name="items", verbose_name="Корзина"
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Товар")
    quantity = models.PositiveIntegerField(
        default=1, validators=[MinValueValidator(1)], verbose_name="Количество"
    )

    class Meta:
        verbose_name = "Товар в корзине"
        verbose_name_plural = "Товары в корзине"

    def __str__(self):
        return f"{self.product.name} (x{self.quantity})"


class Order(models.Model):
    STATUS_CHOICES = [
        ("pending", "В обработке"),
        ("confirmed", "Подтвержден"),
        ("canceled", "Отменен"),
    ]

    order_number = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        verbose_name="Номер заказа",
    )
    customer_name = models.CharField(max_length=100, verbose_name="Имя клиента")
    phone = models.CharField(max_length=20, verbose_name="Телефон")
    messenger = models.CharField(
        max_length=10,
        choices=MESSENGER_CHOICES,
        default="telegram",
        verbose_name="Мессенджер",
    )
    messenger_contact = models.CharField(
        max_length=100, verbose_name="Контакт для связи", default="не указан"
    )
    order_date = models.DateField(verbose_name="Дата заказа")
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default="pending", verbose_name="Статус"
    )
    comment = models.TextField(blank=True, verbose_name="Комментарий")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Заказ {self.order_number} - {self.customer_name} ({self.get_status_display()})"

    def clean(self):
        """Проверка: дата заказа не может быть раньше, чем через 3 дня"""
        if not self.order_date:
            raise ValidationError("Выберите дату заказа.")

        if self.order_date < date.today() + timedelta(days=3):
            raise ValidationError("Дата заказа должна быть не раньше чем через 3 дня.")


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="items", verbose_name="Заказ"
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Товар")
    quantity = models.PositiveIntegerField(
        default=1, validators=[MinValueValidator(1)], verbose_name="Количество"
    )

    class Meta:
        verbose_name = "Товар в заказе"
        verbose_name_plural = "Товары в заказе"

    def __str__(self):
        return f"{self.product.name} (x{self.quantity})"
