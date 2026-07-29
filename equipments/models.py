from django.db import models


class Equipment(models.Model):
    class Category(models.TextChoices):
        COMPUTING = "informatica", "Informática"
        ELECTRONICS = "eletronicos", "Eletrônicos"
        TELEPHONY = "telefonia", "Telefonia"
        PRINTERS = "impressoras", "Impressoras"
        HOME_APPLIANCES = "eletrodomesticos", "Eletrodomésticos"
        OTHERS = "outros", "Outros"

    client = models.ForeignKey(
        "clients.Client",
        on_delete=models.CASCADE,
        related_name="equipment",
        verbose_name="Cliente",
    )
    category = models.CharField("Categoria", max_length=20, choices=Category.choices)
    brand = models.CharField("Marca", max_length=100)
    model = models.CharField("Modelo", max_length=100)
    serial_number = models.CharField(
        "Número de série", max_length=100, unique=True, blank=True,
        null=True
    )
    accessories = models.TextField("Acessorios", blank=True)
    condition = models.TextField("Condição", max_length=100)
    created_at = models.DateTimeField("Criado em", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Equipamentos"

    def __str__(self):
        return f"{self.brand} {self.model} ({self.serial_number})"
    
    def save(self, *args, **kwargs):
        if not self.serial_number:
            self.serial_number = None
        super().save(*args, **kwargs)
