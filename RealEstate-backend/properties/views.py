from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views import View

from rest_framework import viewsets, status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, action, permission_classes, parser_classes
from rest_framework.permissions import (
    IsAuthenticated,
    IsAdminUser,
    AllowAny
)
from rest_framework.parsers import (
    MultiPartParser,
    FormParser,
    JSONParser
)
from rest_framework.authtoken.models import Token

from .models import (
    Property,
    Category,
    Purchase,
    Comment
)
from .serializers import (
    RegisterSerializer,
    PropertySerializer,
    CategorySerializer,
    CommentSerializer
)


# ----------------------------
# Featured properties (public)
# ----------------------------
class FeaturedPropertiesView(View):
    def get(self, request, *args, **kwargs):
        featured_properties = Property.objects.filter(
            is_featured=True,
            status='approved'
        )

        data = []
        for prop in featured_properties:
            data.append({
                "id": prop.id,
                "name": prop.name,
                "image_path": prop.image_path.url if prop.image_path else "",
                "type": prop.type,
                "location": prop.location,
                "price": str(prop.price),
                "is_featured": prop.is_featured,
                "status": prop.status,
                "category": {
                    "id": prop.category.id,
                    "name": prop.category.name,
                    "icon": prop.category.icon,
                }
            })

        return JsonResponse(data, safe=False)


# ----------------------------
# Purchases & cart
# ----------------------------
@api_view(['POST'])
def add_to_user_purchases(request):
    user_id = request.data.get('user_id')
    property_id = request.data.get('property_id')

    try:
        user = User.objects.get(id=user_id)
        property_obj = Property.objects.get(id=property_id)
        Purchase.objects.create(user=user, property=property_obj)
        return Response({"message": "Property added successfully"}, status=status.HTTP_201_CREATED)

    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    except Property.DoesNotExist:
        return Response({"error": "Property not found"}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def checkout_cart(request):
    items = request.data.get("items", [])

    if not items:
        return Response({"error": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)

    for item in items:
        property_id = item.get("property_id")
        quantity = item.get("quantity", 1)

        try:
            property_obj = Property.objects.get(id=property_id)
            for _ in range(quantity):
                Purchase.objects.create(user=request.user, property=property_obj)

        except Property.DoesNotExist:
            return Response(
                {"error": f"Property {property_id} not found"},
                status=status.HTTP_404_NOT_FOUND
            )

    return Response({"message": "Checkout completed successfully"}, status=status.HTTP_200_OK)


# ----------------------------
# Notifications (admin)
# ----------------------------
@api_view(['POST'])
@permission_classes([IsAdminUser])
@parser_classes([JSONParser])
def send_notification(request):
    user_id = request.data.get('user_id')
    message = request.data.get('message')

    if not user_id or not message:
        return Response(
            {"error": "user_id and message are required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Placeholder notification logic
    print(f"Notification to user {user_id}: {message}")

    return Response(
        {"message": "Notification sent successfully"},
        status=status.HTTP_200_OK
    )


# ----------------------------
# Authentication
# ----------------------------
class LoginView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response(
                {"error": "Username and password are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(username=username, password=password)
        if not user:
            return Response(
                {"error": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            "token": token.key,
            "is_admin": user.is_staff
        }, status=status.HTTP_200_OK)


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Account created successfully"},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ----------------------------
# User profile
# ----------------------------
class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = getattr(request.user, 'profile', None)
        image_url = ''

        if profile and profile.image:
            image_url = request.build_absolute_uri(profile.image.url)

        return Response({
            "name": request.user.first_name or request.user.username,
            "email": request.user.email,
            "phone": profile.phone if profile else "",
            "is_admin": request.user.is_staff,
            "image_url": image_url
        }, status=status.HTTP_200_OK)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def update_user_profile(request):
    user = request.user
    profile = getattr(user, 'profile', None)

    if not profile:
        return Response(
            {"error": "Profile not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    phone = request.data.get('phone')
    password = request.data.get('password')
    image = request.FILES.get('image')

    if phone:
        profile.phone = phone
    if image:
        profile.image = image
    if password:
        user.set_password(password)
        user.save()

    profile.save()
    return Response({"message": "Profile updated successfully"}, status=status.HTTP_200_OK)


class UserPurchasesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        purchases = Purchase.objects.filter(user=request.user)
        result = []

        for purchase in purchases:
            if purchase.property:
                serialized_property = PropertySerializer(
                    purchase.property,
                    context={'request': request}
                ).data
            else:
                serialized_property = None

            result.append({
                "id": purchase.id,
                "property": serialized_property,
                "quantity": purchase.quantity,
                "purchase_date": purchase.purchase_date,
            })

        return Response(result, status=status.HTTP_200_OK)


# ----------------------------
# Comments (admin & public)
# ----------------------------
@api_view(['GET'])
@permission_classes([IsAdminUser])
def list_all_comments(request):
    comments = Comment.objects.select_related(
        'user',
        'property'
    ).order_by('-created_at')

    serializer = CommentSerializer(comments, many=True)
    return Response(serializer.data)


@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def delete_comment(request, comment_id):
    try:
        comment = Comment.objects.get(id=comment_id)
        comment.delete()
        return Response(
            {"message": "Comment deleted successfully"},
            status=status.HTTP_200_OK
        )
    except Comment.DoesNotExist:
        return Response(
            {"error": "Comment not found"},
            status=status.HTTP_404_NOT_FOUND
        )


# ----------------------------
# Category ViewSet
# ----------------------------
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


# ----------------------------
# Property ViewSet
# ----------------------------
class PropertyViewSet(viewsets.ModelViewSet):
    serializer_class = PropertySerializer
    parser_classes = (MultiPartParser, FormParser)

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Property.objects.all()
        return Property.objects.filter(status='approved')

    @action(detail=False, methods=['get'])
    def featured(self, request):
        queryset = Property.objects.filter(is_featured=True)
        serializer = self.get_serializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_category(self, request):
        category_id = request.query_params.get('category_id')
        if not category_id:
            return Response(
                {"error": "category_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            category = Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            return Response(
                {"error": "Category not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        properties = Property.objects.filter(category=category)
        serializer = self.get_serializer(properties, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def search(self, request):
        query = request.query_params.get('q')
        if not query:
            return Response(
                {"error": "Search query is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        queryset = Property.objects.filter(name__icontains=query)
        serializer = self.get_serializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def pending(self, request):
        queryset = Property.objects.filter(status='pending')
        serializer = self.get_serializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        property_obj = self.get_object()
        property_obj.favorites.add(request.user)
        return Response({"message": "Added to favorites"}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def unfavorite(self, request, pk=None):
        property_obj = self.get_object()
        property_obj.favorites.remove(request.user)
        return Response({"message": "Removed from favorites"}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def buy(self, request, pk=None):
        property_obj = self.get_object()
        Purchase.objects.create(user=request.user, property=property_obj)
        return Response({"message": "Property purchased successfully"}, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=['get', 'post'],
        permission_classes=[AllowAny],
        parser_classes=[JSONParser]
    )
    def comments(self, request, pk=None):
        property_obj = self.get_object()

        if request.method == 'GET':
            comments = Comment.objects.filter(property=property_obj).order_by('-created_at')
            serializer = CommentSerializer(comments, many=True)
            return Response(serializer.data)

        if not request.user.is_authenticated:
            return Response(
                {"error": "Authentication required"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        content = request.data.get('content')
        if not content:
            return Response(
                {"error": "Comment content is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        comment = Comment.objects.create(
            property=property_obj,
            user=request.user,
            content=content
        )
        serializer = CommentSerializer(comment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
