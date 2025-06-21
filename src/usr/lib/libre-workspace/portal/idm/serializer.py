from rest_framework import serializers

# users.append({"dn": dn, "displayName": displayName, "mail": mail, "cn": cn, "groups": groups, "guid": guid, "enabled": enabled, "admin": is_user_in_group({"groups": groups}, "Administrators")})

class UserSerializer(serializers.Serializer):
    """
    Serializer for basic user data.
    """
    username = serializers.CharField(max_length=100, required=False, read_only=True)
    first_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    displayName = serializers.CharField( max_length=100, required=False, allow_blank=True)
    mail = serializers.EmailField(max_length=100, required=False, allow_blank=True)
    admin = serializers.BooleanField(required=False, default=False)
    enabled = serializers.BooleanField(required=False, default=True)

    # Translate the fields from ldap space to the serializer space
    def to_representation(self, instance):
        print(instance)
        representation = super().to_representation(instance)
        representation['username'] = instance.get('cn', '')
        representation['displayName'] = instance.get('displayName', '')
        return representation
    


class GroupSerializer(serializers.Serializer):
    """
    Serializer for group data.
    """
    cn = serializers.CharField(max_length=100, required=True)
    description = serializers.CharField(max_length=100, required=False, allow_blank=True)
    defaultGroup = serializers.BooleanField(required=False, default=False)
    nextcloud_groupfolder = serializers.BooleanField(required=False, default=False)

    def validate_cn(self, value):
        if not value.isalnum():
            raise serializers.ValidationError("Group name must be alphanumeric.")
        return value