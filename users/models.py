from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
from django.db.models.signals import post_save
from django.dispatch import receiver

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class MenuItem(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='menu_items/', null=True, blank=True)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def get_image_url(self):
        if self.image:
            return self.image.url
        return None

    def get_absolute_url(self):
        return reverse('menu-detail', kwargs={'pk': self.pk})

class Size(models.Model):
    SIZE_CHOICES = [
        ('S', 'Small'),
        ('M', 'Medium'),
        ('L', 'Large'),
    ]
    
    menu_item = models.ForeignKey(MenuItem, related_name='sizes', on_delete=models.CASCADE)
    size = models.CharField(max_length=1, choices=SIZE_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=0)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.menu_item.name} - {self.get_size_display()}"

    def get_size_display(self):
        return dict(self.SIZE_CHOICES)[self.size]

class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    size = models.ForeignKey(Size, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s cart - {self.menu_item.name} ({self.size.get_size_display()})"

    def get_total(self):
        return self.size.price * self.quantity

class Order(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('PREPARING', 'Preparing'),
        ('READY', 'Ready for Pickup'),
        ('DELIVERING', 'Delivering'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
    ]

    MEMBERSHIP_LEVELS = [
        ('BRONZE', 'Bronze'),
        ('SILVER', 'Silver'),
        ('GOLD', 'Gold'),
        ('PLATINUM', 'Platinum'),
        ('DIAMOND', 'Diamond'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    points_earned = models.IntegerField(default=0)
    points_used = models.IntegerField(default=0)
    delivery_address = models.TextField()
    phone_number = models.CharField(max_length=20)
    membership_level = models.CharField(max_length=10, choices=MEMBERSHIP_LEVELS, default='BRONZE')

    def save(self, *args, **kwargs):
        """Save order and handle points calculation"""
        # Check if this is a new delivery completion
        is_newly_delivered = (
            self.pk is not None and  # Not a new order
            self.status == 'DELIVERED' and  # Status is delivered
            Order.objects.get(pk=self.pk).status != 'DELIVERED'  # Previous status wasn't delivered
        )
        
        # Calculate points only when order is newly marked as delivered
        if is_newly_delivered and not self.points_earned:
            # Get points multiplier based on membership level
            points_multiplier = {
                'BRONZE': 1,
                'SILVER': 1.2,
                'GOLD': 1.5,
                'PLATINUM': 2,
                'DIAMOND': 2.5
            }.get(self.membership_level, 1)
            
            # Calculate points earned
            self.points_earned = int(Decimal(str(self.total_amount)) / 1000 * points_multiplier)
            
            # Add points to user's profile
            if self.points_earned > 0:
                self.user.profile.add_points(self.total_amount)
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order {self.id} by {self.user.username}"

    def get_discount_percentage(self):
        discount_map = {
            'BRONZE': 0,
            'SILVER': 5,
            'GOLD': 10,
            'PLATINUM': 15,
            'DIAMOND': 20
        }
        return discount_map.get(self.membership_level, 0)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    size = models.ForeignKey(Size, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=0)

    def __str__(self):
        return f"{self.order.id} - {self.menu_item.name} ({self.size.get_size_display()})"

    def get_total(self):
        return self.price * self.quantity

class Comment(models.Model):
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Comment by {self.user.username} on {self.menu_item.name}'

    class Meta:
        ordering = ['-created_at']

class UserProfile(models.Model):
    MEMBERSHIP_LEVELS = [
        ('BRONZE', 'Bronze'),
        ('SILVER', 'Silver'),
        ('GOLD', 'Gold'),
        ('PLATINUM', 'Platinum'),
        ('DIAMOND', 'Diamond'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    points = models.IntegerField(default=0)
    membership_level = models.CharField(
        max_length=10,
        choices=MEMBERSHIP_LEVELS,
        default='BRONZE'
    )
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def update_membership_level(self):
        """Update membership level based on points"""
        old_level = self.membership_level
        
        # Calculate points thresholds
        if self.points >= 10000:
            new_level = 'DIAMOND'
        elif self.points >= 5000:
            new_level = 'PLATINUM'
        elif self.points >= 2000:
            new_level = 'GOLD'
        elif self.points >= 1000:
            new_level = 'SILVER'
        else:
            new_level = 'BRONZE'
        
        # Only update and save if the level has changed
        if old_level != new_level:
            self.membership_level = new_level
            self.save(update_fields=['membership_level'])
            return True
        return False

    def add_points(self, amount):
        """Add points from a purchase and update membership level"""
        # Calculate points to add (1 point per 1000 VND)
        points_to_add = int(Decimal(str(amount)) / 1000)
        
        # Add points
        self.points += points_to_add
        
        # Save points first
        self.save(update_fields=['points'])
        
        # Then update membership level
        self.update_membership_level()
        
        return points_to_add

    def __str__(self):
        return f"{self.user.username}'s Profile"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

class ShippingAddress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shipping_addresses')
    full_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    address = models.TextField()
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Shipping Addresses'
        ordering = ['-is_default', '-created_at']

    def __str__(self):
        return f"{self.full_name} - {self.address[:50]}"

    def save(self, *args, **kwargs):
        # If this address is set as default, unset all other default addresses for this user
        if self.is_default:
            ShippingAddress.objects.filter(user=self.user, is_default=True).exclude(id=self.id).update(is_default=False)
        super().save(*args, **kwargs)