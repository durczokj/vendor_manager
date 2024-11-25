import sys, os
print('Python %s on %s' % (sys.version, sys.platform))

import django
print('Django %s' % django.get_version())

sys.path.append('/Users/jakubdurczok/Library/CloudStorage/OneDrive-SGH/SGH/Praca Magisterska/vendor_manager')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vendor_manager.settings')
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
if 'setup' in dir(django):
    django.setup()

from django.db import models
from orders.models import Order, OrderVersion, Contract
from companies.models import Company
from undertakings.models import CostCenter, Undertaking
from engagements.models import Engagement, Assignment
from people.models import Person
from undertakings.models import Undertaking
from datetime import date
import random
from datetime import date

import random
from faker import Faker

CostCenter.objects.all().delete()
Undertaking.objects.all().delete()
Company.objects.all().delete()
Order.objects.all().delete()
Contract.objects.all().delete()
Person.objects.all().delete()
Engagement.objects.all().delete()
Assignment.objects.all().delete()
