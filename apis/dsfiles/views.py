from django.shortcuts import render


def swagger(request, output=None):
    return render(request, "dsfiles/swagger.html", {})
