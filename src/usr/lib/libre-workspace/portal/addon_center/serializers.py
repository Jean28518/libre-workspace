from rest_framework import serializers

class AddonSerializer(serializers.Serializer):
    """
    Serializer for Addon data.
    """
    id = serializers.CharField(max_length=100)
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(max_length=1000, allow_blank=True)
    version = serializers.CharField(max_length=50)
    maintainer = serializers.CharField(max_length=255, allow_blank=True)
    homepage = serializers.URLField(allow_blank=True)
    installed = serializers.BooleanField(default=False)
    icon_url = serializers.URLField(allow_blank=True)

    def validate_id(self, value):
        if not value.isalnum():
            raise serializers.ValidationError("ID must be alphanumeric.")
        return value

