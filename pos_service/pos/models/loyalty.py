"""Loyalty program models"""
import uuid
from django.db import models


class LoyaltyProgram(models.Model):
    """Loyalty/rewards program"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    corporate_id = models.UUIDField(db_index=True)
    name = models.CharField(max_length=255)
    points_per_currency = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    redemption_ratio = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    min_points_redemption = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'pos_loyalty_program'
        ordering = ['name']

    def __str__(self):
        return self.name


class LoyaltyCard(models.Model):
    """Customer loyalty card"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    program = models.ForeignKey(LoyaltyProgram, on_delete=models.CASCADE, related_name='cards')
    customer_id = models.UUIDField(db_index=True)
    card_number = models.CharField(max_length=50, unique=True, db_index=True)
    points_balance = models.IntegerField(default=0)
    total_earned = models.IntegerField(default=0)
    total_redeemed = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'pos_loyalty_card'
        ordering = ['-created_at']

    def __str__(self):
        return f"Card {self.card_number}"
