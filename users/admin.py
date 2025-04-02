from django.contrib import admin
from django.utils.html import format_html
from .models import Category, MenuItem, Order, OrderItem, CartItem, Size

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_menu_items_count')
    search_fields = ('name', 'description')
    ordering = ('name',)
    
    def get_menu_items_count(self, obj):
        return obj.menuitem_set.count()
    get_menu_items_count.short_description = 'Menu Items'

@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ('menu_item', 'size', 'get_formatted_price', 'is_available')
    list_filter = ('size', 'is_available', 'menu_item__category')
    search_fields = ('menu_item__name',)
    
    def get_formatted_price(self, obj):
        return f"${obj.price:.2f}"
    get_formatted_price.short_description = 'Price'

class SizeInline(admin.TabularInline):
    model = Size
    extra = 0
    fields = ('size', 'price', 'is_available')

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    inlines = [SizeInline]
    list_display = ('name', 'category', 'get_image_preview', 'is_available', 'get_formatted_price_range')
    list_filter = ('category', 'is_available')
    search_fields = ('name', 'description')
    ordering = ('category', 'name')
    readonly_fields = ('created_at', 'get_image_preview')
    
    def get_image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover; border-radius: 4px;" />', obj.image.url)
        return "No Image"
    get_image_preview.short_description = 'Image'
    
    def get_formatted_price_range(self, obj):
        prices = [size.price for size in obj.sizes.all()]
        if prices:
            return f"${min(prices):.2f} - ${max(prices):.2f}"
        return "N/A"
    get_formatted_price_range.short_description = 'Price Range'

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    readonly_fields = ('menu_item', 'quantity', 'price')
    extra = 0
    fields = ('menu_item', 'size', 'quantity', 'price')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'get_formatted_total', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'phone_number')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [OrderItemInline]
    
    def get_formatted_total(self, obj):
        return f"${obj.total_amount:.2f}"
    get_formatted_total.short_description = 'Total'
    
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('user', 'total_amount')
        return self.readonly_fields

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'menu_item', 'size', 'quantity', 'get_formatted_total', 'created_at')
    list_filter = ('user', 'created_at')
    search_fields = ('user__username', 'menu_item__name')
    readonly_fields = ('created_at', 'updated_at')
    
    def get_formatted_total(self, obj):
        return f"${obj.get_total():.2f}"
    get_formatted_total.short_description = 'Total'

    def has_add_permission(self, request):
        return False