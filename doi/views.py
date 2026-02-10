from django.shortcuts import render


def dereference(request, doi):
    return render(request, "400.html")


