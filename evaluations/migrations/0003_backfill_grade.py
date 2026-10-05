import re
from django.db import migrations

def backfill(apps, schema_editor):
    Classroom = apps.get_model('evaluations', 'Classroom')
    Goal = apps.get_model('evaluations', 'Goal')
    Lesson = apps.get_model('evaluations', 'Lesson')
    for classroom in Classroom.objects.filter(grade__isnull=True):
        match = re.match(r'^([1-7])(?:\D|$)', classroom.name.strip())
        if match:
            classroom.grade = int(match.group(1))
            classroom.save(update_fields=['grade'])
    for goal in Goal.objects.filter(grade__isnull=True):
        grades = set(goal.classrooms.values_list('grade', flat=True))
        if len(grades) == 1 and None not in grades:
            goal.grade = grades.pop()
            goal.save(update_fields=['grade'])
    for lesson in Lesson.objects.filter(grade__isnull=True).select_related('classroom'):
        lesson.grade = lesson.classroom.grade
        lesson.save(update_fields=['grade'])

class Migration(migrations.Migration):
    dependencies = [('evaluations', '0002_remove_score_allowed_score_classroom_grade_and_more')]
    operations = [migrations.RunPython(backfill, migrations.RunPython.noop)]
