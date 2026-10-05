"""Shared presentation of owner-scoped records; sorting/filtering happens in the UI."""
from django.urls import reverse
from .models import Year, Subject, Classroom, Student, StudyDirection


def management_table(kind, objects, year, selected_class=None, user=None):
    columns = {
        'schooljaren': ['Schooljaar'],
        'studierichtingen': ['Studierichting'],
        'vakken': ['Vak', 'Schooljaar', 'Studierichtingen'],
        'klassen': ['Klas', 'Studierichting', 'Leerjaar', 'Schooljaar', 'Vakken', 'Status', 'Leerlingen'],
        'leerlingen': ['Leerling', 'Klas', 'Studierichting', 'Leerjaar', 'Schooljaar', 'Status'],
        'doelen': ['Code', 'Leerplandoel', 'Studierichting', 'Graad', 'Status'],
    }[kind]
    rows = []
    for item in objects:
        if isinstance(item, (Year, StudyDirection)):
            cells = [item.name]
        elif isinstance(item, Subject):
            cells = [item.name, item.year.name, ", ".join(str(d) for d in item.study_directions.all())]
        elif isinstance(item, Classroom):
            cells = [item.name, item.direction_name, item.grade or '', item.year.name,
                     ', '.join(s.name for s in item.subjects.all()),
                     'Gearchiveerd' if item.archived else 'Actief', item.students.count()]
        elif isinstance(item, Student):
            c = item.classroom
            cells = [item.name, c.name, c.direction_name, c.grade or '', c.year.name,
                     'Actief' if item.active else 'Inactief']
        else:
            cells = [item.code, item.title, str(item.study_direction) if item.study_direction_id else 'Nog te koppelen',
                     item.get_stage_display() if item.stage else 'Nog te kiezen',
                     'Gearchiveerd' if item.archived else 'Actief']
        item_year = item if isinstance(item, Year) else (item.classroom.year if isinstance(item, Student) else getattr(item, "year", None))
        row = {'cells': cells, 'url': reverse('manage_edit', args=[kind, item.pk]) + (f'?year={item_year.pk}' if item_year else ''), 'action': 'Wijzigen'}
        row['delete_url'] = reverse('delete_record', args=[kind, item.pk])
        row['label'] = str(item)
        if kind == 'klassen':
            row['related_url'] = reverse('manage', args=['klassen']) + (f'?year={year.pk}&' if year else '?') + f'classroom={item.pk}#leerlingen'
            row['related_label'] = 'Leerlingen'
            row['select_url'] = row['related_url']
            row['selected'] = selected_class is not None and item.pk == selected_class.pk
        owner = item.classroom.owner if isinstance(item, Student) else item.owner
        cells.append(owner.get_full_name() or owner.username)
        rows.append(row)
    return {'columns': [*columns, 'Leerkracht'], 'rows': rows}


def lesson_table(lessons, user=None):
    return {'columns': ['Datum', 'Lesonderwerp', 'Klas', 'Vak', 'Leerjaar', 'Schooljaar', 'Klasfeedback', 'Leerkracht'],
            'rows': [{'cells': [l.date.isoformat(), l.title, l.classroom.name, l.subject.name,
                               l.grade or '', l.classroom.year.name, l.feedback, l.owner.get_full_name() or l.owner.username],
                      'url': reverse('lesson', args=[l.pk]), 'action': 'Bekijken' if user and not user.is_superuser and l.owner_id != user.pk else 'Evalueren',
                      'delete_url': reverse('delete_record', args=['lessen', l.pk]) if not user or user.is_superuser or l.owner_id == user.pk else None, 'label': l.title} for l in lessons]}
