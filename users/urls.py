from django.urls import path
from . import views

urlpatterns = [
    path('cart/', views.cart_view, name='cart-view'),
    path('cart/add/<int:item_id>/', views.cart_add, name='cart-add'),
    path('cart/update-quantity/<int:item_id>/', views.cart_update_quantity, name='cart-update-quantity'),
    path('cart/remove/<int:item_id>/', views.cart_remove, name='cart-remove'),
    path('membership/', views.membership, name='membership'),
    path('staff/orders/', views.staff_orders, name='staff-orders'),
    path('staff/orders/<int:order_id>/update-status/', views.update_order_status, name='update-order-status'),
    path('staff/orders/<int:order_id>/', views.order_detail, name='order-detail'),
    path('shipping-addresses/', views.shipping_addresses, name='shipping-addresses'),
    path('shipping-addresses/add/', views.add_shipping_address, name='add-shipping-address'),
    path('shipping-addresses/<int:address_id>/edit/', views.edit_shipping_address, name='edit-shipping-address'),
    path('shipping-addresses/<int:address_id>/delete/', views.delete_shipping_address, name='delete-shipping-address'),
    path('search/', views.search_menu_items, name='search'),
]