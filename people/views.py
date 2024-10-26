from django.http import HttpResponse
from django.template import loader
from .models import Person

# def people(request):
#   template = loader.get_template('myfirst.html')
#   return HttpResponse(template.render())

def people(request):
  mypeople = Person.objects.all().values()
  template = loader.get_template('all_people.html')
  context = {
    'mypeople': mypeople,
  }
  return HttpResponse(template.render(context, request))
  
def details(request, id):
  myperson = Person.objects.get(id=id)
  template = loader.get_template('details.html')
  context = {
    'myperson': myperson,
  }
  return HttpResponse(template.render(context, request))

def main(request):
  template = loader.get_template('main.html')
  return HttpResponse(template.render())