from django.conf import settings
from django.db import models


class Client(models.Model):
    name = models.CharField("Nome", max_length=255)
    email = models.EmailField("E-mail", unique=True)
    phone = models.CharField("Telefone", max_length=20)
    address = models.TextField("Endereço", blank=True)
    document = models.CharField("Documento", max_length=20, blank=True)
    notes = models.TextField("Notas", blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="clients",
        verbose_name="Criado por",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        ordering = ["name"]
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"

    def __str__(self):
        return self.name
