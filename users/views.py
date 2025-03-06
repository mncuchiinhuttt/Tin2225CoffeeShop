from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .forms import UserRegistrationForm, VoucherForm
from .models import MenuItem, CartItem, Order, OrderItem, Size, Voucher  
from django.contrib.humanize.templatetags.humanize import intcomma
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from django.utils import timezone
from datetime import timedelta

@login_required
def update_cart_quantity(request, item_id):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            cart_item = CartItem.objects.get(id=item_id, user=request.user)
            quantity = int(request.POST.get('quantity', 1))
            
            if quantity > 0:
                cart_item.quantity = quantity
                cart_item.save()
                
                # Calculate new totals
                cart_items = CartItem.objects.filter(user=request.user)
                subtotal = sum(item.get_total() for item in cart_items)
                
                # Apply voucher if exists
                discount = 0
                voucher_code = request.session.get('voucher_code')
                if voucher_code:
                    try:
                        voucher = Voucher.objects.get(code=voucher_code)
                        if voucher.is_valid() and subtotal >= voucher.min_spend:
                            discount = min(
                                voucher.discount_amount,
                                voucher.max_discount or float('inf')
                            )
                    except Voucher.DoesNotExist:
                        pass
                
                total = subtotal - discount
                
                return JsonResponse({
                    'success': True,
                    'item_total': cart_item.get_total(),
                    'subtotal': subtotal,
                    'discount': discount,
                    'total': total
                })
                
        except CartItem.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Item not found'}, status=404)
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Invalid quantity'}, status=400)
            
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

@login_required
def checkout(request):
    cart_items = CartItem.objects.filter(user=request.user)
    if not cart_items.exists():
        messages.warning(request, 'Your cart is empty.')
        return redirect('cart-view')
    
    voucher_code = request.session.get('voucher_code')
    voucher = None
    subtotal = sum(item.get_total() for item in cart_items)
    discount = 0
    
    # Apply voucher if exists
    if voucher_code:
        try:
            voucher = Voucher.objects.get(code=voucher_code)
            if voucher.is_valid() and subtotal >= voucher.min_spend:
                discount = min(
                    voucher.discount_amount,
                    voucher.max_discount or float('inf')
                )
        except Voucher.DoesNotExist:
            del request.session['voucher_code']
    
    total = subtotal - discount
    
    if request.method == 'POST':
        try:
            # Create order
            order = Order.objects.create(
                user=request.user,
                delivery_address=request.POST['delivery_address'],
                phone_number=request.POST['phone_number'],
                subtotal=subtotal,
                discount=discount,
                total_amount=total,
                voucher=voucher if voucher and voucher.is_valid() else None
            )
            
            # Create order items
            for cart_item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    menu_item=cart_item.menu_item,
                    size=cart_item.size.size,
                    quantity=cart_item.quantity,
                    price=cart_item.size.price
                )
            
            # Update voucher usage if used
            if voucher and voucher.is_valid():
                voucher.times_used += 1
                voucher.save()
            
            # Clear cart and voucher
            cart_items.delete()
            if 'voucher_code' in request.session:
                del request.session['voucher_code']
            
            messages.success(request, 'Order placed successfully!')
            return redirect('order-history')
            
        except Exception as e:
            messages.error(request, f'Error placing order: {str(e)}')
    
    context = {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'voucher': voucher,
        'discount': discount,
        'total': total
    }
    return render(request, 'users/checkout.html', context)

@login_required
def cart_view(request):
    cart_items = CartItem.objects.filter(user=request.user)
    voucher_code = request.session.get('voucher_code')
    voucher = None
    
    # Calculate subtotal
    subtotal = sum(item.get_total() for item in cart_items)
    discount = 0
    
    # Apply voucher if exists
    if voucher_code:
        try:
            voucher = Voucher.objects.get(code=voucher_code)
            if voucher.is_valid() and subtotal >= voucher.min_spend:
                discount = min(
                    voucher.discount_amount,
                    voucher.max_discount or float('inf')
                )
        except Voucher.DoesNotExist:
            del request.session['voucher_code']
    
    total = subtotal - discount
    
    context = {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'voucher': voucher,
        'discount': discount,
        'total': total
    }
    return render(request, 'users/cart.html', context)

# Modification needed in views.py
@login_required
def apply_voucher(request):
    if request.method == 'POST':
        form = VoucherForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            try:
                voucher = Voucher.objects.get(code=code)
                cart_total = sum(item.get_total() for item in CartItem.objects.filter(user=request.user))
                
                if cart_total < voucher.min_spend:
                    messages.error(request, f'Minimum spend of {voucher.min_spend} VND required')
                else:
                    request.session['voucher_code'] = code
                    messages.success(request, 'Voucher applied successfully!')
            except Voucher.DoesNotExist:
                messages.error(request, 'Invalid voucher code')
        else:
            messages.error(request, form.errors['code'][0])
    
    # Check if we need to redirect back to checkout
    next_page = request.POST.get('next')
    if next_page == 'checkout':
        return redirect('checkout')
    return redirect('cart-view')

@login_required
def remove_voucher(request):
    if 'voucher_code' in request.session:
        del request.session['voucher_code']
        messages.success(request, 'Voucher removed successfully!')
    
    # Check if we need to redirect back to checkout
    next_page = request.GET.get('next')
    if next_page == 'checkout':
        return redirect('checkout')
    return redirect('cart-view')

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
    categories = MenuItem.objects.values_list('category', flat=True).distinct()
    selected_category = request.GET.get('category', '')
    
    if selected_category:
        menu_items = menu_items.filter(category=selected_category)
    
    return render(request, 'users/menu_list.html', {
        'menu_items': menu_items,
        'categories': categories,
        'selected_category': selected_category
    })

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