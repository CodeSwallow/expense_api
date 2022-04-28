from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

from api.models import Account, Expense, Payment
# Create your tests here.


class AccountAndUserTest(APITestCase):

    def test_create_account(self):
        url = 'http://localhost:8000/api/'
        data = {"username": "test77", "email": "test@gmail.com", "password": "test77test"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.get().username, 'test77')
        self.assertEqual(Account.objects.count(), 1)
        self.assertEqual(Account.objects.get().owner.username, 'test77')


class ExpenseViewSetTest(APITestCase):
    jwt_url = 'http://localhost:8000/api/token/'
    basic_expense_data = {"name": "Pizza", "amount": 220, "category": "FO", "payment_date": "2022-4-28 23:59:59"}
    basic_expense_data_2 = {"name": "TV", "amount": 4220, "category": "HO", "payment_date": "2022-5-20 23:59:59"}
    basic_expense_data_3 = {"name": "Gas", "amount": 385, "category": "UT", "payment_date": "2022-6-20 23:59:59"}
    basic_expense_data_4 = {"name": "Water", "amount": 350, "category": "UT", "payment_date": "2022-4-28 23:59:59"}
    recurring_expense_data = {
        "name": "WoW",
        "amount": 200,
        "category": "PE",
        "number_of_recurrences": 3,
        "recurrence": "MO",
        "payment_date": "2022-3-31 23:59:59"
    }
    recurring_expense_data_2 = {
        "name": "Internet",
        "amount": 385,
        "category": "UT",
        "number_of_recurrences": 12,
        "recurrence": "MO",
        "payment_date": "2022-4-20 23:59:59"
    }

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="test77", email="test@gmail.com", password="test77test")
        Account.objects.create(owner=cls.user)

    def addItems(self):
        url = reverse('api:expenses-list')
        self.client.post(url, self.basic_expense_data, format='json')
        self.client.post(url, self.basic_expense_data_2, format='json')
        self.client.post(url, self.basic_expense_data_3, format='json')
        self.client.post(url, self.basic_expense_data_4, format='json')
        self.client.post(url, self.recurring_expense_data, format='json')
        self.client.post(url, self.recurring_expense_data_2, format='json')

    def authenticate(self):
        response = self.client.post(self.jwt_url, {"username": self.user.username, "password": "test77test"})
        assert response.status_code == status.HTTP_200_OK
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + response.data['access'])

    def test_can_create_basic_expense(self):
        self.authenticate()
        url = reverse('api:expenses-list')
        response = self.client.post(url, self.basic_expense_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        self.assertEqual(Expense.objects.count(), 1)
        self.assertFalse(response.data['recurring'])
        self.assertFalse(response.data['number_of_recurrences'])
        self.assertEqual(self.user, Account.objects.get(pk=response.data['account']).owner)
        self.assertEqual(len(response.data['payments']), Payment.objects.count())

    def test_can_create_recurring_expense(self):
        self.authenticate()
        url = reverse('api:expenses-list')
        response = self.client.post(url, self.recurring_expense_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        self.assertEqual(Expense.objects.count(), 1)
        self.assertTrue(response.data['recurring'])
        self.assertEqual(response.data['number_of_recurrences'], 3)
        self.assertEqual(self.user, Account.objects.get(pk=response.data['account']).owner)
        self.assertEqual(len(response.data['payments']), 4)
        self.assertEqual(Payment.objects.count(), 4)

    def test_can_view_all_expenses(self):
        self.authenticate()
        url = reverse('api:expenses-list')
        self.client.post(url, self.basic_expense_data, format='json')
        self.client.post(url, self.recurring_expense_data, format='json')
        response = self.client.get(url, format='json')
        assert response.status_code == status.HTTP_200_OK
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(Payment.objects.count(), 5)

    def test_can_view_expenses_by_month_without_params(self):
        self.authenticate()
        self.addItems()
        url = reverse('api:expenses-expenses-by-month')
        response = self.client.get(url, format='json')
        assert response.status_code == status.HTTP_200_OK
        self.assertEqual(response.data['month'], 'April')
        self.assertEqual(len(response.data['expenses']), 4)
        self.assertEqual(response.data['total'], 1155)

    def test_can_view_expenses_by_month_with_month_param(self):
        self.authenticate()
        self.addItems()
        url = reverse('api:expenses-expenses-by-month')+'?month=3'
        response = self.client.get(url, format='json')
        assert response.status_code == status.HTTP_200_OK
        self.assertEqual(response.data['month'], 'March')
        self.assertEqual(len(response.data['expenses']), 1)
        self.assertEqual(response.data['total'], 200)
        url = reverse('api:expenses-expenses-by-month')+'?month=1'
        response = self.client.get(url, format='json')
        assert response.status_code == status.HTTP_200_OK
        self.assertEqual(response.data['month'], 'January')
        self.assertEqual(len(response.data['expenses']), 0)
        self.assertEqual(response.data['total'], 0)
        url = reverse('api:expenses-expenses-by-month')+'?month=6'
        response = self.client.get(url, format='json')
        assert response.status_code == status.HTTP_200_OK
        self.assertEqual(response.data['month'], 'June')
        self.assertEqual(len(response.data['expenses']), 3)
        self.assertEqual(response.data['total'], 970)
        url = reverse('api:expenses-expenses-by-month')+'?month=10'
        response = self.client.get(url, format='json')
        assert response.status_code == status.HTTP_200_OK
        self.assertEqual(response.data['month'], 'October')
        self.assertEqual(len(response.data['expenses']), 1)
        self.assertEqual(response.data['total'], 385)
