
from rest_framework import serializers
from .models import Documento

#convierte el documento json(para la api)
class DocumentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Documento
        fields = "__all__"
