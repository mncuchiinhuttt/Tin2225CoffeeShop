from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from .forms import UserRegistrationForm
from .models import MenuItem, CartItem, Order, OrderItem, Size, Category, Comment
from django.contrib.humanize.templatetags.humanize import intcomma
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from django.utils import timezone
from datetime import timedelta, datetime
from .forms import CommentForm
import json
from decimal import Decimal

def forgot_password(request):
    return render(request, 'users/forgot_password.html')

def terms(request):
    context = {
        'today': timezone.now().date()
    }
    return render(request, 'legal/terms.html', context)

def privacy(request):
    context = {
        'today': timezone.now().date()
    }
    return render(request, 'legal/privacy.html', context)

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
                
                total = subtotal
                
                return JsonResponse({
                    'success': True,
                    'item_total': cart_item.get_total(),
                    'subtotal': subtotal,
                    'total': total
                })
                
        except CartItem.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Item not found'}, status=404)
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Invalid quantity'}, status=400)
            
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

@login_required
def cart_view(request):
    cart_items = CartItem.objects.filter(user=request.user)
    total = sum(item.get_total() for item in cart_items)
    
    context = {
        'cart_items': cart_items,
        'total': total,
    }
    return render(request, 'users/cart.html', context)

@login_required
def checkout(request):
    cart_items = CartItem.objects.filter(user=request.user)
    if not cart_items:
        messages.error(request, 'Your cart is empty')
        return redirect('cart-view')
    
    subtotal = sum(item.get_total() for item in cart_items)
    delivery_fee = Decimal('15000')  # Base delivery fee
    
    # Calculate membership discount
    membership_level = request.user.profile.membership_level
    discount_percentage = Decimal(str({
        'BRONZE': 0,
        'SILVER': 5,
        'GOLD': 10,
        'PLATINUM': 15,
        'DIAMOND': 20
    }.get(membership_level, 0)))
    
    discount_amount = (subtotal * discount_percentage) / Decimal('100')
    
    # Free delivery for Platinum and Diamond members
    if membership_level in ['PLATINUM', 'DIAMOND']:
        delivery_fee = Decimal('0')
    
    final_total = subtotal - discount_amount + delivery_fee
    
    # Calculate points to be earned (will be added when order is delivered)
    points_multiplier = Decimal(str({
        'BRONZE': 1,
        'SILVER': 1.2,
        'GOLD': 1.5,
        'PLATINUM': 2,
        'DIAMOND': 2.5
    }.get(membership_level, 1)))
    
    points_to_earn = int((final_total / Decimal('1000')) * points_multiplier)
    
    if request.method == 'POST':
        # Create order
        order = Order.objects.create(
            user=request.user,
            subtotal=subtotal,
            discount_amount=discount_amount,
            delivery_fee=delivery_fee,
            total_amount=final_total,
            delivery_address=request.POST['delivery_address'],
            phone_number=request.POST['phone_number'],
            membership_level=membership_level,
            points_earned=0  # Points will be set when order is delivered
        )
        
        # Create order items
        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                menu_item=cart_item.menu_item,
                size=cart_item.size,
                quantity=cart_item.quantity,
                price=cart_item.size.price
            )
        
        # Clear cart
        cart_items.delete()
        
        messages.success(request, 'Order placed successfully!')
        return redirect('order-history')
    
    context = {
        'cart_items': cart_items,
        'total': subtotal,
        'discount_amount': discount_amount,
        'delivery_fee': delivery_fee,
        'final_total': final_total,
        'points_to_earn': points_to_earn
    }
    return render(request, 'users/checkout.html', context)

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    context = {
        'orders': orders,
        'status_choices': Order.STATUS_CHOICES,
    }
    return render(request, 'users/order_history.html', context)

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
    featured_categories = Category.objects.annotate(
        item_count=Count('menuitem')
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
    categories = Category.objects.all()
    selected_category = request.GET.get('category', '')
    
    if selected_category:
        menu_items = menu_items.filter(category__id=selected_category)
    
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
def cart_update_quantity(request, item_id):
    try:
        cart_item = get_object_or_404(CartItem, id=item_id, user=request.user)
        quantity = int(request.POST.get('quantity', 1))
        
        if quantity > 0:
            cart_item.quantity = quantity
            cart_item.save()
            
            # Calculate new totals
            cart_items = CartItem.objects.filter(user=request.user)
            subtotal = sum(item.get_total() for item in cart_items)
            
            # Calculate discount if applicable
            discount = 0
            if request.user.profile.membership_level != 'BRONZE':
                discount_percentage = {
                    'SILVER': 5,
                    'GOLD': 10,
                    'PLATINUM': 15,
                    'DIAMOND': 20
                }.get(request.user.profile.membership_level, 0)
                
                if discount_percentage:
                    discount = (subtotal * discount_percentage) / 100
            
            total = subtotal - discount
            
            return JsonResponse({
                'success': True,
                'item_total': cart_item.get_total(),
                'subtotal': subtotal,
                'discount': discount,
                'total': total
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Quantity must be greater than 0'
            }, status=400)
            
    except CartItem.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Item not found'
        }, status=404)
    except ValueError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid quantity'
        }, status=400)

@login_required
def cart_remove(request, item_id):
    if request.method == 'POST':
        cart_item = get_object_or_404(CartItem, id=item_id, user=request.user)
        cart_item.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)

def about(request):
    return render(request, 'about.html')

@login_required
def add_comment(request, menu_item_id):
    menu_item = get_object_or_404(MenuItem, id=menu_item_id)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.menu_item = menu_item
            comment.save()
            messages.success(request, 'Comment added successfully.')
            return redirect('menu-detail', pk=menu_item.id)
    else:
        form = CommentForm()
    
    return render(request, 'users/add_comment.html', {
        'form': form,
        'menu_item': menu_item
    })

@login_required
def edit_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, user=request.user)
    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Comment updated successfully!')
            return redirect('menu-detail', pk=comment.menu_item.id)
    else:
        form = CommentForm(instance=comment)
    return render(request, 'users/edit_comment.html', {'form': form, 'comment': comment})

@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, user=request.user)
    menu_item_id = comment.menu_item.id
    comment.delete()
    messages.success(request, 'Comment deleted successfully!')
    return redirect('menu-detail', pk=menu_item_id)

@login_required
def profile(request):
    user_profile = request.user.profile
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'profile': user_profile,
        'orders': orders,
    }
    return render(request, 'users/profile.html', context)

@login_required
def membership(request):
    profile = request.user.profile
    current_points = profile.points
    
    # Calculate points needed for next level
    if profile.membership_level == 'BRONZE':
        points_needed = 1000 - current_points  # Need 1000 for Silver
        next_level = 'SILVER'
    elif profile.membership_level == 'SILVER':
        points_needed = 2000 - current_points  # Need 2000 for Gold
        next_level = 'GOLD'
    elif profile.membership_level == 'GOLD':
        points_needed = 5000 - current_points  # Need 5000 for Platinum
        next_level = 'PLATINUM'
    elif profile.membership_level == 'PLATINUM':
        points_needed = 10000 - current_points  # Need 10000 for Diamond
        next_level = 'DIAMOND'
    else:  # DIAMOND
        points_needed = 0
        next_level = None
    
    context = {
        'profile': profile,
        'current_points': current_points,
        'points_needed': max(0, points_needed),
        'next_level': next_level,
        'progress_percentage': min(100, (current_points / (points_needed + current_points) * 100 if points_needed > 0 else 100))
    }
    return render(request, 'users/membership.html', context)

def is_staff(user):
    return user.is_staff

@login_required
@user_passes_test(is_staff)
def staff_orders(request):
    orders = Order.objects.all().order_by('-created_at')
    
    # Apply filters
    status = request.GET.get('status')
    date = request.GET.get('date')
    
    if status:
        orders = orders.filter(status=status)
    if date:
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        orders = orders.filter(created_at__date=date_obj)
    
    # Pagination
    paginator = Paginator(orders, 10)  # Show 10 orders per page
    page = request.GET.get('page')
    orders = paginator.get_page(page)
    
    return render(request, 'users/staff_orders.html', {'orders': orders})

@login_required
@user_passes_test(is_staff)
def update_order_status(request, order_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=400)
    
    order = get_object_or_404(Order, id=order_id)
    new_status = request.POST.get('status')
    
    if new_status not in ['PENDING', 'PROCESSING', 'DELIVERED', 'CANCELLED']:
        return JsonResponse({'error': 'Invalid status'}, status=400)
    
    # If marking as delivered, add points to user's profile
    if new_status == 'DELIVERED' and order.status != 'DELIVERED':
        points_multiplier = Decimal(str({
            'BRONZE': 1,
            'SILVER': 1.2,
            'GOLD': 1.5,
            'PLATINUM': 2,
            'DIAMOND': 2.5
        }.get(order.membership_level, 1)))
        
        points_earned = int((order.total_amount / Decimal('1000')) * points_multiplier)
        order.points_earned = points_earned
        order.user.profile.add_points(order.total_amount)
        messages.success(request, f'Order marked as delivered. {points_earned} points added to customer\'s account.')
    
    order.status = new_status
    order.save()
    
    return redirect('staff-orders')

@login_required
@user_passes_test(is_staff)
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order_items = order.orderitem_set.all()
    
    context = {
        'order': order,
        'order_items': order_items,
    }
    return render(request, 'users/order_detail.html', context)