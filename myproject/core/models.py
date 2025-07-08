from django.db import models
from django.contrib.auth.models import User 


class Addresses(models.Model):
    store = models.ForeignKey('Stores', on_delete=models.DO_NOTHING, null=True, blank=True)
    remote_id = models.BigIntegerField(null=True, blank=True)
    customer = models.ForeignKey('Customers', on_delete=models.SET_NULL, null=True, blank=True, related_name='addresses')
    order = models.ForeignKey('Orders', on_delete=models.CASCADE, related_name='addresses')
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    address1 = models.TextField(blank=True, null=True)
    address2 = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    zip = models.CharField(max_length=20, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        # managed = False
        db_table = 'addresses'
        
    def __str__(self):
        return f"{self.address1}, {self.city}"


class Customers(models.Model):
    store = models.ForeignKey('Stores', models.DO_NOTHING)
    remote_id = models.BigIntegerField(null=True, blank=True)
    email = models.CharField(max_length=255, blank=True, null=True)
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    verified_email = models.BooleanField(blank=True, null=True)
    currency = models.CharField(max_length=3, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        # managed = False
        db_table = 'customers'
        unique_together = (('store', 'remote_id'),)
        
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"


class FlaggedOrders(models.Model):
    order_id = models.IntegerField()
    rule = models.ForeignKey('Rules', models.DO_NOTHING)
    flagged_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        # managed = False
        db_table = 'flagged_orders'


class LineItems(models.Model):
    order = models.ForeignKey('Orders', related_name='lineitems', on_delete=models.CASCADE)
    sku = models.CharField(max_length=100, blank=True, null=True)
    remote_id = models.BigIntegerField(null=True, blank=True)
    name = models.TextField(blank=True, null=True)
    quantity = models.IntegerField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    fulfillment_status = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        # managed = False
        db_table = 'line_items'

class Orders(models.Model):
    DELIVERY_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('rto', 'RTO'),
        ('failed', 'Delivery Failed'),
    ]

    store = models.ForeignKey('Stores', models.DO_NOTHING)
    remote_id = models.BigIntegerField()
    order_number = models.IntegerField(blank=True, null=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    contact_email = models.CharField(max_length=255, blank=True, null=True)
    contact_phone = models.CharField(max_length=20, blank=True, null=True)
    financial_status = models.CharField(max_length=50, blank=True, null=True)
    delivery_status = models.CharField(
        max_length=20,
        choices=DELIVERY_STATUS_CHOICES,
        default='pending',
        blank=True,
        null=True
    )
    total_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    subtotal_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    total_tax = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    total_discounts = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    currency = models.CharField(max_length=3, blank=True, null=True)
    processed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    customer = models.ForeignKey(Customers, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    tags = models.TextField(blank=True, null=True)
    payment_gateway = models.CharField(max_length=100, blank=True, null=True)
    shipping_title = models.CharField(max_length=100, blank=True, null=True)
    shipping_code = models.CharField(max_length=50, blank=True, null=True)
    shipping_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    # csv_upload = models.ForeignKey('CSVUpload', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        # managed = False
        db_table = 'orders'
        unique_together = (('store', 'remote_id'),)
        indexes = [
            models.Index(fields=['financial_status']),
            models.Index(fields=['delivery_status']),
            models.Index(fields=['contact_phone']),
            models.Index(fields=['created_at']),
        ]
        
    def __str__(self):
        return f"Order #{self.order_number} - {self.total_price}"


class Rules(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    condition = models.JSONField(blank=True, null=True)
    scope = models.CharField(max_length=20, blank=True, null=True)
    store = models.ForeignKey('Stores', models.DO_NOTHING, blank=True, null=True)
    is_enabled = models.BooleanField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        # managed = False
        db_table = 'rules'


class Stores(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True)
    shopify_domain = models.CharField(unique=True, max_length=255, blank=True, null=True)
    access_token = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        # managed = False
        db_table = 'stores'
        

# from django.contrib.auth import get_user_model
# User = get_user_model()

# class CSVUpload(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     file_name = models.CharField(max_length=255)
#     uploaded_at = models.DateTimeField(auto_now_add=True)
#     record_count = models.IntegerField(default=0)
#     store = models.ForeignKey('Stores', on_delete=models.SET_NULL, null=True, blank=True)
#     status = models.CharField(max_length=20, default='completed', choices=[
#         ('processing', 'Processing'),
#         ('completed', 'Completed'),
#         ('failed', 'Failed')
#     ])

#     class Meta:
#         ordering = ['-uploaded_at']
        
#     def __str__(self):
#         return f"{self.file_name} - {self.uploaded_at.strftime('%Y-%m-%d %H:%M')}"

# class UploadBatch(models.Model):
#     created_at = models.DateTimeField(auto_now_add=True)
#     user = models.ForeignKey(User, on_delete=models.CASCADE)