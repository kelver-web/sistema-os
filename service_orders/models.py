from django.db import models
from django.conf import settings


class ServiceOrder(models.Model):
    class Priority(models.IntegerChoices):
        LOW = 1, 'Baixa'
        MEDIUM = 2, 'Média'
        HIGH = 3, 'Alta'
        URGENT = 4, 'Urgente'
        
    class Status(models.TextChoices):
        PANDING = 'PENDING', 'Pendente'
        AWAITING_PARTS = 'AWAITING_PARTS', 'Aguardando peças'
        IN_PROGRESS = 'IN_PROGRESS', 'Em andamento'
        AWAITING_APPROVAL = 'AWAITING_APPROVAL', 'Aguardando aprovação'
        COMPLETED = 'COMPLETED', 'Concluído'
        DELIVERED = 'DELIVERED', 'Entregue'
        CANCELED = 'CANCELED', 'Cancelado'
        
    client = models.ForeignKey(
        'clients.Client', on_delete=models.PROTECT, related_name='service_orders',
        verbose_name='Cliente'
    )
    equipment = models.ForeignKey(
        'equipments.Equipment', on_delete=models.PROTECT, related_name='service_orders',
        verbose_name='Equipamento'
    )
    opened_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='service_orders',
        verbose_name='Aberta por'
    )
    technician = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='assigned_orders',
        null=True, blank=True, verbose_name='Técnico'
    )
    reported_problem = models.TextField('Problema relatado')
    technical_fidings = models.TextField('Problema técnico', blank=True)
    solution_description = models.TextField('Solução', blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PANDING
    )
    priority = models.IntegerField('Prioridade', choices=Priority.choices, default=Priority.MEDIUM)
    estimated_cost = models.DecimalField('Preço estimado', max_digits=10, decimal_places=2, null=True, blank=True)
    final_cost = models.DecimalField('Preço final', max_digits=10, decimal_places=2, null=True, blank=True)
    opened_at = models.DateTimeField('Aberta em', auto_now_add=True)
    started_at = models.DateTimeField('Iniciada em', null=True, blank=True)
    completed_at = models.DateTimeField('Completada em', null=True, blank=True)
    delivered_at = models.DateTimeField('Entregue em', null=True, blank=True)
    deadline = models.DateTimeField('Prazo', null=True, blank=True)
    
    class Meta:
        ordering = ['-priority', 'opened_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['technician', 'status']),
        ]
        verbose_name_plural = 'Ordens de Serviço'
    
    def __str__(self):
        return f'OS #{self.pk} - {self.client.name} ({self.get_status_display()})'


class ServiceOrderItem(models.Model):
    service_order = models.ForeignKey(
        'service_orders.ServiceOrder', on_delete=models.CASCADE, related_name='items',
        verbose_name='Ordem de serviço'
    )
    description = models.CharField('Descrição', max_length=255)
    quantity = models.PositiveIntegerField('Quantidade', default=1)
    unit_price = models.DecimalField('Preço unitário', max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    
    class Meta:
        verbose_name_plural = 'Itens do serviço'
    
    def save(self, *args, **kwargs):
        self.total = self.quantity * self.unit_price
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.description


class ServiceTimeLine(models.Model):
    service_order = models.ForeignKey(
        'service_orders.ServiceOrder', on_delete=models.CASCADE, related_name='timeline',
        verbose_name='Ordem de serviço'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        verbose_name='Usuário'
    )
    action = models.CharField('Ação', max_length=100)
    description = models.TextField('Descrição')
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
        verbose_name_plural = 'Entradas do serviço'
        
    def __str__(self):
        return f'{self.action} - {self.service_order}'
