from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import models
from datetime import datetime, timedelta
from calendar import monthrange


# Create your models here.


class Account(models.Model):
    owner = models.OneToOneField(User, on_delete=models.CASCADE)
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    @property
    def this_month_expense_average(self):
        today = datetime.today()
        days = timedelta(days=today.day)
        filters = {'payment_date__month': today.month, 'payment_date__year': today.year}
        expenses = self.expenses.filter(**filters)
        expense_sum = 0
        for expense in expenses:
            expense_sum += expense.amount
        return expense_sum / days.days

    def monthly_expense_average(self, date):
        filters = {'payment_date__month': date.month, 'payment_date__year': date.year}
        expenses = self.expenses.filter(**filters)
        days_range = monthrange(date.year, date.month)
        average = expenses / days_range[1]
        return average


class Recurrence(models.TextChoices):
    DAILY = 'DA', _('Daily')
    WEEKLY = 'WE', _('Weekly')
    BIWEEKLY = 'BW', _('Biweekly')
    MONTHLY = 'MO', _('Monthly')
    YEARLY = 'YE', _('Yearly')
    ONCE = 'ON', _('Once')


class Income(models.Model):
    name = models.CharField(max_length=255)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    amount = models.FloatField()
    number_of_recurrences = models.SmallIntegerField(default=0)
    recurrence = models.CharField(
        max_length=2,
        choices=Recurrence.choices,
        default=Recurrence.ONCE,
    )

    @property
    def recurring(self):
        return bool(self.number_of_recurrences)

    def __str__(self):
        return self.name


class Expense(models.Model):

    class Category(models.TextChoices):
        HOUSING = 'HO', _('Housing')
        TRANSPORTATION = 'TR', _('Transportation')
        FOOD = 'FO', _('Food')
        UTILITIES = 'UT', _('Utilities')
        INSURANCE = 'IN', _('Insurance')
        MEDICAL = 'ME', _('Medical & Healthcare')
        SAVINGS = 'SA', _('Savings, Investing & Debt Payments')
        PERSONAL = 'PE', _('Personal Spending')
        ENTERTAINMENT = 'EN', _('Recreation and Entertainment')
        MISCELLANEOUS = 'MI', _('Miscellaneous')
        UNCATEGORIZED = 'UN', _('Uncategorized')

    name = models.CharField(max_length=255)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='expenses', blank=True)
    amount = models.FloatField()
    category = models.CharField(
        max_length=2,
        choices=Category.choices,
        default=Category.UNCATEGORIZED,
    )
    number_of_recurrences = models.SmallIntegerField(default=0)
    recurrence = models.CharField(
        max_length=2,
        choices=Recurrence.choices,
        default=Recurrence.ONCE,
    )
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    @property
    def recurring(self):
        return bool(self.number_of_recurrences)

    @property
    def recurrence_until_cancelled(self):
        if self.number_of_recurrences < 0:
            return True
        return False

    @property
    def payment_date(self):
        return self.payments.first()

    def __str__(self):
        return f"{self.name}: {self.amount} | {self.category}"

    class Meta:
        ordering = ['-date_created']


class Payment(models.Model):
    date = models.DateTimeField(default=timezone.now)
    expense = models.ForeignKey(Expense, on_delete=models.CASCADE, related_name='payments')

    def __str__(self):
        return f"{self.date.date()} | {self.expense.name}"

    class Meta:
        ordering = ['-date']


class AmountModifier(models.Model):

    class Modifier(models.TextChoices):
        PERCENT_INCREASE = 'PI', _('Add Percentage')
        PERCENT_DECREASE = 'PD', _('Reduce Percentage')
        PERCENT_NONE = 'PN', _('No Change')

    name = models.CharField(max_length=255)
    percent_modifier = models.CharField(
        max_length=2,
        choices=Modifier.choices,
        default=Modifier.PERCENT_NONE,
    )
    percent = models.FloatField()
    income = models.ForeignKey(Income, on_delete=models.CASCADE, related_name="modifier")
    expense = models.ForeignKey(Expense, on_delete=models.CASCADE, related_name="modifier")

    @property
    def value(self):
        if self.income is not None:
            return self.percent_formula(self.income.amount)
        if self.expense is not None:
            return self.percent_formula(self.expense.amount)

    def __str__(self):
        return self.name

    def percent_formula(self, amount):
        if self.percent_modifier == self.Modifier.PERCENT_NONE:
            return amount
        if self.percent_modifier == self.Modifier.PERCENT_INCREASE:
            return amount * (1 + self.percent)
        if self.percent_modifier == self.Modifier.PERCENT_DECREASE:
            return amount * self.percent

    def clean(self):
        if self.income is None and self.expense is None:
            raise ValidationError(_('Either income or expense must be specified.'))
        if self.income is not None and self.expense is not None:
            raise ValidationError(_("Modifier can't have both income and expense attribute."))
