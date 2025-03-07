from django.contrib import admin
from django.urls import path, reverse_lazy
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
    path('checkout/', user_views.checkout, name='checkout'),
    path('orders/', user_views.order_history, name='order-history'),
    path('cart/update/<int:item_id>/', user_views.cart_update_quantity, name='cart-update-quantity'),
    path('apply-voucher/', user_views.apply_voucher, name='apply-voucher'),
    path('remove-voucher/', user_views.remove_voucher, name='remove-voucher'),
    path('cart/update-quantity/<int:item_id>/', user_views.update_cart_quantity, name='cart-update-quantity'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)