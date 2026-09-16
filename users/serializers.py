from django.contrib.auth import get_user_model
from rest_framework import serializers


User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):

    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "phone_number",
            "role",
        ]

    def create(self, validated_data):
        password = validated_data.pop("password")

        user = User(**validated_data)
        user.set_password(password)#Django hashes the password and stores it in the database.
        #This is important for security reasons, as storing plain text passwords is a major security risk. 
        # The set_password method takes care of hashing the password before saving it to the database.
        user.save()

        return user