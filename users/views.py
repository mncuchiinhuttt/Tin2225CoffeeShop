from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from .forms import UserRegistrationForm
from .models import MenuItem, CartItem, Order, OrderItem, Size
from django.contrib.humanize.templatetags.humanize import intcomma
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from django.utils import timezone
from datetime import timedelta

def custom_404(request, exception):
    return render(request, '404.html', status=404)

def home(request):
    # Get hot items (most ordered in the last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    hot_items = MenuItem.objects.filter(
        orderitem__order__created_at__gte=thirty_days_ago
    ).annotate(
        total_ordered=Sum('orderitem__quantity')
    ).filter(
        is_available=True
    ).order_by('-total_ordered')[:4]

    # Get new items (added in last 7 days)
    seven_days_ago = timezone.now() - timedelta(days=7)
    new_items = MenuItem.objects.filter(
        created_at__gte=seven_days_ago,
        is_available=True
    ).order_by('-created_at')[:4]

    # Get featured categories (categories with most items)
    featured_categories = MenuItem.objects.values('category').annotate(
        item_count=Count('id')
    ).order_by('-item_count')[:4]

    context = {
        'hot_items': hot_items,
        'new_items': new_items,
        'featured_categories': featured_categories,
    }
    return render(request, 'users/home.html', context)

def logout_view(request):
    logout(request)
    return redirect('home')

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserRegistrationForm()
    return render(request, 'users/register.html', {'form': form})

def menu_list(request):
    menu_items = MenuItem.objects.all()
    return render(request, 'users/menu_list.html', {'menu_items': menu_items})

def menu_detail(request, pk):
    item = get_object_or_404(MenuItem, pk=pk)
    min_price = item.sizes.filter(is_available=True).order_by('price').first()
    formatted_price = intcomma(min_price.price).replace(",", ".") if min_price else "N/A"
    
    related_items = MenuItem.objects.filter(
        category=item.category,
        is_available=True
    ).exclude(id=pk)[:4]
    
    return render(request, 'users/menu_detail.html', {
        'item': item,
        'formatted_price': formatted_price,
        'related_items': related_items
    })

@login_required
def cart_add(request, item_id):
    if request.method == 'POST':
        menu_item = get_object_or_404(MenuItem, id=item_id)
        size = get_object_or_404(Size, id=request.POST.get('size'))
        
        cart_item, created = CartItem.objects.get_or_create(
            user=request.user,
            menu_item=menu_item,
            size=size,
            defaults={'quantity': 1}
        )
        
        if not created:
            cart_item.quantity += 1
            cart_item.save()
            
        messages.success(request, f"{menu_item.name} ({size.get_size_display()}) added to cart.")
        return redirect('cart-view')
    return redirect('menu-list')

@login_required
def cart_view(request):
    cart_items = CartItem.objects.filter(user=request.user)
    total = sum(item.get_total() for item in cart_items)
    return render(request, 'users/cart.html', {
        'cart_items': cart_items,
        'total': total
    })

@login_required
def cart_update_quantity(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, user=request.user)
    quantity = int(request.POST.get('quantity', 1))
    
    if quantity > 0:
        cart_item.quantity = quantity
        cart_item.save()
        messages.success(request, "Cart updated successfully.")
    else:
        cart_item.delete()
        messages.success(request, "Item removed from cart.")
        
    return redirect('cart-view')

@login_required
def cart_remove(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, user=request.user)
    cart_item.delete()
    messages.success(request, "Item removed from cart.")
    return redirect('cart-view')

@login_required
def checkout(request):
    cart_items = CartItem.objects.filter(user=request.user)
    if not cart_items:
        messages.warning(request, "Your cart is empty.")
        return redirect('cart-view')
    
    total = sum(item.get_total() for item in cart_items)
        
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        delivery_address = request.POST.get('delivery_address')
        
        order = Order.objects.create(
            user=request.user,
            total_amount=total,
            phone_number=phone_number,
            delivery_address=delivery_address
        )
        
        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                menu_item=cart_item.menu_item,
                size=cart_item.size.size,
                quantity=cart_item.quantity,
                price=cart_item.size.price
            )
        
        cart_items.delete()  # Clear the cart
        messages.success(request, "Order placed successfully!")
        return redirect('order-history')
        
    return render(request, 'users/checkout.html', {
        'cart_items': cart_items,
        'total': total
    })

@login_required
def order_history(request):
    orders_list = Order.objects.filter(user=request.user)
    
    # Filtering
    status = request.GET.get('status')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    search = request.GET.get('search')
    
    if status:
        orders_list = orders_list.filter(status=status)
    if date_from:
        orders_list = orders_list.filter(created_at__gte=date_from)
    if date_to:
        orders_list = orders_list.filter(created_at__lte=date_to)
    if search:
        orders_list = orders_list.filter(
            Q(id__icontains=search) |
            Q(delivery_address__icontains=search) |
            Q(phone_number__icontains=search)
        )
    
    # Sorting
    sort_by = request.GET.get('sort_by', '-created_at')  # Default sort by newest
    orders_list = orders_list.order_by(sort_by)
    
    # Pagination
    paginator = Paginator(orders_list, 20)  # Show 20 orders per page
    page_number = request.GET.get('page')
    orders = paginator.get_page(page_number)
    
    context = {
        'orders': orders,
        'status_choices': Order.STATUS_CHOICES,
        'current_status': status,
        'current_sort': sort_by,
        'date_from': date_from,
        'date_to': date_to,
        'search': search,
    }
    return render(request, 'users/order_history.html', context)