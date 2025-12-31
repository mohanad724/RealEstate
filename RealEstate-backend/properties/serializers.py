from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Property, Category, Purchase, Profile
from .models import Comment 
#  Profile Serializer
class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['phone', 'image']


#  User Registration Serializer
class RegisterSerializer(serializers.ModelSerializer):
    name = serializers.CharField(write_only=True)
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('name', 'email', 'password')

    def create(self, validated_data):
        name = validated_data.get('name')
        email = validated_data.get('email')
        password = validated_data.get('password')
        user = User.objects.create_user(
            username=email,
            first_name=name,
            email=email,
            password=password,
        )
        return user


#  Category Serializer
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


#  Property Serializer
class PropertySerializer(serializers.ModelSerializer):
    image_path = serializers.ImageField(required=False)
    is_favorite = serializers.SerializerMethodField()

    name = serializers.CharField(required=False)
    type = serializers.CharField(required=False)
    location = serializers.CharField(required=False)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    transaction_type = serializers.CharField(required=False)
    is_featured = serializers.BooleanField(required=False)
    is_favorite = serializers.BooleanField(required=False)
    status = serializers.CharField(required=False)

    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True,
        required=False
    )
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Property
        fields = '__all__'
        read_only_fields = ['added_by']

    def get_is_favorite(self, obj):
        request = self.context.get('request')
        user = request.user if request else None
        return obj.is_favorite_for(user) if user and user.is_authenticated else False

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        image_field = instance.image_path
        if image_field:
            if image_field.name.startswith("http"):
                representation["image_path"] = image_field.name
            else:
                request = self.context.get("request")
                if request:
                    representation["image_path"] = request.build_absolute_uri(image_field.url)
                else:
                    representation["image_path"] = image_field.url
        else:
            representation["image_path"] = ""

        if instance.added_by:
            representation['added_by_user_id'] = instance.added_by.id
            representation['added_by_user_name'] = instance.added_by.first_name or instance.added_by.username
        else:
            representation['added_by_user_id'] = None
            representation['added_by_user_name'] = ""

        return representation

    def create(self, validated_data):
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user
            validated_data["added_by"] = user

            if not user.is_staff:
                validated_data["is_featured"] = False
                validated_data["status"] = "pending"
            else:
                validated_data.setdefault("status", "approved")

        return super().create(validated_data)


#  Serializer for CartItem (Used in Checkout)
class CartItemSerializer(serializers.Serializer):
    property_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)

    def validate_property_id(self, value):
        if not Property.objects.filter(id=value).exists():
            raise serializers.ValidationError("This property does not exist.")
        return value

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0.")
        return value


#  Purchase Serializer
class PurchaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Purchase
        fields = ['user', 'property', 'quantity', 'purchase_date']

    def create(self, validated_data):
        return Purchase.objects.create(**validated_data)


class CommentSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'user', 'property', 'content', 'created_at', 'user_name']
        read_only_fields = ['user', 'created_at']

    def get_user_name(self, obj):
        return obj.user.first_name or obj.user.username

