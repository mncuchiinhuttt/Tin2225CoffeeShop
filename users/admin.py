from django.contrib import admin
from .models import MenuItem, Order, OrderItem, CartItem, Size, Voucher

@admin.register(Voucher)
class VoucherAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_amount', 'valid_from', 'valid_to', 
                   'is_active', 'times_used')
    search_fields = ('code',)
    list_filter = ('is_active', 'valid_from', 'valid_to')

@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ('menu_item', 'size', 'price', 'is_available')
    list_filter = ('size', 'is_available', 'menu_item__category')
    search_fields = ('menu_item__name',)

class SizeInline(admin.TabularInline):
    model = Size
    extra = 0

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    inlines = [SizeInline]
    list_display = ('name', 'category', 'is_available')
    list_filter = ('category', 'is_available')
    search_fields = ('name', 'description')
    ordering = ('category', 'name')
    readonly_fields = ('created_at',)

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    readonly_fields = ('menu_item', 'quantity', 'price')
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'phone_number')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [OrderItemInline]
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ('user', 'total_amount')
        return self.readonly_fields

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'menu_item', 'quantity', 'date_added')
    list_filter = ('user', 'date_added')