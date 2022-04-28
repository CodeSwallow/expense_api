from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api import views

router = DefaultRouter()
router.register(r'account', views.AccountViewSet, basename='account')
router.register(r'expenses', views.ExpenseViewSet, basename='expenses')
router.register(r'payments', views.PaymentViewSet, basename='payments')

app_name = "api"
urlpatterns = [
    path('', views.create_user),
    path('', include(router.urls)),
]
