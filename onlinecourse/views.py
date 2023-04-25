from django.shortcuts import render
from django.http import HttpResponseRedirect
# <HINT> Import any new Models here
from .models import Course, Enrollment, Submission, Question
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views import generic
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth import get_user
import logging
# Get an instance of a logger
logger = logging.getLogger(__name__)
# Create your views here.


def registration_request(request):
    context = {}
    if request.method == 'GET':
        return render(request, 'onlinecourse/user_registration_bootstrap.html', context)
    elif request.method == 'POST':
        # Check if user exists
        username = request.POST['username']
        password = request.POST['psw']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        user_exist = False
        try:
            User.objects.get(username=username)
            user_exist = True
        except:
            logger.error("New user")
        if not user_exist:
            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name,
                                            password=password)
            login(request, user)
            return redirect("onlinecourse:index")
        else:
            context['message'] = "User already exists."
            return render(request, 'onlinecourse/user_registration_bootstrap.html', context)


def login_request(request):
    context = {}
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['psw']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('onlinecourse:index')
        else:
            context['message'] = "Invalid username or password."
            return render(request, 'onlinecourse/user_login_bootstrap.html', context)
    else:
        return render(request, 'onlinecourse/user_login_bootstrap.html', context)


def logout_request(request):
    logout(request)
    return redirect('onlinecourse:index')


def check_if_enrolled(user, course):
    is_enrolled = False
    if user.id is not None:
        # Check if user enrolled
        num_results = Enrollment.objects.filter(user=user, course=course).count()
        if num_results > 0:
            is_enrolled = True
    return is_enrolled



# CourseListView
class CourseListView(generic.ListView):
    template_name = 'onlinecourse/course_list_bootstrap.html'
    context_object_name = 'course_list'

    def get_queryset(self):
        user = self.request.user
        courses = Course.objects.order_by('-total_enrollment')[:10]
        for course in courses:
            if user.is_authenticated:
                course.is_enrolled = check_if_enrolled(user, course)
        return courses


class CourseDetailView(generic.DetailView):
    model = Course
    template_name = 'onlinecourse/course_detail_bootstrap.html'
    

def enroll(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    user = request.user

    is_enrolled = check_if_enrolled(user, course)
    if not is_enrolled and user.is_authenticated:
        # Create an enrollment
        Enrollment.objects.create(user=user, course=course, mode='honor')
        course.total_enrollment += 1
        course.save()

    return HttpResponseRedirect(reverse(viewname='onlinecourse:course_details', args=(course.id,)))


def submitexam(request, course_id):
    enroll_obj = Enrollment.objects.get(user=request.user, course = course_id)
    submission_obj = Submission.objects.create(enrollment_id = enroll_obj.id)
    ids = list(request.POST.values())[1:]
    for id in ids:
        submission_obj.choices.add(id)
    submission_obj.save()
    print(submission_obj.id)
    return HttpResponseRedirect(reverse(viewname='onlinecourse:exam_result', args=(course_id, submission_obj.id,)))


def show_exam_result(request, course_id, submission_id):
    context = {}
    submission_obj = Submission.objects.get(pk=submission_id)
    total_questions = Question.objects.filter(course = Course.objects.get(pk=course_id))
    total_marks = 0.0
    obt_marks = 0.0
    for quest in total_questions:
        total_marks += quest.grade_points
        if quest.is_get_score(submission_obj.choices.filter(question = quest)):
            obt_marks+=quest.grade_points
    context['course'] = Course.objects.get(pk=course_id)
    context['grade'] = int(obt_marks/total_marks*100)
    context['min'] = 80
    context['questions'] = total_questions
    context['selected'] = submission_obj.choices.all()
    #print(f"Total: {total_marks*100}, Obtained: {context['grade']}")
    return render(request, 'onlinecourse/exam_result_bootstrap.html', context)




