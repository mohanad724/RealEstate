from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter

from .views import (
    LoginView,
    RegisterView,
    UserProfileView,
    UserPurchasesView,
    CategoryViewSet,
    PropertyViewSet,
    checkout_cart,
    update_user_profile,
    send_notification,
    add_to_user_purchases,
    list_all_comments,
    delete_comment,
)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'properties', PropertyViewSet, basename='property')

urlpatterns = [
    path('', include(router.urls)),

    # Authentication endpoints
    path('login/', LoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),

    # User profile endpoints
    path('user/profile/', UserProfileView.as_view(), name='user-profile'),
    path('user/profile/update/', update_user_profile, name='user-profile-update'),

    # Purchase endpoints
    path('user/purchases/', UserPurchasesView.as_view(), name='user-purchases'),
    path('user/purchases/add/', add_to_user_purchases, name='add-user-purchase'),

    # Cart endpoints
    path('cart/checkout/', checkout_cart, name='cart-checkout'),

    # Notification endpoints
    path('notifications/', send_notification, name='send-notification'),

    # Admin comment management
    path('admin/comments/', list_all_comments, name='admin-list-comments'),
    path(
        'admin/comments/<int:comment_id>/delete/',
        delete_comment,
        name='admin-delete-comment'
    ),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
