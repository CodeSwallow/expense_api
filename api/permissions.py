from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from rest_framework.permissions import BasePermission
from api.models import Account


class IsOwner(BasePermission):

    def has_object_permission(self, request, view, obj):
        return obj.owner == get_object_or_404(User, pk=request.user.id)


class AccountPermission(BasePermission):

    def has_object_permission(self, request, view, obj):
        return obj.account == get_object_or_404(Account, owner=request.user.id)


class PaymentPermission(BasePermission):

    def has_object_permission(self, request, view, obj):
        return obj.expense.account == get_object_or_404(Account, owner=request.user.id)
