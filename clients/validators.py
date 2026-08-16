from validate_docbr import CNPJ, CPF

from rest_framework import serializers

import re


def validate_document(value):
    numbers = re.sub(r"\D", "", value or "")

    if not numbers:  # Se o campo estiver vazio, retorna sem validação.
        return

    if len(numbers) == 11:
        if not CPF().validate(numbers):
            raise serializers.ValidationError(
                "CPF inválido, verifique os dados informados."
            )
    elif len(numbers) == 14:
        if not CNPJ().validate(numbers):
            raise serializers.ValidationError(
                "CNPJ inválido, verifique os dados informados."
            )
    else:
        raise serializers.ValidationError(
            "Documento deve ter 11 dígitos (CPF) ou 14 dígitos (CNPJ)."
        )
