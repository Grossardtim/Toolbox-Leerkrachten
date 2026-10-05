from datetime import date
from functools import wraps
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils.http import content_disposition_header
import re
from django.views.decorators.cache import never_cache
from evaluations.models import Classroom, Subject, Student, Lesson
from evaluations.views import teacher_required, selected_year, log
from .forms import ExportForm
from accounts.access import visible_records
from .services import export_payload, render_excel, ExportUnavailable

@never_cache
@teacher_required
def index(request):
    if not (request.user.can_export or request.user.is_superuser):
        raise PermissionDenied('Je hebt geen toegang tot Excel-export.')
    year = selected_year(request)
    classes = visible_records(Classroom, request.user).filter(year=year)
    classroom = None
    key = request.GET.get('classroom') or request.POST.get('classroom')
    if key:
        try:
            classroom = get_object_or_404(classes, pk=int(key))
        except ValueError:
            raise Http404
    subjects, students, lessons = [], [], []
    source = request.POST if request.method == 'POST' else request.GET
    filters = {key: source.get(key, '') for key in ('subject', 'from', 'to')}
    filter_error = None
    if classroom:
        # Include subjects used by historical lessons even if the class setup changed.
        subjects = Subject.objects.filter(year=year,
            pk__in=visible_records(Lesson, request.user).filter(classroom=classroom).values('subject_id')).distinct()
        students = Student.objects.filter(classroom=classroom)
        query = visible_records(Lesson, request.user).filter(classroom=classroom).select_related('subject').order_by('date', 'pk')
        if filters['subject']:
            try:
                subject = get_object_or_404(subjects, pk=int(filters['subject']))
                query = query.filter(subject=subject)
            except ValueError:
                raise Http404
        try:
            start = date.fromisoformat(filters['from']) if filters['from'] else None
            end = date.fromisoformat(filters['to']) if filters['to'] else None
            if start and end and start > end:
                raise ValueError
            if start: query = query.filter(date__gte=start)
            if end: query = query.filter(date__lte=end)
        except ValueError:
            filter_error = 'Kies een geldige periode; de begindatum mag niet na de einddatum liggen.'
            query = query.none()
        lessons = list(query)
    preset = request.GET.get('lesson')
    form = ExportForm(request.POST if request.method == 'POST' else None,
        lessons=lessons, students=students,
        initial={'mode': request.GET.get('mode', 'class'), 'student': request.GET.get('student', ''), 'lessons': [str(l.pk) for l in lessons if not preset or str(l.pk) == preset]})
    if request.method == 'POST' and classroom and not filter_error and form.is_valid():
        chosen = [l for l in lessons if str(l.pk) in form.cleaned_data['lessons']]
        student = None
        if form.cleaned_data['mode'] == 'student':
            student = get_object_or_404(Student, pk=int(form.cleaned_data['student']), classroom=classroom)
        try:
            payload = export_payload(chosen, classroom, student)
            content = render_excel(payload)
        except (ValueError, ExportUnavailable) as error:
            form.add_error(None, str(error))
        else:
            included = [lesson for lesson in chosen if student is None or lesson.roster.filter(student=student).exists()]
            filename = export_filename(year, classroom, included, student)
            response = HttpResponse(content, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = content_disposition_header(True, filename)
            response['X-Content-Type-Options'] = 'nosniff'
            response['Cache-Control'] = 'private, no-store, max-age=0'
            log(request.user, 'individueel Excel-puntenlijst' if student else 'klas Excel-puntenlijst', student or classroom)
            return response
    return render(request, 'exports/index.html', {'year': year, 'classes': classes,
        'classroom': classroom, 'subjects': subjects, 'lessons': lessons,
        'form': form, 'filters': filters, 'filter_error': filter_error, 'nav': 'exports',
        'selection_rows': list(zip(form['lessons'], lessons))})


def export_filename(year, classroom, lessons, student=None):
    subjects = sorted({l.subject.name for l in lessons})
    dates = sorted({l.date.isoformat() for l in lessons})
    parts = [year.name, classroom.name, subjects[0] if len(subjects) == 1 else 'Meerdere vakken']
    if student:
        parts.append(student.name)
    parts += [lessons[0].title if len(lessons) == 1 else f'{len(lessons)} lessen', dates[0] if len(dates) == 1 else f'{dates[0]} tot {dates[-1]}']
    limit = min(80, (230 - 3 * (len(parts) - 1)) // len(parts))
    return ' - '.join(re.sub(r'[<>:"/\\|?*\x00-\x1f]', '-', p).strip(' .')[:limit] or 'Naamloos' for p in parts) + '.xlsx'
