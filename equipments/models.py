from django.db import models


class Equipment(models.Model):
    class Category(models.TextChoices):
        COMPUTING = 'informatica', 'Informática'
        ELECTRONICS = 'eletronicos', 'Eletrônicos'
        TELEPHONY = 'telefonia', 'Telefonia'
        PRINTERS = 'impressoras', 'Impressoras'
        HOME_APPLIANCES = 'eletrodomesticos', 'Eletrodomésticos'
        OTHERS = 'outros', 'Outros'
    
    client = models.ForeignKey('clients.Client', on_delete=models.CASCADE, related_name='equipment')
    category = models.CharField(max_length=20, choices=Category.choices)
    brand = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    serial_number = models.CharField(max_length=100, unique=True, blank=True)
    accessories = models.TextField(blank=True)
    condition = models.TextField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f'{self.brand} {self.model} ({self.serial_number})'
