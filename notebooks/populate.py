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
from leaves.models import Leave
from datetime import date, timedelta
import random
from faker import Faker

fake = Faker()

# Delete all existing CostCenter objects
CostCenter.objects.all().delete()

# Create new CostCenter objects
cost_centers = []

cost_centers.append(CostCenter(id=1234, name='HR'))
cost_centers.append(CostCenter(id=9876, name='Finance'))

for cc in cost_centers:
    cc.save()

# Delete all existing Undertaking objects
Undertaking.objects.all().delete()

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


# Delete all existing Company objects
Company.objects.all().delete()

# Create new Company objects
companies = []

companies.append(Company(id=1, name='EY', email = "jan.kowalski@ey.com"))
companies.append(Company(id=2, name='Deloitte', email = "tomasz.nowak@deloitte.com"))
companies.append(Company(id=3, name='Atos', email = "anna.kaczmarska@atos.eu"))

for company in companies:
    company.save()

# Delete all existing Order objects
Order.objects.all().delete()

# Create new Order objects
orders = []
orders.append(Order(id=1, name='Support EY', company=Company.objects.get(id=1)))
orders.append(Order(id=2, name='Support Atos', company=Company.objects.get(id=3)))
orders.append(Order(id=3, name='Support Deloitte', company=Company.objects.get(id=2)))

# Create new OrderVersion objects for each Order
order_versions = []
start_date = date(2024, 7, 1)
end_date = date(2025, 6, 30)

i = 1
for order in orders:
    order.save()
    order_versions.append(OrderVersion(id = i, order=order, version_number=1, start_date=start_date, end_date=end_date))
    i += 1

for ov in order_versions:
    ov.save()

# Delete all existing Contract objects
Contract.objects.all().delete()

# Create new Contract objects for each OrderVersion
contracts = []
for ov in order_versions:
    contracts.append(Contract(id=1234, order_version = OrderVersion.objects.get(id=1), name = "HR Support EY Contract", status = "Active", size =  1000000))
    contracts.append(Contract(id=5678, order_version = OrderVersion.objects.get(id=2), name = "HR Support Atos Contract", status = "Active", size =  2000000))
    contracts.append(Contract(id=9876, order_version = OrderVersion.objects.get(id=3), name = "Finance Support Deloitte Contract", status = "Active", size =  3000000))
for contract in contracts:
    contract.save()


# Delete all existing Engagement, Person and Assignment objects
Person.objects.all().delete()
Engagement.objects.all().delete()
Assignment.objects.all().delete()

# Sample data for people
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
        order_version=OrderVersion.objects.get(id=random.randint(1, 3)),
        person=p,
        start_date=date(2024, 7, 1),
        end_date=date(2025, 6, 30),
        daily_rate=daily_rate,
        fte=1
    )
    engagements.append(e)
    e.save()

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
        while Assignment.objects.filter(engagement=e, undertaking_id=undertaking_id).exists():
            undertaking_id = random.randint(1, 6)
        if not Assignment.objects.filter(engagement=e, undertaking_id=undertaking_id).exists():
            a = Assignment(
                id=(i - 1) * 2 + j + 1,
                undertaking=Undertaking.objects.get(id=undertaking_id),
                engagement=e,
                percentage=percentage,
                start_date=date(2024, 7, 1),
                end_date=date(2025, 6, 30)
            )
            assignments.append(a)
            a.save()
            print(sum([ass.percentage for ass in a.engagement.assignments.all()]))

for person in people:
    person.save()
for engagement in engagements:
    engagement.save()
for assignment in assignments:
    assignment.save()

# Create new versions of two random orders
selected_orders = random.sample(orders, 2)
for order in selected_orders:
    current_version = order.versions.latest('version_number')
    new_version_number = current_version.version_number + 1

    # Delimit the current version
    current_version.end_date = date(2024, 10, 31)
    current_version.save()

    # Create new OrderVersion
    new_order_version = OrderVersion(
        order=order,
        version_number=new_version_number,
        start_date=date(2024, 11, 1),
        end_date=date(2025, 6, 30)
    )
    new_order_version.save()

    # Create new Contract for the new OrderVersion
    new_contract = Contract(
        order_version=new_order_version,
        name=f"{order.name} Contract Version {new_version_number}",
        status="Active",
        size=random.randint(1000000, 3000000)
    )
    new_contract.save()

    # Copy engagements from current version to new version
    current_engagements = current_version.engagements.all()
    if current_engagements.exists():
        # Remove one engagement
        engagement_to_remove = random.choice(current_engagements)
        current_engagements = current_engagements.exclude(id=engagement_to_remove.id)

        # Add one new engagement
        existing_people_ids = current_engagements.values_list('person_id', flat=True)
        available_people = [person for person in people if person.id not in existing_people_ids]

        if available_people:
            new_engagement = Engagement(
                id=current_engagements.latest('id').id + 1000,
                order_version=new_order_version,
                person=random.choice(available_people),
                start_date=date(2024, 11, 1),
                end_date=date(2025, 6, 30),
                daily_rate=max(0, round(random.gauss(1000, 300))),
                fte=1
            )
            new_engagement.save()

            assignment = Assignment(
                undertaking=random.choice(undertakings),
                engagement=new_engagement,
                percentage=1.0,
                start_date=date(2024, 11, 1),
                end_date=date(2025, 6, 30)
            )
            assignment.save()

        for engagement in current_engagements:
            old_assignments = [a for a in engagement.assignments.all()]
            engagement.id = engagement.id + 100
            engagement.order_version = new_order_version
            engagement.start_date = date(2024, 11, 1)
            engagement.end_date = date(2025, 6, 30)
            engagement.save()

            # Copy assignments
            for assignment in old_assignments:
                assignment.pk = None  # Reset primary key to create a new record
                assignment.engagement = Engagement.objects.get(id=engagement.id)
                assignment.start_date = date(2024, 11, 1)
                assignment.end_date = date(2025, 6, 30)
                assignment.save()

Leave.objects.all().delete()
leaves = []
leaves.append(Leave(person = Person.objects.all()[0], start_date = date(2024, 1, 1), end_date = date(2024, 1, 1), percentage = 1))
leaves.append(Leave(person = Person.objects.all()[3], start_date = date(2024, 4, 1), end_date = date(2024, 4, 1), percentage = 1))
leaves.append(Leave(person = Person.objects.all()[5], start_date = date(2024, 5, 1), end_date = date(2024, 5, 1), percentage = 1))
for l in leaves:
    l.save()
