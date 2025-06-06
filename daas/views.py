import sys
import datetime
from django.shortcuts import render
from django.http import HttpResponse
import psycopg2
from .common import get_dssdb_config

dssdb_config = get_dssdb_config()

def my_submissions(request):
    user = get_user(request)
    submissions = get_all_submissions(user)
    return render(request,'daas_my_submissions.html', {'submissions':submissions})

def user_submissions(request):
    user = get_user(request)
    submissions = get_submissions(user)
    return render(request,'daas_my_submissions.html', {'submissions':submissions})

def full_submission(request):
    _id = request.GET['id']
    user = get_user(request)
    submission_description = get_submission_description(_id)
    return render(request,'daas_full_submission.html', {'data' : submission_description})

def accept(request):
    _id = request.GET['id']
    return HttpResponse('{sucess:true}')

def reject(request):
    _id = request.GET['id']
    return HttpResponse('{sucess:true}')

def get_all_submissions(user):
    conn = psycopg2.connect(**dssdb_config)
    cursor = conn.cursor()
    cursor.execute("select logname from dssgrp where role='S' or role='M'")
    specialists =  cursor.fetchall()
    specialists = [a[0] for a in specialists]
    logname =  user.split('@ucar.edu')[0]
     
    if logname in specialists:
        query = 'select "DatasetID", "DatasetFullTitle", "DatasetStatus", "DateSubmitted", "DateResolved", "UserEmailAddress" from "dataset_AS"'
        cursor.execute(query)
        result = cursor.fetchall()
    else:
        result = get_submissions(user)
        
    #result = format_date_resolved(result)
    return result

def get_submissions(user_email):
    conn = psycopg2.connect(**dssdb_config)
    cursor = conn.cursor()

    query = 'select "DatasetID", "DatasetFullTitle","DatasetStatus","DateSubmitted","DateResolved","UserEmailAddress" from "dataset_AS" where "UserEmailAddress"=%s'
    cursor.execute(query, (user_email,))
    result = cursor.fetchall()

    #result = format_date_resolved(result)
    return result

def get_submission_description(_id):
    conn = psycopg2.connect(**dssdb_config)
    cursor = conn.cursor()
    query = 'select * from "dataset_AS" where "DatasetID"=%s'
    cursor.execute(query, (_id,))
    result = cursor.fetchone()
    return result
    
def format_date_resolved(result):
    date_resolved_idx = 4
    for submission in result:
        date = submission[date_resolved_idx]
        if date.year < 2015:
            submission[date_resolved_idx] = ""
    return result

def get_user(request):
    cookies = request.COOKIES
    if 'duser' in cookies:
        return cookies['duser']
    return ""
    
    sys.stderr.write(str(cookies))
    
