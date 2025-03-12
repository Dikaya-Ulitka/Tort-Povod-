from django.shortcuts import render, get_object_or_404, redirect
from .models import Category, Product, Order, OrderItem, Cart, CartItem
from .forms import OrderForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from decimal import Decimal
import requests
import os


def home(request):
    """Главная страница с информацией о кондитере"""
    return render(request, "shop/home.html")


@login_required
def order_list(request):
    """Страница списка заказов (для администратора)"""
    orders = Order.objects.all()
    return render(request, "shop/order_list.html", {"orders": orders})


def product_list(request, category_slug=None):
    """Список товаров с фильтрацией по категориям"""
    category = None
    categories = Category.objects.all()
    products = Product.objects.all()

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    return render(
        request,
        "shop/product_list.html",
        {
            "category": category,
            "categories": categories,
            "products": products,
        },
    )


def product_detail(request, product_slug):
    """Детальная страница товара"""
    product = get_object_or_404(Product, slug=product_slug)
    return render(request, "shop/product_detail.html", {"product": product})


### 🔹 Telegram-уведомления о заказе

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def send_telegram_message(order):
    """Отправка уведомления в Telegram"""
    items = order.items.all()
    items_text = "\n".join([f"{item.product.name} x{item.quantity}" for item in items])

    message = (
        f"📢 Новый заказ!\n\n"
        f"Товары:\n{items_text}\n"
        f"Клиент: {order.customer_name}\n"
        f"Телефон: {order.phone}\n"
        f"Мессенджер: {order.get_messenger_display()} ({order.messenger_contact})\n"
        f"Дата: {order.order_date}\n"
        f"Комментарий: {order.comment}"
    )

    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
        data={"chat_id": TELEGRAM_CHAT_ID, "text": message},
    )


### 🔹 Логика корзины


def get_cart(request):
    """Получаем или создаем корзину для текущей сессии"""
    session_key = request.session.session_key
    if not session_key:
        request.session.create()
        session_key = request.session.session_key

    cart, created = Cart.objects.get_or_create(session_key=session_key)
    return cart


def cart_add(request, product_id):
    """Добавление товара в корзину (с AJAX-уведомлением)"""
    product = get_object_or_404(Product, id=product_id)
    cart = get_cart(request)

    quantity = int(request.POST.get("quantity", product.min_order_quantity))

    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if created:
        cart_item.quantity = quantity
    else:
        cart_item.quantity += quantity

    cart_item.save()

    return JsonResponse(
        {"status": "success", "message": f"✅ {product.name} добавлен в корзину!"}
    )


def cart_update(request, product_id):
    """Обновление количества товара в корзине"""
    product = get_object_or_404(Product, id=product_id)
    cart = get_cart(request)

    try:
        cart_item = CartItem.objects.get(cart=cart, product=product)
        quantity = int(
            request.POST.get("quantity", cart_item.product.min_order_quantity)
        )

        if quantity >= cart_item.product.min_order_quantity:
            cart_item.quantity = quantity  # Устанавливаем новое количество
            cart_item.save()

    except CartItem.DoesNotExist:
        pass  # Товар не найден в корзине, ничего не делаем

    return redirect("cart_detail")  # ✅ Перенаправление на страницу корзины


def cart_remove(request, product_id):
    """Удаление товара из корзины"""
    cart = get_cart(request)
    cart_item = get_object_or_404(CartItem, cart=cart, product_id=product_id)
    cart_item.delete()

    return redirect("cart_detail")


def cart_detail(request):
    """Отображение корзины"""
    cart = get_cart(request)
    cart_items = cart.items.all()

    total_price = Decimal("0.00")
    cart_data = []

    for item in cart_items:
        total_price_item = Decimal(item.quantity) * item.product.price
        total_price += total_price_item

        cart_data.append(
            {
                "product": item.product,
                "quantity": item.quantity,
                "total_price": total_price_item,
            }
        )

    return render(
        request,
        "shop/cart.html",
        {
            "cart_items": cart_data,
            "total_price": total_price,
        },
    )


### 🔹 Создание заказа из корзины


def order_create(request):
    """Создание заказа из корзины"""
    cart = get_cart(request)
    cart_items = cart.items.all()

    if not cart_items:
        return redirect("cart_detail")

    if request.method == "POST":
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)  # Сначала создаем объект
            order.save()  # Теперь у него есть ID

            order_items = [
                OrderItem(order=order, product=item.product, quantity=item.quantity)
                for item in cart_items
            ]
            OrderItem.objects.bulk_create(order_items)  # Массовое создание товаров

            cart.items.all().delete()  # Очищаем корзину

            send_telegram_message(order)

            return render(request, "shop/order_success.html", {"order": order})

    else:
        form = OrderForm()

    return render(
        request, "shop/order_form.html", {"form": form, "cart_items": cart_items}
    )
