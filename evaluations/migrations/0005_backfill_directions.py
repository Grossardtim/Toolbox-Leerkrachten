from django.db import migrations


def forwards(apps, schema_editor):
    Classroom = apps.get_model('evaluations', 'Classroom')
    Direction = apps.get_model('evaluations', 'StudyDirection')
    alias = schema_editor.connection.alias
    for classroom in Classroom.objects.using(alias).all():
        direction, _ = Direction.objects.using(alias).get_or_create(
            owner_id=classroom.owner_id, name=classroom.direction.strip() or 'Nog in te vullen')
        classroom.study_direction_id = direction.pk
        classroom.save(using=alias, update_fields=['study_direction'])
        for subject in classroom.subjects.all():
            subject.study_directions.add(direction)


class Migration(migrations.Migration):
    dependencies = [('evaluations', '0004_studydirection_classroom_study_direction_and_more')]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
