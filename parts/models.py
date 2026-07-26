from django.db import models


class Part(models.Model):
    name = models.CharField(max_length=200)
    manufacturer = models.CharField(max_length=200, blank=True)
    model_number = models.CharField(max_length=100, blank=True)
    supplier = models.CharField(max_length=200, blank=True)
    supplier_price = models.FloatField()
    sale_price = models.FloatField()
    quantity = models.PositiveIntegerField()
    location = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Peças'
        
    def __str__(self):
        return self.name
    

class PartMovement(models.Model):
    class MovementType(models.TextChoices):
        IN = 'in', 'Entrada'
        USED = 'used', 'Usado'
    
    part = models.ForeignKey(
        Part, on_delete=models.PROTECT, related_name='movements'
    )
    service_order = models.ForeignKey(
        'service_orders.ServiceOrder', on_delete=models.SET_NULL, related_name='part_movements',
        null=True, blank=True
    )
    movement_type = models.CharField(max_length=10, choices=MovementType.choices)
    quantity = models.PositiveIntegerField()
    unit_price = models.FloatField()
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        'accounts.User', on_delete=models.PROTECT
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Movimentos de peças'
        
    def __str__(self):
        return f'{self.movement_type} - {self.part.name}'