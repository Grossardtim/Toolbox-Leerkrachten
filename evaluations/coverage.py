"""Subgoal exposure matrix, with the same visibility checks as lesson pages."""
from io import BytesIO
from collections import defaultdict
from django import forms
from django.http import HttpResponse
from django.shortcuts import render
from django.core.exceptions import PermissionDenied
from django.views.decorators.cache import never_cache
from accounts.access import visible_records
from .models import Year, StudyDirection, Classroom, Goal, Student, Lesson, Score, STAGES, stage_for_grade
from .views import teacher_required, log
import xlsxwriter

SCORE_COLORS = {0:'#B91C3D',20:'#EF4444',40:'#FBBF24',60:'#48CA75',80:'#0879EF'}

class CoverageForm(forms.Form):
    year = forms.ModelChoiceField(label='Schooljaar',queryset=Year.objects.none(),required=False,empty_label='Alle schooljaren')
    direction = forms.ModelChoiceField(label='Studierichting',queryset=StudyDirection.objects.none(),required=False,empty_label='Alle studierichtingen')
    classroom = forms.ModelChoiceField(label='Klas',queryset=Classroom.objects.none(),required=False,empty_label='Alle klassen')
    stage = forms.TypedChoiceField(label='Graad',choices=[('','Alle graden'),*STAGES],coerce=int,empty_value=None,required=False)
    def __init__(self,*args,user,**kwargs):
        super().__init__(*args,**kwargs)
        for key,model in [('year',Year),('direction',StudyDirection),('classroom',Classroom)]:
            self.fields[key].queryset = visible_records(model,user)
        self.fields['classroom'].label_from_instance = lambda c:f'{c.direction_name} · {c.name} · {c.year.name}'

def build_coverage(user, filters):
    classes = visible_records(Classroom,user).select_related('year','study_direction')
    if filters.get('year'): classes=classes.filter(year=filters['year'])
    if filters.get('direction'): classes=classes.filter(study_direction=filters['direction'])
    if filters.get('classroom'): classes=classes.filter(pk=filters['classroom'].pk)
    if filters.get('stage'):
        grades={1:[1,2],2:[3,4],3:[5,6,7]}[filters['stage']]
        classes=classes.filter(grade__in=grades)
    classes=list(classes)
    pupils=list(Student.objects.filter(classroom__in=classes).select_related('classroom__study_direction').order_by('classroom__study_direction__name','classroom__name','name','pk'))
    learners=[{'key':p.pk,'name':p.name,'class':p.classroom.name,'class_id':p.classroom_id} for p in pupils]
    class_scope={(c.study_direction_id,stage_for_grade(c.grade)) for c in classes}
    goals=visible_records(Goal,user).filter(study_direction_id__in=[c.study_direction_id for c in classes]).select_related('owner','study_direction').prefetch_related('points').order_by('study_direction__name','stage','code','pk')
    rows={}
    requirements={}
    for goal in goals:
        if (goal.study_direction_id,goal.stage) not in class_scope: continue
        points=list(goal.points.all())
        requirements[goal.pk]=[]
        for point in points or [None]:
            key=(goal.pk,point.pk if point else 'direct')
            requirements[goal.pk].append(key)
            rows[key]={'code':goal.code,'title':goal.title,'point':point.title if point else goal.title,
                       'goal_id':goal.pk,'kind':'subgoal' if point else 'direct',
                       'teacher':goal.owner.get_full_name() or goal.owner.username,
                       'direction':str(goal.study_direction),'stage':goal.stage,'values':defaultdict(list)}
    lessons=visible_records(Lesson,user).filter(classroom__in=classes)
    scores=Score.objects.filter(point__goal__lesson__in=lessons,status='scored',value__isnull=False).select_related(
        'point__goal__lesson__owner','point__goal__lesson__classroom__study_direction','learner')
    learner_keys={p['key'] for p in learners}
    for score in scores:
        goal=score.point.goal
        lesson=goal.lesson
        key=(goal.source_id or f'historic:{goal.pk}', 'direct' if score.point.is_direct else score.point.source_point_id or f'historic:{score.point_id}')
        row=rows.setdefault(key,{'code':goal.code,'title':goal.title,'point':score.point.title+' (leshistoriek)',
            'goal_id':goal.source_id,'kind':'historic','teacher':lesson.owner.get_full_name() or lesson.owner.username,
            'direction':lesson.classroom.direction_name,'stage':stage_for_grade(lesson.grade),'values':defaultdict(list)})
        learner_key=score.learner.student_id or f'historic:{score.learner_id}'
        if learner_key not in learner_keys:
            learners.append({'key':learner_key,'name':score.learner.name,'class':lesson.classroom.name,'class_id':lesson.classroom_id})
            learner_keys.add(learner_key)
        row['values'][learner_key].append(score.value)
    summaries={}
    for goal_id, keys in requirements.items():
        if len(keys)==1 and keys[0][1]=='direct': continue
        first=rows[keys[0]]
        summary={**first,'kind':'bk','point':first['title'],'cells':[]}
        for learner in learners:
            sets=[rows[key]['values'].get(learner['key'],[]) for key in keys]
            covered=sum(bool(values) for values in sets)
            values=[value for subset in sets for value in subset]
            average=sum(values)/len(values) if values else None
            category=min(80,int(average//20)*20) if average is not None else None
            summary['cells'].append({'seen':covered==len(keys),'covered':covered,'required':len(keys),
                'average':average,'category':category,'color':SCORE_COLORS.get(category,'#f0f2f6'),'count':len(values)})
        summary.pop('values',None)
        summaries[goal_id]=summary
    result=[]
    for row in rows.values():
        row['cells']=[]
        for learner in learners:
            values=row['values'].get(learner['key'],[])
            average=sum(values)/len(values) if values else None
            category=min(80,int(average//20)*20) if average is not None else None
            row['cells'].append({'seen':bool(values),'average':average,'category':category,
                'color':SCORE_COLORS.get(category,'#f0f2f6'),'count':len(values)})
        del row['values']
        if row['goal_id'] in summaries:
            result.append(summaries.pop(row['goal_id']))
        result.append(row)
    return learners,result

def coverage_workbook(learners,rows):
    stream=BytesIO()
    book=xlsxwriter.Workbook(stream,{'in_memory':True,'strings_to_formulas':False,'strings_to_urls':False})
    sheet=book.add_worksheet('BK en subdoelen')
    head=book.add_format({'bold':True,'bg_color':'#85175e','font_color':'white','text_wrap':True})
    text=book.add_format({'text_wrap':True,'valign':'vcenter'})
    sheet.merge_range(0,0,0,max(4,len(learners)+4),'Leerkrachten Tool · BK- en subdoelenoverzicht',head)
    sheet.merge_range(1,0,1,max(4,len(learners)+4),'BK ✓ = alle subdoelen beoordeeld; zonder subdoelen de BK zelf. 0 telt mee. Kleur = gemiddelde op 80, geen slaaggrens.',text)
    sheet.set_row(1,38)
    columns=['Studierichting / graad','Code','Leerplandoel','Subdoel','Leerkracht']+[p['name']+' · '+p['class'] for p in learners]
    for c,label in enumerate(columns): sheet.write(3,c,label,head)
    sheet.set_row(3,60)
    sheet.set_column(0,0,24);sheet.set_column(1,1,14);sheet.set_column(2,3,42);sheet.set_column(4,4,22)
    if learners: sheet.set_column(5,len(columns)-1,20)
    formats={None:book.add_format({'align':'center','bg_color':'#f0f2f6'})}
    for value,color in SCORE_COLORS.items():
        formats[value]=book.add_format({'align':'center','bg_color':color,'font_color':'white' if value in (0,80) else '#111111'})
    for r,row in enumerate(rows,4):
        for c,value in enumerate([f"{row['direction']} · {row['stage']}e graad",row['code'],row['title'],row['point'],row['teacher']]):
            sheet.write(r,c,value,text)
        for c,cell in enumerate(row['cells'],5):
            value=('✓' if cell['seen'] else '✗')
            if row['kind']=='bk': value+=f" {cell['covered']}/{cell['required']} subdoelen"
            elif cell['seen']: value+=' '+format(cell['average'],'.1f')
            sheet.write(r,c,value,formats[cell['category']])
        sheet.set_row(r,max(32,15*(1+max(len(row['point']),len(row['title']))//45)))
    sheet.freeze_panes(4,5)
    sheet.autofilter(3,0,max(3,len(rows)+3),len(columns)-1)
    book.close()
    return stream.getvalue()

@never_cache
@teacher_required
def coverage(request):
    form=CoverageForm(request.GET or None,user=request.user)
    learners,rows=[],[]
    if not request.GET or form.is_valid():
        learners,rows=build_coverage(request.user,form.cleaned_data if form.is_bound else {})
    if request.GET.get('download') == 'excel' and not form.errors:
        if not (request.user.can_export or request.user.is_superuser): raise PermissionDenied
        response=HttpResponse(coverage_workbook(learners,rows),content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition']='attachment; filename="BK-en-subdoelenoverzicht.xlsx"'
        response['Cache-Control']='private, no-store'
        log(request.user,'subdoelenoverzicht geëxporteerd',request.user)
        return response
    return render(request,'evaluations/coverage.html',{'form':form,'learners':learners,'rows':rows,'nav':'coverage'})

