from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

class Voucher(models.Model):
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField()
    discount_amount = models.DecimalField(max_digits=10, decimal_places=0)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    min_spend = models.DecimalField(max_digits=10, decimal_places=0, default=0)
    max_discount = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True)
    usage_limit = models.PositiveIntegerField(null=True, blank=True)
    times_used = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return f"{self.code} ({self.discount_amount} VND)"
    
    def is_valid(self):
        now = timezone.now()
        return (
            self.is_active and
            self.valid_from <= now <= self.valid_to and
            (self.usage_limit is None or self.times_used < self.usage_limit)
        )

class Size(models.Model):
    SIZES = [
        ('S', 'Small'),
        ('M', 'Medium'),
        ('L', 'Large'),
        ('XL', 'Extra Large'),
    ]

    menu_item = models.ForeignKey('MenuItem', on_delete=models.CASCADE, related_name='sizes')
    size = models.CharField(max_length=2, choices=SIZES)
    price = models.DecimalField(max_digits=10, decimal_places=0)
    is_available = models.BooleanField(default=True)

    class Meta:
        unique_together = ['menu_item', 'size']
        ordering = ['size']

    def __str__(self):
        return f"{self.menu_item.name} - {self.get_size_display()}"

class MenuItem(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    category = models.CharField(max_length=50)
    image = models.ImageField(
        upload_to='menu_items/',
        null=True, 
        blank=True,
        default='menu_items/default.png' 
    )
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_base_price(self):
        size = self.sizes.filter(size='M').first()
        return size.price if size else 0
    
    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('menu-detail', args=[str(self.id)])

    def get_image_url(self):
        """Return image URL, use default if no image exists"""
        if self.image and hasattr(self.image, 'url'):
            return self.image.url
        return '/static/images/default-menu-item.png' 
    
class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    size = models.ForeignKey(Size, on_delete=models.CASCADE, null=True, default=None)
    quantity = models.PositiveIntegerField(default=1)
    date_added = models.DateTimeField(auto_now_add=True)

    def get_total(self):
        return self.size.price * self.quantity

class Order(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('PREPARING', 'Preparing'),
        ('OUT_FOR_DELIVERY', 'Out for Delivery'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    items = models.ManyToManyField(MenuItem, through='OrderItem')
    total_amount = models.DecimalField(max_digits=10, decimal_places=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    phone_number = models.CharField(max_length=15)
    delivery_address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    voucher = models.ForeignKey(Voucher, on_delete=models.SET_NULL, null=True, blank=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=0, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=0, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=0, default=0)

    def __str__(self):
        return f"Order #{self.id} by {self.user.username}"
    
    pass

class OrderItem(models.Model):
    order = models.ForeignKey('Order', on_delete=models.CASCADE)
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    size = models.CharField(max_length=2, null=True) 
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=0) 

    def get_total(self):
        return self.price * self.quantity