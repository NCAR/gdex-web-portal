from django.shortcuts import render


def resolve(request, doi):
    return render(request, "400.html")


