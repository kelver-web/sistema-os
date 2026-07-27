from django.db import models


class Part(models.Model):
    name = models.CharField("Nome", max_length=200)
    manufacturer = models.CharField("Fabricante", max_length=200, blank=True)
    model_number = models.CharField("Número do modelo", max_length=100, blank=True)
    supplier = models.CharField("Fornecedor", max_length=200, blank=True)
    supplier_price = models.FloatField("Preço do fornecedor")
    sale_price = models.FloatField("Preço de venda")
    quantity = models.PositiveIntegerField("Quantidade")
    location = models.CharField("Local", max_length=100, blank=True)
    created_at = models.DateTimeField("Criado em", auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Peças"

    def __str__(self):
        return self.name


class PartMovement(models.Model):
    class MovementType(models.TextChoices):
        IN = "in", "Entrada"
        USED = "used", "Usado"

    part = models.ForeignKey(
        Part, on_delete=models.PROTECT, related_name="movements", verbose_name="Peça"
    )
    service_order = models.ForeignKey(
        "service_orders.ServiceOrder",
        on_delete=models.SET_NULL,
        related_name="part_movements",
        null=True,
        blank=True,
        verbose_name="Ordem de serviço",
    )
    movement_type = models.CharField(
        "Tipo", max_length=10, choices=MovementType.choices
    )
    quantity = models.PositiveIntegerField("Quantidade")
    unit_price = models.FloatField("Preço unitário")
    notes = models.TextField("Notas", blank=True)
    created_by = models.ForeignKey(
        "accounts.User", on_delete=models.PROTECT, verbose_name="Criado por"
    )
    created_at = models.DateTimeField("Criado em", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Movimentos de peças"

    def __str__(self):
        return f"{self.movement_type} - {self.part.name}"
