from django import forms

class ExportForm(forms.Form):
    mode = forms.ChoiceField(label='Soort export', choices=[('class', 'Klasoverzicht'), ('student', 'Individuele leerling')],
        widget=forms.RadioSelect, initial='class')
    student = forms.ChoiceField(label='Leerling', required=False)
    lessons = forms.MultipleChoiceField(label='Lessen opnemen', widget=forms.CheckboxSelectMultiple)

    def __init__(self, *args, lessons, students, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['lessons'].choices = [(str(lesson.pk), f'{lesson.date:%d/%m/%Y} · {lesson.title} · {lesson.subject.name}') for lesson in lessons]
        self.fields['student'].choices = [('', 'Kies een leerling')] + [(str(s.pk), s.name) for s in students]

    def clean(self):
        data = super().clean()
        if data.get('mode') == 'student' and not data.get('student'):
            self.add_error('student', 'Kies de leerling waarvoor je een puntenlijst wilt maken.')
        if len(data.get('lessons', [])) > 100:
            self.add_error('lessons', 'Kies maximaal 100 lessen per bestand. Verklein eventueel de periode.')
        return data
