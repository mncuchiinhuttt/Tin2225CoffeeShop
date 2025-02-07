from django.contrib import admin
from .models import MenuItem

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'is_available')
    list_filter = ('category', 'is_available')
    search_fields = ('name', 'description')
    ordering = ('category', 'name')
    readonly_fields = ('created_at',)