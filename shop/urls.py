from django.urls import path
from .views import (
    home,
    product_list,
    product_detail,
    order_create,
    order_list,
    cart_detail,
    cart_add,
    cart_remove,
    cart_update,  # ✅ Исправлено! Теперь `cart_update` импортирован
)

urlpatterns = [
    path("", home, name="home"),
    path("catalog/", product_list, name="product_list"),
    path("order/", order_create, name="order_create"),
    path("orders/", order_list, name="order_list"),
    # Корзина
    path("cart/", cart_detail, name="cart_detail"),
    path("cart/add/<int:product_id>/", cart_add, name="cart_add"),
    path("cart/remove/<int:product_id>/", cart_remove, name="cart_remove"),
    path(
        "cart/update/<int:product_id>/", cart_update, name="cart_update"
    ),  # ✅ Теперь маршрут работает
    # Категории и товары
    path("<slug:category_slug>/", product_list, name="product_list_by_category"),
    path("product/<slug:product_slug>/", product_detail, name="product_detail"),
]
