from django.urls import path
from . import views

urlpatterns = [
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove-from-cart'),
    path('about/', views.about, name='about'),
] 