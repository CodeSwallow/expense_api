from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework import viewsets, status
from datetime import datetime
from django.utils import timezone
from dateutil.relativedelta import relativedelta

from api.permissions import AccountPermission, PaymentPermission
from api.paginations import SmallResultsSetPagination, StandardResultsSetPagination
from api.serializers import (
    UserSerializer,
    AccountSerializer,
    ExpenseSerializer,
    PaymentSerializer
)
from api.models import Account, Expense, Payment

# Create your views here.


@api_view(['GET', 'POST'])
def create_user(request):
    if request.method == 'POST':
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response({'response': 'Use POST method to create user. (username, email, password)'})


class AccountViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Account.objects.all()

    def list(self, request):
        account = get_object_or_404(self.queryset, owner=self.request.user.id)
        serializer = AccountSerializer(account)
        return Response(serializer.data)


class ExpenseViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, AccountPermission]
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        account = get_object_or_404(Account, owner=self.request.user.id)
        filters = {"account": account}
        self.queryset = self.queryset.filter(**filters)
        return self.queryset

    def create(self, request, *args, **kwargs):
        today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        payment_date = request.data.pop('payment_date', today)
        serializer = self.get_serializer(data=request.data, context={'payment_date': payment_date})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        account = get_object_or_404(Account, owner=self.request.user.id)
        serializer.save(account=account)

    @action(detail=False, methods=['get'])
    def expenses_by_category(self, request):
        self.pagination_class = SmallResultsSetPagination
        category = request.query_params.get('category', None)
        if category:
            expenses = Expense.objects.filter(category=category).order_by("-date_created")
            page = self.paginate_queryset(expenses)

            if page:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(expenses, many=True)
            return Response(serializer.data)
        return Response({"response": "No category chosen."})

    @action(detail=False, methods=['get'])
    def most_recent_expenses(self, request):
        self.pagination_class = SmallResultsSetPagination
        expenses = Expense.objects.all().order_by('-date_created')
        page = self.paginate_queryset(expenses)

        if page:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(expenses, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def expenses_by_month(self, request):
        today = timezone.now()
        month = request.query_params.get('month', today.month)
        year = request.query_params.get('year', today.year)
        try:
            month = int(month)
            year = int(year)
            date = datetime(year, month, 1)
        except (TypeError, ValueError) as e:
            return Response({"error": f"Query must be valid integer: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        filters = {"payments__date__month": month, "payments__date__year": year}
        expenses = Expense.objects.filter(**filters)
        total = sum(expense.amount for expense in expenses)
        serializer = self.get_serializer(expenses, many=True)
        response = {"month": date.strftime("%B"), "expenses": serializer.data, "total": total}
        return Response(response)

    @action(detail=False, methods=['get'])
    def expenses_so_far(self, request):
        return Response({"status": "End point not yet implemented"}, status=status.HTTP_501_NOT_IMPLEMENTED)


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated, PaymentPermission]
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    pagination_class = SmallResultsSetPagination

    @action(detail=False, methods=['get'])
    def upcoming_payments(self, request):
        today = timezone.now()
        payments = Payment.objects.filter(date__gte=today)
        page = self.paginate_queryset(payments)

        if page:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(payments, many=True)
        return Response(serializer.data)

