from django.shortcuts import render


def docks(request):
    return render(request, 'redoc.html',
                  context={'schema_url': '/static/openapi-schema.yml'})
