from functools import wraps
from datetime import date
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.db.models import F
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import (Year, Subject, Classroom, Student, Goal, Point, Lesson, StudyDirection,
    LessonStudent, LessonPoint, Score, AuditEvent, stage_for_grade)
from .forms import StudyDirectionForm, YearForm, SubjectForm, ClassroomForm, StudentForm, GoalForm, LessonForm
from .services import lesson_report, snapshot_goal, goals_for_lesson, display_goal_groups
from .tables import management_table, lesson_table
from accounts.access import visible_records, visible_owner_ids

def teacher_required(view):
    @login_required
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not (request.user.can_evaluate or request.user.is_superuser):
            raise PermissionDenied('Je hebt geen toegang tot Leerlingenevaluaties.')
        return view(request, *args, **kwargs)
    return wrapped

def log(user, action, obj):
    AuditEvent.objects.create(actor=user, action=action, object_type=obj._meta.model_name, object_id=obj.pk)

def selected_year(request):
    years = visible_records(Year, request.user)
    key = request.GET.get('year') or request.POST.get('year')
    if key:
        try:
            return get_object_or_404(years, pk=int(key))
        except ValueError:
            raise Http404
    return years.first()

@login_required
def home(request):
    return render(request, 'home.html')

@teacher_required
def dashboard(request):
    year = selected_year(request) if request.GET.get('year') else None
    classes = visible_records(Classroom, request.user).select_related('year')
    lessons = visible_records(Lesson, request.user).select_related('classroom__year', 'subject', 'owner')
    goals = visible_records(Goal, request.user).filter(archived=False)
    if year:
        classes = classes.filter(year=year)
        lessons = lessons.filter(classroom__year=year)
        # Goals are reusable across school years.
    classroom = None
    if request.GET.get('classroom'):
        classroom = get_object_or_404(classes, pk=request.GET['classroom'])
        lessons = lessons.filter(classroom=classroom)
    return render(request, 'evaluations/dashboard.html', {'year': year, 'classes': classes,
        'lessons': lessons, 'lesson_table': lesson_table(lessons, request.user), 'classroom': classroom, 'nav': 'lessons',
        'student_count': Student.objects.filter(classroom__in=classes, active=True).count(),
        'goal_count': goals.count()})

KINDS = {
    'studierichtingen': (StudyDirection, StudyDirectionForm, 'Studierichtingen', 'studierichting'),
    'schooljaren': (Year, YearForm, 'Schooljaren', 'schooljaar'),
    'vakken': (Subject, SubjectForm, 'Vakken', 'vak'),
    'klassen': (Classroom, ClassroomForm, 'Klassen', 'klas'),
    'leerlingen': (Student, StudentForm, 'Leerlingen', 'leerling'),
    'doelen': (Goal, GoalForm, 'Leerplandoelstellingen', 'doelstelling'),
}

def owned_objects(model, user):
    return model.objects.filter(**({'classroom__owner': user} if model == Student else {'owner': user}))

@login_required
def manage(request, kind='klassen', pk=None):
    if kind not in KINDS:
        raise Http404
    model, form_cls, title, singular = KINDS[kind]
    year = None if model in (StudyDirection, Goal) else selected_year(request)
    if not year and model not in (Year, StudyDirection, Goal):
        messages.info(request, 'Maak eerst een schooljaar aan.')
        return redirect('manage', kind='schooljaren')
    overview_all_years = not pk and 'nieuw' not in request.GET and request.method == 'GET' and not request.GET.get('year')
    if overview_all_years:
        year = None
    qs = model.objects.all()
    if model == Student:
        qs = qs.select_related('classroom__year')
        if year:
            qs = qs.filter(classroom__year=year)
    elif model not in (Year, StudyDirection, Goal) and year:
        qs = qs.filter(year=year)
    obj = get_object_or_404(qs, pk=pk) if pk else model()
    editing = bool(pk)
    show_form = editing or 'nieuw' in request.GET or request.method == 'POST' or (model == Year and not qs.exists())
    if model != Student and not editing:
        obj.owner = request.user
        if model not in (Year, StudyDirection, Goal):
            obj.year = year
    form = form_cls(request.POST or None, instance=obj)
    classes = visible_records(Classroom, request.user).select_related('year')
    if year:
        classes = classes.filter(year=year)
    selected_class = None
    if request.GET.get('classroom') and model in (Classroom, Student):
        selected_class = get_object_or_404(classes, pk=request.GET['classroom'])
        if model == Student and not editing:
            form.initial['classroom'] = selected_class.pk
    subjects = Subject.objects.filter(year=year)
    if model in (StudyDirection, Goal):
        year = None
    if model == Subject:
        form.fields['study_directions'].queryset = StudyDirection.objects.all()
    if model == Classroom:
        form.fields['study_direction'].queryset = StudyDirection.objects.all()
        form.fields['subjects'].queryset = subjects
    if model == Student:
        form.fields['classroom'].queryset = classes
    if model == Goal and not editing and request.method == 'GET':
        form.initial.update(request.user.goal_defaults)
    if model == Goal:
        form.fields['study_direction'].queryset = StudyDirection.objects.all()
        if editing and request.method != 'POST':
            form.fields['evaluation_points'].initial = '\n'.join(obj.points.values_list('title', flat=True))
    if request.method == 'POST' and form.is_valid():
        # Ownership and schoolyear are server assigned, never taken from form IDs.
        duplicate = model != Student and model != Goal and qs.exclude(pk=obj.pk).filter(name=form.cleaned_data['name']).exists()
        if duplicate:
            form.add_error('name', 'Deze naam bestaat al binnen deze context.')
        elif model == Student and editing and obj.lessonstudent_set.exists() and form.cleaned_data['classroom'].pk != Student.objects.get(pk=obj.pk).classroom_id:
            form.add_error('classroom', 'Deze leerling heeft al lessen. Maak voor een andere klas een nieuwe inschrijving.')
        else:
            try:
                with transaction.atomic():
                    obj = form.save()
                    if model == Goal:
                        request.user.goal_defaults = {'study_direction': obj.study_direction_id, 'stage': obj.stage}
                        request.user.save(update_fields=['goal_defaults'])
                        # Preserve identity for unchanged subgoals, including when reordered.
                        old = {p.title: p for p in obj.points.all()}
                        keep = []
                        for i, title in enumerate(form.cleaned_data['evaluation_points']):
                            point = old.get(title) or Point(goal=obj, title=title)
                            point.position = i
                            point.save()
                            keep.append(point.pk)
                        obj.points.exclude(pk__in=keep).delete()
                    log(request.user, 'gewijzigd' if editing else 'aangemaakt', obj)
                messages.success(request, f'{singular.capitalize()} opgeslagen.')
                if model in (StudyDirection, Goal):
                    return redirect('manage', kind=kind)
                target_year = obj if model == Year else year
                if model == Student:
                    return redirect(reverse('manage', args=['klassen']) + f'?year={target_year.pk}&classroom={obj.classroom_id}#leerlingen')
                return redirect(reverse('manage', args=[kind]) + f'?year={target_year.pk}')
            except IntegrityError as e:
                form.add_error(None, f'Deze gegevens bestaan al. Controleer de naam en probeer opnieuw. Fout: {str(e)}')
    class_screen = model in (Classroom, Student)
    pupils = visible_records(Student, request.user).select_related('classroom__year')
    if year:
        pupils = pupils.filter(classroom__year=year)
    if selected_class:
        pupils = pupils.filter(classroom=selected_class)
    table_objects = classes.prefetch_related('subjects', 'students').select_related('year') if class_screen else qs
    if model == Subject:
        table_objects = qs.select_related('year')
    if model == Goal:
        table_objects = qs.select_related('study_direction').prefetch_related('points')
    return render(request, 'evaluations/manage.html', {'year': year, 'kind': kind,
        'title': 'Klassen & leerlingen' if class_screen else title, 'class_screen': class_screen,
        'table': management_table('klassen' if class_screen else kind, table_objects, year, selected_class, request.user),
        'pupil_table': management_table('leerlingen', pupils, year, user=request.user) if class_screen else None,
        'classes': classes, 'selected_class': selected_class,
        'singular': singular, 'form': form, 'show_form': show_form, 'editing': editing, 'nav': 'manage'})


@teacher_required
def goal_import(request):
    # The parser is deliberately not guessed before the official reference files arrive.
    year = None
    return render(request, 'evaluations/goal_import.html', {'year': year, 'nav': 'manage'})

@teacher_required
def lesson_create(request):
    year = selected_year(request)
    if not year:
        return redirect('manage', kind='schooljaren')
    form = LessonForm(request.POST or None, initial={'date': date.today(), 'classroom': request.GET.get('classroom')})
    form.fields['classroom'].queryset = visible_records(Classroom, request.user).filter(year=year, archived=False)
    form.fields['subject'].queryset = visible_records(Subject, request.user).filter(year=year)
    if request.method == 'POST' and form.is_valid():
        classroom = form.cleaned_data['classroom']
        if not classroom.students.filter(active=True).exists():
            form.add_error('classroom', 'Voeg eerst leerlingen toe aan deze klas.')
        else:
            with transaction.atomic():
                lesson = form.save(commit=False)
                lesson.owner = request.user
                lesson.grade = classroom.grade
                lesson.save()
                LessonStudent.objects.bulk_create([LessonStudent(lesson=lesson, student=s, name=s.name)
                    for s in classroom.students.filter(active=True)])
                log(request.user, 'aangemaakt', lesson)
            return redirect('lesson', pk=lesson.pk)
    return render(request, 'evaluations/lesson_create.html', {'form': form, 'year': year, 'nav': 'lessons'})

class EditConflict(Exception): pass

def claim_revision(lesson, value):
    try:
        revision = int(value)
    except (TypeError, ValueError):
        raise EditConflict
    if not Lesson.objects.filter(pk=lesson.pk, revision=revision).update(
            revision=F('revision') + 1, updated_at=timezone.now()):
        raise EditConflict

@teacher_required
def lesson_detail(request, pk):
    lesson = get_object_or_404(visible_records(Lesson, request.user).select_related('classroom__year', 'subject', 'owner'), pk=pk)
    read_only = lesson.owner_id != request.user.pk and not request.user.is_superuser
    if request.method == 'POST' and read_only:
        raise PermissionDenied('Alleen de oorspronkelijke leerkracht kan deze evaluatie aanpassen.')
    submitted, errors = None, []
    status = 200
    if request.method == 'POST':
        submitted = request.POST
        learners = list(lesson.roster.all())
        points = list(LessonPoint.objects.filter(goal__lesson=lesson))
        parsed = []
        ordered_goals = None
        if 'goal_order' in request.POST:
            try:
                ordered_goals = [int(key) for key in request.POST['goal_order'].split(',') if key]
                current = set(lesson.goals.values_list('pk', flat=True))
                if len(ordered_goals) != len(current) or set(ordered_goals) != current:
                    raise ValueError
            except ValueError:
                errors.append('De doelvolgorde is ongeldig. Er is niets opgeslagen.')
        # Require the complete form: a truncated request must never erase scores.
        expected = {f'score_{p.pk}_{s.pk}' for p in points for s in learners}
        expected |= {f'feedback_{s.pk}' for s in learners}
        expected |= {'title', 'date', 'feedback', 'revision'}
        if not expected.issubset(request.POST.keys()):
            errors.append('Het formulier is onvolledig ontvangen. Er is niets opgeslagen.')
        for p in points:
            for s in learners:
                raw = request.POST.get(f'score_{p.pk}_{s.pk}', '')
                if raw not in ('', '0', '20', '40', '60', '80', 'absent'):
                    errors.append('Alleen 0, 20, 40, 60, 80 en Afwezig zijn toegestaan.')
                elif raw == 'absent':
                    parsed.append(Score(point=p, learner=s, value=None, status='absent'))
                elif raw:
                    parsed.append(Score(point=p, learner=s, value=int(raw)))
        title = request.POST.get('title', '').strip()
        if not title:
            errors.append('Vul een lesonderwerp in.')
        elif len(title) > 180:
            errors.append('Het lesonderwerp mag maximaal 180 tekens bevatten.')
        try:
            lesson_date = date.fromisoformat(request.POST.get('date', ''))
        except ValueError:
            errors.append('Vul een geldige datum in (JJJJ-MM-DD).')
        if not errors:
            try:
                with transaction.atomic():
                    claim_revision(lesson, request.POST.get('revision'))
                    if ordered_goals is not None:
                        goal_map = {g.pk: g for g in lesson.goals.all()}
                        for position, key in enumerate(ordered_goals):
                            goal_map[key].position = position
                        lesson.goals.model.objects.bulk_update(goal_map.values(), ['position'])
                    Lesson.objects.filter(pk=lesson.pk).update(title=title, date=lesson_date, feedback=request.POST.get('feedback', ''))
                    Score.objects.filter(point__goal__lesson=lesson).delete()
                    Score.objects.bulk_create(parsed)
                    for s in learners:
                        s.feedback = request.POST.get(f'feedback_{s.pk}', '')
                    LessonStudent.objects.bulk_update(learners, ['feedback'])
                    log(request.user, 'evaluatie opgeslagen', lesson)
                messages.success(request, 'Scores en feedback zijn opgeslagen.')
                return redirect('lesson', pk=lesson.pk)
            except EditConflict:
                errors.append('Deze les is intussen gewijzigd in een ander venster of tabblad. Je invoer staat hieronder om te vergelijken. Open de actuele les in een nieuw tabblad en kopieer je wijzigingen handmatig.')
                status = 409
        else:
            status = 400
    report = lesson_report(lesson, submitted)
    if submitted is not None and ordered_goals is not None and not any('doelvolgorde' in e for e in errors):
        order = {pk: i for i, pk in enumerate(ordered_goals)}
        report['groups'].sort(key=lambda group: order[group['goal'].pk])
    report['display_groups'] = display_goal_groups(report['groups'])
    report['display_order'] = ','.join(g['ids'] for g in report['display_groups'])
    available = list(goals_for_lesson(lesson, request.user).prefetch_related('points'))
    present = set(LessonPoint.objects.filter(goal__lesson=lesson).values_list('source_point_id', flat=True))
    direct = set(LessonPoint.objects.filter(goal__lesson=lesson, is_direct=True).values_list('goal__source_id', flat=True))
    for goal in available:
        goal.selection_points = list(goal.points.all())
        for point in goal.selection_points:
            point.in_lesson = point.pk in present
        goal.fully_selected = all(p.in_lesson for p in goal.selection_points) if goal.selection_points else goal.pk in direct
    return render(request, 'evaluations/lesson.html', {**report, 'lesson': lesson,
        'year': lesson.classroom.year, 'goal_stage': stage_for_grade(lesson.grade), 'nav': 'lessons', 'available': available,
        'result_columns': ['Code', 'Leerplandoel', 'Totaal', 'Gemiddelde', 'Beoordeeld', 'Afwezig'],
        'read_only': read_only, 'errors': list(dict.fromkeys(errors)), 'submitted': submitted,
        'form_title': request.POST.get('title', lesson.title),
        'form_date': request.POST.get('date', lesson.date.isoformat()),
        'form_feedback': request.POST.get('feedback', lesson.feedback),
        'form_revision': request.POST.get('revision', lesson.revision)}, status=status)

@teacher_required
@require_POST
def lesson_goal_action(request, pk):
    lesson = get_object_or_404(Lesson.objects.all() if request.user.is_superuser else Lesson.objects.filter(owner=request.user), pk=pk)
    action = request.POST.get('action')
    try:
        with transaction.atomic():
            claim_revision(lesson, request.POST.get('revision'))
            if action in ('add', 'add_selection'):
                catalog = goals_for_lesson(lesson, request.user)
                if action == 'add':
                    source = get_object_or_404(catalog, pk=request.POST.get('goal'))
                    snapshot_goal(lesson, source)
                else:
                    goal_ids = {int(v) for v in request.POST.getlist('goals')}
                    point_ids = {int(v) for v in request.POST.getlist('points')}
                    sources = {g.pk: g for g in catalog.prefetch_related('points')}
                    points = {p.pk: p for g in sources.values() for p in g.points.all()}
                    if not goal_ids and not point_ids:
                        raise ValueError('Vink minstens één BK of subdoel aan om toe te voegen.')
                    if not goal_ids <= sources.keys() or not point_ids <= points.keys():
                        raise ValueError('De selectie bevat doelen die niet beschikbaar zijn voor dit leerplan. Controleer je selectie.')
                    for source in sources.values():
                        chosen = [p for p in source.points.all() if p.pk in point_ids]
                        if source.pk in goal_ids or chosen:
                            snapshot_goal(lesson, source, None if source.pk in goal_ids else chosen)
            elif action in ('remove', 'remove_point', 'up', 'down'):
                if action in ('remove', 'up', 'down'):
                    target = get_object_or_404(lesson.goals, pk=request.POST.get('goal'))
                    if action == 'remove':
                        if request.POST.get('confirm') != 'yes':
                            raise ValueError('Bevestig dat je dit doel en alle bijbehorende scores wilt verwijderen. Deze actie kan niet ongedaan worden gemaakt.')
                        target.delete()
                    else:
                        goals = list(lesson.goals.all())
                        index = next(i for i, g in enumerate(goals) if g.pk == target.pk)
                        other = index + (-1 if action == 'up' else 1)
                        if 0 <= other < len(goals):
                            goals[index], goals[other] = goals[other], goals[index]
                        for i, goal in enumerate(goals):
                            goal.position = i
                        lesson.goals.model.objects.bulk_update(goals, ['position'])
                elif action == 'remove_point':
                    target_point = get_object_or_404(LessonPoint, pk=request.POST.get('point'))
                    if request.POST.get('confirm') != 'yes':
                        raise ValueError('Bevestig dat je dit subdoel en de bijbehorende scores wilt verwijderen. Deze actie kan niet ongedaan worden gemaakt.')
                    target_point.delete()
            else:
                raise ValueError('Onbekende actie. Geldige acties zijn: up, down, remove, remove_point.')
            log(request.user, f'lesdoel {action}', lesson)
    except EditConflict:
        messages.error(request, 'De les is intussen gewijzigd. Controleer de actuele versie en probeer opnieuw.')
    except ValueError as error:
        messages.error(request, str(error))
    return redirect('lesson', pk=lesson.pk)
