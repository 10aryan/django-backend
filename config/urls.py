from django.urls import path, include
from django.contrib import admin
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from devices.views import signup 

urlpatterns = [
     # ADMIN PANEL 👇
    path('admin/', admin.site.urls),
    # AUTH
    path('api/signup/', signup),  # 👈 create user
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # DEVICES
    path('api/', include('devices.urls')),
]
