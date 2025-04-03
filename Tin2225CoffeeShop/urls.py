from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from users import views as user_views
from django.contrib.auth import views as auth_views
from django.conf.urls import handler404

handler404 = 'users.views.custom_404'

urlpatterns = [
    path('', user_views.home, name='home'),
    path('admin/', admin.site.urls),
    path('register/', user_views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', user_views.logout_view, name='logout'),
    path('menu/', user_views.menu_list, name='menu-list'),
    path('menu/<int:pk>/', user_views.menu_detail, name='menu-detail'),
    path('cart/', user_views.cart_view, name='cart-view'),
    path('cart/add/<int:item_id>/', user_views.cart_add, name='cart-add'),
    path('cart/remove/<int:item_id>/', user_views.cart_remove, name='cart-remove'),
    path('cart/update-quantity/<int:item_id>/', user_views.cart_update_quantity, name='cart-update-quantity'),
    path('checkout/', user_views.checkout, name='checkout'),
    path('orders/', user_views.order_history, name='order-history'),
    path('orders/<int:order_id>/update-status/', user_views.update_order_status, name='update-order-status'),
    path('cart/update-quantity/<int:item_id>/', user_views.cart_update_quantity, name='cart-update-quantity'),
    path('__reload__/', include('django_browser_reload.urls')),
    path('terms/', user_views.terms, name='terms'),
    path('privacy/', user_views.privacy, name='privacy'),
    path('forgot-password/', user_views.forgot_password, name='forgot-password'),
    path('about/', user_views.about, name='about'),
    path('menu/<int:menu_item_id>/comment/', user_views.add_comment, name='add_comment'),
    path('comment/<int:comment_id>/edit/', user_views.edit_comment, name='edit_comment'),
    path('comment/<int:comment_id>/delete/', user_views.delete_comment, name='delete_comment'),
    path('profile/', user_views.profile, name='profile'),
    path('membership/', user_views.membership, name='membership'),
    path('staff/orders/', user_views.staff_orders, name='staff-orders'),
    path('staff/orders/<int:order_id>/update-status/', user_views.update_order_status, name='update-order-status'),
    path('staff/orders/<int:order_id>/', user_views.order_detail, name='order-detail'),
    path('shipping-addresses/', user_views.shipping_addresses, name='shipping-addresses'),
    path('shipping-addresses/add/', user_views.add_shipping_address, name='add-shipping-address'),
    path('shipping-addresses/<int:address_id>/edit/', user_views.edit_shipping_address, name='edit-shipping-address'),
    path('shipping-addresses/<int:address_id>/delete/', user_views.delete_shipping_address, name='delete-shipping-address'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)