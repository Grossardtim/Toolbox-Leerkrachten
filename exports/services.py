"""Privacy-filtered report data and the Excel generation adapter.

Only a new, minimal payload goes to the workbook engine. No class workbook is
ever reused to create a student report. Exported files are temporary and private.
"""
from django.conf import settings
from evaluations.models import Lesson, LessonStudent, Score

class ExportUnavailable(Exception):
    pass

def export_payload(lessons, classroom, student=None):
    lessons = list(lessons)
    individual = student is not None
    result = {
        'mode': 'student' if individual else 'class',
        'school': 'GO! Atheneum Tungrorum', 'schoolYear': classroom.year.name,
        'className': classroom.name, 'direction': classroom.direction_name,
        'grade': classroom.grade, 'studentName': student.name if individual else None,
        'lessons': [],
    }
    for lesson in lessons:
        if lesson.classroom_id != classroom.pk:
            raise ValueError('Les hoort niet bij de geselecteerde klas.')
        roster = LessonStudent.objects.filter(lesson=lesson)
        if individual:
            if student.classroom_id != classroom.pk:
                raise ValueError('Leerling hoort niet bij de geselecteerde klas.')
            roster = roster.filter(student=student)
        learners = list(roster)
        if individual and not learners:
            continue
        scores = {(s.point_id, s.learner_id): ('Afwezig' if s.status == 'absent' else s.value)
                  for s in Score.objects.filter(point__goal__lesson=lesson, learner__in=learners)}
        record = {'date': lesson.date.isoformat(), 'title': lesson.title,
            'subject': lesson.subject.name, 'grade': lesson.grade,
            'teacher': lesson.owner.get_full_name() or lesson.owner.username,
            'students': [{'key': f's{s.student_id}' if s.student_id else f'r{s.pk}',
                          'name': s.name, 'feedback': s.feedback} for s in learners],
            'goals': []}
        # Class feedback can name peers: never send it to the student renderer.
        if not individual:
            record['classFeedback'] = lesson.feedback
        for goal in lesson.goals.prefetch_related('points'):
            points = [{'title': p.title, 'values': [scores.get((p.pk, s.pk)) for s in learners]} for p in goal.points.all()]
            points = [p for p in points if any(isinstance(v, int) for v in p['values'])]
            if points:
                record['goals'].append({'code': goal.code, 'title': goal.title, 'points': points})
        result['lessons'].append(record)
    if not result['lessons']:
        raise ValueError('De gekozen leerling komt niet voor in de geselecteerde lessen.')
    revisions = dict(Lesson.objects.filter(pk__in=[l.pk for l in lessons]).values_list('pk','revision'))
    if any(revisions.get(l.pk) != l.revision for l in lessons):
        raise ValueError('Een les is tijdens de export gewijzigd. Probeer de export opnieuw.')
    return result


def render_excel(payload):
    from .workbook import build_workbook
    try:
        return build_workbook(payload, settings.BASE_DIR / 'static/school-logo.png')
    except (OSError, ValueError) as error:
        raise ExportUnavailable('De Excel-puntenlijst kon niet worden samengesteld.') from error
