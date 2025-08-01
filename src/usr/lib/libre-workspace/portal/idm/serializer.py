from rest_framework import serializers

# users.append({"dn": dn, "displayName": displayName, "mail": mail, "cn": cn, "groups": groups, "guid": guid, "enabled": enabled, "admin": is_user_in_group({"groups": groups}, "Administrators")})

class UserSerializer(serializers.Serializer):
    """
    Serializer for basic user data.
    """
    username = serializers.CharField(max_length=100, required=False, read_only=True)
    first_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    display_name = serializers.CharField( max_length=100, required=False, allow_blank=True)
    mail = serializers.EmailField(max_length=100, required=False, allow_blank=True)
    admin = serializers.BooleanField(required=False, default=False)
    enabled = serializers.BooleanField(required=False, default=True)

    # Translate the fields from ldap space to the serializer space
    def to_representation(self, instance):
        print(instance)
        representation = super().to_representation(instance)
        representation['username'] = instance.get('cn', '')
        representation['display_name'] = instance.get('displayName', '')
        return representation
    


class GroupSerializer(serializers.Serializer):
    """
    Serializer for group data.
    """
    name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    description = serializers.CharField(max_length=100, required=False, allow_blank=True)
    default = serializers.BooleanField(required=False, default=False)
   
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        print(instance)
        representation['name'] = instance.get('cn', '')
        representation['default'] = instance.get('defaultGroup', False)
        return representation


class LinuxUserSerializer(serializers.Serializer):
    """
    Serializer for Linux user data.
    """
    dn = serializers.CharField(max_length=255, required=False, allow_blank=True)
    display_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    mail = serializers.EmailField(max_length=100, required=False, allow_blank=True)
    cn = serializers.CharField(max_length=100, required=False, allow_blank=True)
    username = serializers.CharField(max_length=100, required=False, allow_blank=True)
    groups = serializers.ListField(child=serializers.DictField(), required=False, default=list)
    guid = serializers.CharField(max_length=100, required=False, allow_blank=True)
    enabled = serializers.BooleanField(required=False, default=True)
    admin = serializers.BooleanField(required=False, default=False)
    yescrypt_hash = serializers.CharField(max_length=100, required=False, allow_blank=True)
    uidNumber = serializers.CharField(max_length=100, required=False, allow_blank=True)
    enabled = serializers.BooleanField(required=False, default=True)
    admin = serializers.BooleanField(required=False, default=False)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['display_name'] = instance.get('displayName', '')
        return representation