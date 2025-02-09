import sys
import os
import django
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vendor_manager.settings')
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
if 'setup' in dir(django):
    django.setup()

from django.db import models
from orders.models import Order, OrderVersion
from contracts.models import Contract
from companies.models import Company
from undertakings.models import CostCenter, Undertaking
from engagements.models import Engagement, EngagementUndertakingAssignment, EngagementOrderVersionAssignment
from people.models import Person
from undertakings.models import Undertaking
from leaves.models import Leave
from datetime import date, timedelta
import random
from faker import Faker

fake = Faker()

# Delete all existing objects
EngagementOrderVersionAssignment.objects.all().delete()
EngagementUndertakingAssignment.objects.all().delete()
Engagement.objects.all().delete()
Undertaking.objects.all().delete()
CostCenter.objects.all().delete()
Leave.objects.all().delete()
Person.objects.all().delete()
OrderVersion.objects.all().delete()
Order.objects.all().delete()
Contract.objects.all().delete()
Company.objects.all().delete()

# Create new CostCenter objects
cost_centers = []

cost_centers.append(CostCenter(id=1234, name='HR'))
cost_centers.append(CostCenter(id=9876, name='Finance'))

for cc in cost_centers:
    cc.save()

# Create new Undertaking objects and assign CostCenter
undertakings = []

undertakings.append(Undertaking(id=1, name='HR Payroll', cost_center=CostCenter.objects.get(id=1234)))
undertakings.append(Undertaking(id=2, name='HR ESS Portal', cost_center=CostCenter.objects.get(id=1234)))
undertakings.append(Undertaking(id=3, name='HR ESS Time Management', cost_center=CostCenter.objects.get(id=1234)))

undertakings.append(Undertaking(id=4, name='Finance Reporting', cost_center=CostCenter.objects.get(id=9876)))
undertakings.append(Undertaking(id=5, name='SAP Finance Support', cost_center=CostCenter.objects.get(id=9876)))
undertakings.append(Undertaking(id=6, name='Accounting', cost_center=CostCenter.objects.get(id=9876)))

for undertaking in undertakings:
    undertaking.save()

# Create new Company objects
companies = []

companies.append(Company(id=1, name='EY', email = "contracting@ey.com"))
companies.append(Company(id=2, name='Deloitte', email = "contracting@deloitte.com"))
companies.append(Company(id=3, name='Atos', email = "contracting@atos.eu"))

for company in companies:
    company.save()

# Create new Order objects
orders = []

orders.append(Order(id=1, name='Support EY', company=Company.objects.get(id=1)))
orders.append(Order(id=2, name='Support Atos', company=Company.objects.get(id=3)))
orders.append(Order(id=3, name='Support Deloitte', company=Company.objects.get(id=2)))

for order in orders:
    order.save()

# Create new Contract objects for each Order
contracts = []
contracts.append(Contract(id=1234, name = "HR Support EY Contract", status = "Active", size =  1000000))
contracts.append(Contract(id=5678, name = "HR Support Atos Contract", status = "Active", size =  2000000))
contracts.append(Contract(id=9876, name = "Finance Support Deloitte Contract", status = "Active", size =  3000000))

for contract in contracts:
    contract.save()

# Create new OrderVersion objects for each contract
order_versions = []
order_versions.append(OrderVersion(order=Order.objects.get(id=1), contract=Contract.objects.get(id=1234), version_number=1, start_date=date(2024, 1, 1), end_date=date(2024, 12, 31)))
order_versions.append(OrderVersion(order=Order.objects.get(id=2), contract=Contract.objects.get(id=5678), version_number=1, start_date=date(2024, 1, 1), end_date=date(2024, 12, 31)))
order_versions.append(OrderVersion(order=Order.objects.get(id=3), contract=Contract.objects.get(id=9876), version_number=1, start_date=date(2024, 1, 1), end_date=date(2024, 12, 31)))

for ov in order_versions:
    ov.save()

# Create new Person, Engagement EngagementOrderVersionAssignment and EngagementUndertakingAssignment objects
first_names = ['John', 'Jane', 'Alice', 'Bob', 'Charlie', 'David', 'Eve', 'Frank', 'Grace', 'Helen']
last_names = ['Smith', 'Doe', 'Johnson', 'Williams', 'Brown', 'Davis', 'Miller', 'Wilson', 'Moore', 'Taylor', 'Anderson', 'Thomas', 'Jackson']
locations = ['USA', 'Poland', 'UK', 'Germany', 'Australia']

people = []
engagements = []
assignments = []

for i in range(1, 31):

    # Create Person
    p = Person(
        id=f"{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}{random.randint(1000, 9999)}",
        first_name=random.choice(first_names),
        last_name=random.choice(last_names),
        description="Consultant",
        location=random.choice(locations)
    )
    people.append(p)
    p.save()

    # Create Engagement
    daily_rate = max(0, round(random.gauss(1000, 300)))  # Ensure daily rate is never negative
    e = Engagement(
        id=i,
        person=p,
        start_date=date(2024, 7, 1),
        end_date=date(2025, 6, 30),
        daily_rate=daily_rate,
        fte=1
    )
    engagements.append(e)
    e.save()

    # Assign the engagement to a random Order
    order_id = random.randint(1, 3)
    a = EngagementOrderVersionAssignment(
        engagement=e,
        order_version=OrderVersion.objects.filter(order_id = order_id, version_number = 1).first()
    )
    a.save()

    # Create Assignments
    num_assignments = random.randint(1, 2)
    assignment_percentage = 1.0
    for j in range(num_assignments):
        if j == num_assignments - 1:
            percentage = round(assignment_percentage, 1)
        else:
            percentage = round(random.uniform(0.3, 0.7), 1)
        assignment_percentage -= percentage

        undertaking_id = random.randint(1, 6)
        while EngagementUndertakingAssignment.objects.filter(engagement=e, undertaking_id=undertaking_id).exists():
            undertaking_id = random.randint(1, 6)
        a = EngagementUndertakingAssignment(
            undertaking=Undertaking.objects.get(id=undertaking_id),
            engagement=e,
            percentage=percentage,
            start_date=date(2024, 7, 1),
            end_date=date(2025, 6, 30))
        assignments.append(a)
        a.save()

# Create leaves
leaves = []
leaves.append(Leave(person = Person.objects.all()[0], start_date = date(2024, 1, 1), end_date = date(2024, 1, 1), percentage = 1))
leaves.append(Leave(person = Person.objects.all()[3], start_date = date(2024, 4, 1), end_date = date(2024, 4, 1), percentage = 1))
leaves.append(Leave(person = Person.objects.all()[5], start_date = date(2024, 5, 1), end_date = date(2024, 5, 1), percentage = 1))
for l in leaves:
    l.save()

# # Create new versions of two random orders
selected_orders = random.sample(orders, 2)
for order in selected_orders:
    contract = Contract(
        id = random.randint(10000, 20000),
        name = f"CR1 to {order.name}",
        status = "Active",
        size = random.randint(1000000, 3000000))

    order.create_new_version(
        contract=contract,
        start_date=date(2025, 2, 1),
        end_date=date(2025, 6, 30))

    ov = order.versions.filter(version_number = 2).first()
    random.choice(ov.engagement_assignments.all()).delete()

    p = Person(
        id=f"{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}{random.randint(1000, 9999)}",
        first_name=random.choice(first_names),
        last_name=random.choice(last_names),
        description="Consultant",
        location=random.choice(locations)
    )
    p.save()

    e = Engagement(
        person=p,
        start_date=date(2025, 2, 1),
        end_date=date(2025, 6, 30),
        daily_rate=max(0, round(random.gauss(1000, 300))),
        fte=1
    )
    e.save()

    a = EngagementOrderVersionAssignment(
        engagement=e,
        order_version=ov
    )
    a.save()
