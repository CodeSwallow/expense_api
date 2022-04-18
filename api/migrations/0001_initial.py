# Generated by Django 4.0.3 on 2022-04-09 18:13

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Account',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_modified', models.DateTimeField(auto_now=True)),
                ('owner', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Income',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('amount', models.FloatField()),
                ('number_of_recurrences', models.SmallIntegerField(default=0)),
                ('recurrence', models.CharField(choices=[('DA', 'Daily'), ('WE', 'Weekly'), ('BW', 'Biweekly'), ('MO', 'Monthly'), ('YE', 'Yearly'), ('ON', 'Once')], default='ON', max_length=2)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.account')),
            ],
        ),
        migrations.CreateModel(
            name='Expense',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('amount', models.FloatField()),
                ('category', models.CharField(choices=[('HO', 'Housing'), ('TR', 'Transportation'), ('FO', 'Food'), ('UT', 'Utilities'), ('IN', 'Insurance'), ('ME', 'Medical & Healthcare'), ('SA', 'Savings, Investing & Debt Payments'), ('PE', 'Personal Spending'), ('EN', 'Recreation and Entertainment'), ('MI', 'Miscellaneous'), ('UN', 'Uncategorized')], default='UN', max_length=2)),
                ('payment_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('number_of_recurrences', models.SmallIntegerField(default=0)),
                ('recurrence', models.CharField(choices=[('DA', 'Daily'), ('WE', 'Weekly'), ('BW', 'Biweekly'), ('MO', 'Monthly'), ('YE', 'Yearly'), ('ON', 'Once')], default='ON', max_length=2)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_modified', models.DateTimeField(auto_now=True)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='expenses', to='api.account')),
            ],
        ),
        migrations.CreateModel(
            name='AmountModifier',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('percent_modifier', models.CharField(choices=[('PI', 'Add Percentage'), ('PD', 'Reduce Percentage'), ('PN', 'No Change')], default='PN', max_length=2)),
                ('percent', models.FloatField()),
                ('expense', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='modifier', to='api.expense')),
                ('income', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='modifier', to='api.income')),
            ],
        ),
    ]
