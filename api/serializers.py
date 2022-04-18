from rest_framework import serializers
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime
from dateutil.relativedelta import relativedelta

from api.models import Account, Expense, Payment


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        Account.objects.create(owner=user)
        return user


class AccountSerializer(serializers.ModelSerializer):

    class Meta:
        model = Account
        fields = '__all__'


class PaymentSerializer(serializers.ModelSerializer):
    expense = serializers.StringRelatedField(source='expense.amount')
    name = serializers.StringRelatedField(source='expense.name')

    class Meta:
        model = Payment
        fields = ['id', 'expense', 'date', 'name']


class ExpenseSerializer(serializers.ModelSerializer):
    recurring = serializers.ReadOnlyField()
    recurrence_until_cancelled = serializers.ReadOnlyField()
    payments = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = Expense
        fields = '__all__'

    def create(self, validated_data):
        recurrences = validated_data.get('number_of_recurrences', 0)
        payment_date = datetime.strptime(self.context['payment_date'], "%Y-%m-%d %H:%M:%S")
        payment_date_aware = timezone.make_aware(payment_date)
        print(f"Payment date naive: {payment_date}")
        print(f"Payment date aware: {payment_date_aware}")
        expense = Expense.objects.create(**validated_data)
        Payment.objects.create(expense=expense, date=payment_date_aware)
        for i in range(recurrences):
            Payment.objects.create(expense=expense, date=(payment_date_aware+relativedelta(months=i+1)))
        return expense
