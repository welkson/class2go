from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response
from django.template import Context, loader
from django.template import RequestContext
from c2g.models import Course, Announcement, NewsEvent
from courses.common_page_data import get_common_page_data
import re

def main(request, course_prefix, course_suffix):
    try:
        common_page_data = get_common_page_data(request, course_prefix, course_suffix)
    except:
        raise Http404

    announcement_list = common_page_data['course'].announcement_set.all().order_by('-time_created')
    news_list = common_page_data['production_course'].newsevent_set.all().order_by('-time_created')[0:5]
    return render_to_response('courses/view.html',
            {'common_page_data': common_page_data,
             'announcement_list': announcement_list,
             'news_list': news_list,
             },
            context_instance=RequestContext(request))

def overview(request, course_prefix, course_suffix):
    try:
        common_page_data = get_common_page_data(request, course_prefix, course_suffix)
    except:
        raise Http404

    if request.method == 'POST':
        if request.POST.get("revert") == '1':
            common_page_data['staging_course'].description = common_page_data['production_course'].description
            common_page_data['staging_course'].save()
        else:
            common_page_data['staging_course'].description = request.POST.get("description")
            common_page_data['staging_course'].save()
            if request.POST.get("commit") == '1':
                common_page_data['production_course'].description = common_page_data['staging_course'].description
                common_page_data['production_course'].save()

    return render_to_response('courses/overview.html',
            {'common_page_data': common_page_data},
            context_instance=RequestContext(request))

def syllabus(request, course_prefix, course_suffix):
    try:
        common_page_data = get_common_page_data(request, course_prefix, course_suffix)
    except:
        raise Http404

    if request.method == 'POST':
        if request.POST.get("revert") == '1':
            common_page_data['staging_course'].syllabus = common_page_data['production_course'].syllabus
            common_page_data['staging_course'].save()
        else:
            common_page_data['staging_course'].syllabus = request.POST.get("syllabus")
            common_page_data['staging_course'].save()
            if request.POST.get("commit") == '1':
                common_page_data['production_course'].syllabus = common_page_data['staging_course'].syllabus
                common_page_data['production_course'].save()

    return render_to_response('courses/syllabus.html',
            {'common_page_data': common_page_data},
            context_instance=RequestContext(request))

def course_materials(request, course_prefix, course_suffix):
    try:
        common_page_data = get_common_page_data(request, course_prefix, course_suffix)
    except:
        raise Http404
    
    section_structures = []
    if request.user.is_authenticated():
        sections = common_page_data['course'].contentsection_set.all().order_by('index')
        videos = Video.objects.filter(course=common_page_data['course']).order_by('section', 'index')
        problem_sets = ProblemSet.objects.filter(course=common_page_data['course']).order_by('section', 'index')
        video_recs = request.user.videoactivity_set.filter(course=common_page_data['course'])
        
        index = 0
        for section in sections:
            section_dict = {'section':section, 'items':[]}
            
            secion_videos = []
            secion_problem_sets = []
            for video in videos:
                if video.section_id == section.id:
                    item = {'type':'video', 'video':video}
                    for video_rec in video_recs:
                        if video_rec.video_id == video.id:
                            item['video_rec'] = video_rec
                            break
                    section_dict['items'].append(item)
                    
            for problem_set in problem_sets:
                if problem_set.section_id == section.id:
                    item = {'type':'problem_set', 'problem_set':problem_set}
                    
                    exercises = problem_set.exercise_set.all()
                    numQuestions = len(exercises)
                    #Starting values are total questions and will be subtracted from
                    numCompleted = numQuestions
                    numCorrect = numQuestions
                    for exercise in exercises:
                        attempts = exercise.problemactivity_set.filter(student = request.user).exclude(attempt_content="hint")

                        #Counts the completed problems by subtracting all without a student activity recorded for it
                        if len(attempts) == 0:
                            numCompleted -= 1

                        #Add one to the number of correctly answered questions if the first attempt is correct
                        attempts.filter(attempt_number = 1)
                        for attempt in attempts:
                            if attempt.complete == 0:
                                numCorrect -= 1
                                break

                    #Divide by zero safety check
                    if numQuestions == 0:
                        progress = 0
                    else:
                        progress = 100.0*numCompleted/numQuestions
                    
                    item['numQuestions'] = numQuestions
                    item['numCompleted'] = numCompleted
                    item['numCorrect'] = numCorrect
                    item['progress'] = progress

                    section_dict['items'].append(item)
            
            for video in videos:
                if video.section_id == section.id and (common_page_data['course_mode'] == 'staging' or (video.live_datetime and common_page_data['current_datetime'] > video.live_datetime)):
                    current_video_rec = None
                    for video_rec in video_recs:
                        if video_rec.video_id == video.id:
                            current_video_rec = video_rec
                            break
                    live_status = ''
                    if common_page_data['course_mode'] == 'staging':
                        prod_video = video.image
                        if not prod_video.live_datetime:
                            live_status = "<span style='color:red;'>Not live</span>"
                        else:
                            if prod_video.live_datetime > datetime.datetime.now():
                                year = prod_video.live_datetime.year
                                month = prod_video.live_datetime.month
                                day = prod_video.live_datetime.day
                                hour = prod_video.live_datetime.hour
                                minute = prod_video.live_datetime.minute
                                live_status = "<span style='color:red;'>Goes live on %02d-%02d-%04d at %02d:%02d</span>" % (month,day,year,hour,minute)
                            else:
                                live_status = "<span style='color:green;'>Live</span>"
                                
                    section_dict['video_video_recs'].append({'video':video, 'video_rec':current_video_rec, 'live_status':live_status})
            
            if common_page_data['course_mode'] == 'staging' or len(section_dict['items']) > 0:
                section_structures.append(section_dict)
                index += 1
                
    if common_page_data['course_mode'] == 'staging':
        return render_to_response('courses/staging/course_materials.html', {'common_page_data': common_page_data, 'section_structures':section_structures}, context_instance=RequestContext(request))
    else:
        return render_to_response('courses/production/course_materials.html', {'common_page_data': common_page_data, 'section_structures':section_structures}, context_instance=RequestContext(request))
