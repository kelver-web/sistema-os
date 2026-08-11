from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, validators=[validate_password]
        # Não deve ser mostrado na resposta
    )
    password_confirm = serializers.CharField(write_only=True) # Nao deve ser mostrado
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'password', 'password_confirm'
        ]
        
    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError(
                {'password_confirm': 'As senhas devem ser iguais.'}
            )
        
        return data
    
    def create(self, validated_data):
        validated_data.pop('password_confirm') # As senhas nao devem ser mostradas
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        
        return user
