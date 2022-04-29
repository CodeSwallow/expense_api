from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase
from freezegun import freeze_time

from api.models import Account, Expense, Payment
# Create your tests here.

JWT_URL = 'http://localhost:8000/api/token/'
BASIC_EXPENSE_1 = {"name": "Pizza", "amount": 220, "category": "FO", "payment_date": "2022-4-28 23:59:59"}
BASIC_EXPENSE_2 = {"name": "TV", "amount": 4220, "category": "HO", "payment_date": "2022-5-20 23:59:59"}
BASIC_EXPENSE_3 = {"name": "Gas", "amount": 385, "category": "UT", "payment_date": "2022-6-20 23:59:59"}
BASIC_EXPENSE_4 = {"name": "Water", "amount": 350, "category": "UT", "payment_date": "2022-4-28 23:59:59"}
BASIC_EXPENSE_5 = {"name": "Ibuprofen", "amount": 150, "category": "ME", "payment_date": "2022-4-10 23:59:59"}
BASIC_EXPENSE_6 = {"name": "Table", "amount": 1250, "category": "HO"}
RECURRING_EXPENSE_1 = {
    "name": "WoW",
    "amount": 200,
    "category": "PE",
    "number_of_recurrences": 3,
    "recurrence": "MO",
    "payment_date": "2022-3-31 23:59:59"
}
RECURRING_EXPENSE_2 = {
    "name": "Internet",
    "amount": 385,
    "category": "UT",
    "number_of_recurrences": 12,
    "recurrence": "MO",
    "payment_date": "2022-4-20 23:59:59"
}


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

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="test77", email="test@gmail.com", password="test77test")
        Account.objects.create(owner=cls.user)

    def addItems(self):
        url = reverse('api:expenses-list')
        self.client.post(url, BASIC_EXPENSE_1, format='json')
        self.client.post(url, BASIC_EXPENSE_2, format='json')
        self.client.post(url, BASIC_EXPENSE_3, format='json')
        self.client.post(url, BASIC_EXPENSE_4, format='json')
        self.client.post(url, BASIC_EXPENSE_5, format='json')
        self.client.post(url, BASIC_EXPENSE_6, format='json')
        self.client.post(url, RECURRING_EXPENSE_1, format='json')
        self.client.post(url, RECURRING_EXPENSE_2, format='json')

    def authenticate(self):
        response = self.client.post(JWT_URL, {"username": self.user.username, "password": "test77test"})
        assert response.status_code == status.HTTP_200_OK
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + response.data['access'])

    def test_can_create_basic_expense(self):
        self.authenticate()
        url = reverse('api:expenses-list')
        response = self.client.post(url, BASIC_EXPENSE_1, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        self.assertEqual(Expense.objects.count(), 1)
        self.assertFalse(response.data['recurring'])
        self.assertFalse(response.data['number_of_recurrences'])
        self.assertEqual(self.user, Account.objects.get(pk=response.data['account']).owner)
        self.assertEqual(len(response.data['payments']), Payment.objects.count())

    def test_can_create_recurring_expense(self):
        self.authenticate()
        url = reverse('api:expenses-list')
        response = self.client.post(url, RECURRING_EXPENSE_1, format='json')
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
        self.client.post(url, BASIC_EXPENSE_1, format='json')
        self.client.post(url, RECURRING_EXPENSE_1, format='json')
        response = self.client.get(url, format='json')
        assert response.status_code == status.HTTP_200_OK
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(Payment.objects.count(), 5)

    @freeze_time("2022-04-25")
    def test_can_view_expenses_by_month_without_params(self):
        self.authenticate()
        self.addItems()
        url = reverse('api:expenses-expenses-by-month')
        response = self.client.get(url, format='json')
        assert response.status_code == status.HTTP_200_OK
        self.assertEqual(response.data['month'], 'April')
        self.assertEqual(len(response.data['expenses']), 6)
        self.assertEqual(response.data['total'], 2555)

    @freeze_time("2022-04-25")
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

    @freeze_time("2022-04-25")
    def test_can_view_expenses_by_month_with_month_and_year_params(self):
        self.authenticate()
        self.addItems()
        url = reverse('api:expenses-expenses-by-month')+'?month=3&year=2022'
        response = self.client.get(url, format='json')
        assert response.status_code == status.HTTP_200_OK
        self.assertEqual(response.data['month'], 'March')
        self.assertEqual(len(response.data['expenses']), 1)
        self.assertEqual(response.data['total'], 200)
        url = reverse('api:expenses-expenses-by-month')+'?month=6&year=2022'
        response = self.client.get(url, format='json')
        assert response.status_code == status.HTTP_200_OK
        self.assertEqual(response.data['month'], 'June')
        self.assertEqual(len(response.data['expenses']), 3)
        self.assertEqual(response.data['total'], 970)
        url = reverse('api:expenses-expenses-by-month')+'?month=5&year=2023'
        response = self.client.get(url, format='json')
        assert response.status_code == status.HTTP_200_OK
        self.assertEqual(response.data['month'], 'May')
        self.assertEqual(len(response.data['expenses']), 0)
        self.assertEqual(response.data['total'], 0)

    @freeze_time("2022-04-25")
    def test_view_expenses_by_month_with_invalid_params(self):
        self.authenticate()
        self.addItems()
        url = reverse('api:expenses-expenses-by-month')+'?month=d'
        response = self.client.get(url, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        url = reverse('api:expenses-expenses-by-month')+'?month=22'
        response = self.client.get(url, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        url = reverse('api:expenses-expenses-by-month')+'?month=2&year=dd'
        response = self.client.get(url, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        url = reverse('api:expenses-expenses-by-month')+'?month=2&year=22002'
        response = self.client.get(url, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @freeze_time("2022-04-25")
    def test_view_expenses_so_far_date_1(self):
        self.authenticate()
        self.addItems()
        url = reverse('api:expenses-expenses-so-far')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['month'], 'April')
        self.assertEqual(len(response.data['expenses']), 3)
        self.assertEqual(response.data['total'], 1785)

    @freeze_time("2022-04-30")
    def test_view_expenses_so_far_date_2(self):
        self.authenticate()
        self.addItems()
        url = reverse('api:expenses-expenses-so-far')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['month'], 'April')
        self.assertEqual(len(response.data['expenses']), 5)
        self.assertEqual(response.data['total'], 2355)

    @freeze_time("2022-04-15")
    def test_view_expenses_so_far_date_3(self):
        self.authenticate()
        self.addItems()
        url = reverse('api:expenses-expenses-so-far')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['month'], 'April')
        self.assertEqual(len(response.data['expenses']), 2)
        self.assertEqual(response.data['total'], 1400)


class PaymentViewSetTest(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="test77", email="test@gmail.com", password="test77test")
        Account.objects.create(owner=cls.user)

    def addItems(self):
        url = reverse('api:expenses-list')
        self.client.post(url, BASIC_EXPENSE_1, format='json')
        self.client.post(url, BASIC_EXPENSE_2, format='json')
        self.client.post(url, BASIC_EXPENSE_3, format='json')
        self.client.post(url, BASIC_EXPENSE_4, format='json')
        self.client.post(url, BASIC_EXPENSE_5, format='json')
        self.client.post(url, BASIC_EXPENSE_6, format='json')
        self.client.post(url, RECURRING_EXPENSE_1, format='json')
        self.client.post(url, RECURRING_EXPENSE_2, format='json')

    def authenticate(self):
        response = self.client.post(JWT_URL, {"username": self.user.username, "password": "test77test"})
        assert response.status_code == status.HTTP_200_OK
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + response.data['access'])

    @freeze_time("2022-04-25")
    def test_view_upcoming_payments(self):
        self.authenticate()
        self.addItems()
        url = reverse('api:payments-upcoming-payments')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print(response.data['count'])
        for data in response.data['results']:
            print(data)
        self.assertEqual(response.data['count'], 19)

    @freeze_time("2022-06-25")
    def test_view_upcoming_payments(self):
        self.authenticate()
        self.addItems()
        url = reverse('api:payments-upcoming-payments')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print(response.data['count'])
        for data in response.data['results']:
            print(data)
        self.assertEqual(response.data['count'], 11)

    @freeze_time("2022-04-15")
    def test_view_upcoming_payments(self):
        self.authenticate()
        self.addItems()
        url = reverse('api:payments-upcoming-payments')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
