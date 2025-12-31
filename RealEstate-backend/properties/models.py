from django.db import models
from django.contrib.auth.models import User


# User profile model (extends Django's built-in User model)
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, blank=True)
    image = models.ImageField(upload_to='profile_images/', blank=True, null=True)

    def __str__(self):
        return self.user.username


# Category model
class Category(models.Model):
    name = models.CharField(max_length=100)
    icon = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


# Property model
class Property(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    TRANSACTION_CHOICES = [
        ('sale', 'Sale'),
        ('rent', 'Rent'),
    ]

    name = models.CharField(max_length=255)
    image_path = models.ImageField(upload_to='property_images/', blank=True, null=True)
    type = models.CharField(max_length=100)
    location = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(
        max_length=50,
        choices=TRANSACTION_CHOICES,
        default='sale'
    )

    is_featured = models.BooleanField(default=False)

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='properties'
    )
    favorites = models.ManyToManyField(
        User,
        related_name='favorite_properties',
        blank=True
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )
    added_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='added_properties'
    )

    def __str__(self):
        return self.name

    def is_favorite_for(self, user):
        if not user or not user.is_authenticated:
            return False
        return self.favorites.filter(id=user.id).exists()


# Purchase model
class Purchase(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='purchases'
    )
    property = models.ForeignKey(
        Property,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    quantity = models.PositiveIntegerField(default=1)
    purchase_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        property_name = self.property.name if self.property else 'Deleted Property'
        return f'{self.user.username} - {property_name} (x{self.quantity})'


# Comment / review model
class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username}: {self.content[:30]}'
