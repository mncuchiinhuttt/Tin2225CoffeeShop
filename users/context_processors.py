from .models import CartItem

def cart_item_count(request):
    """
    Context processor to make cart items available across all templates
    """
    if request.user.is_authenticated:
        cart_items = CartItem.objects.filter(user=request.user)
        return {'cart_items': cart_items}
    return {'cart_items': []}