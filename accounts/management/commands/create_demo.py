import secrets
from datetime import date
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from accounts.models import User
from evaluations.models import Year, Subject, Classroom, Student, Goal, Point, Lesson, LessonStudent, Score, StudyDirection
from evaluations.services import snapshot_goal

class Command(BaseCommand):
    help = 'Maak eenmalig fictieve demonstratiegegevens en lokale accounts aan.'

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.DEBUG and not settings.STANDALONE:
            raise CommandError('Demogegevens zijn alleen toegestaan in ontwikkeling.')
        if User.objects.exists():
            raise CommandError('Er bestaan al accounts. Demo wordt niet opnieuw uitgevoerd of overschreven.')
        teacher_password = secrets.token_urlsafe(16)
        admin_password = secrets.token_urlsafe(16)
        teacher = User.objects.create_user('demo.leerkracht', password=teacher_password,
            first_name='Sam', last_name='Demo', can_evaluate=True)
        User.objects.create_superuser('beheerder', email='', password=admin_password, first_name='Beheerder')
        year = Year.objects.create(owner=teacher, name='2026–2027')
        subject = Subject.objects.create(owner=teacher, year=year, name='Praktijk haarzorg')
        direction = StudyDirection.objects.create(owner=teacher, name='Haarverzorging')
        subject.study_directions.add(direction)
        classroom = Classroom.objects.create(owner=teacher, year=year, name='6HV', direction='Haarverzorging', study_direction=direction, grade=6)
        classroom.subjects.add(subject)
        for name in ['Alex Voorbeeld', 'Bo Voorbeeld', 'Charlie Voorbeeld', 'Dani Voorbeeld']:
            Student.objects.create(classroom=classroom, name=name)
        descriptions = [
            ('DEMO.01', 'Een verzorgende wasbehandeling uitvoeren', ['De haren voldoende vochtig maken', 'Een geschikte shampoo kiezen', 'De haren zorgvuldig uitspoelen']),
            ('DEMO.02', 'Veilig en hygiënisch werken', ['De werkplek voorbereiden', 'Materialen hygiënisch gebruiken']),
            ('DEMO.03', 'De klant begeleiden', ['De wensen van de klant bespreken', 'Duidelijke verzorgingstips meegeven']),
        ]
        sources = []
        for code, title, points in descriptions:
            goal = Goal.objects.create(owner=teacher, study_direction=direction, stage=3, code=code, title=title)
            for i, text in enumerate(points):
                Point.objects.create(goal=goal, title=text, position=i)
            sources.append(goal)
        lesson = Lesson.objects.create(owner=teacher, classroom=classroom, subject=subject, grade=6,
            title='Wasbehandeling & verzorging', date=date(2026, 10, 5),
            feedback='Fictieve demonstratieles. De klas werkte aandachtig aan de voorbereiding en productkeuze.')
        roster = [LessonStudent.objects.create(lesson=lesson, student=s, name=s.name) for s in classroom.students.all()]
        for goal in sources[:2]:
            snap = snapshot_goal(lesson, goal)
            for p in snap.points.all():
                for i, learner in enumerate(roster):
                    if i != 3:
                        Score.objects.create(point=p, learner=learner, value=[60, 80, 40][i])
        credentials = settings.DATA_DIR / 'demo-toegang.txt'
        credentials.write_text(
            'ALLEEN LOKALE DEMO — fictieve gegevens\n\n'
            f'Leerkracht: demo.leerkracht\nWachtwoord: {teacher_password}\n\n'
            f'Admin: beheerder\nWachtwoord: {admin_password}\n\n'
            'Verwijder of beveilig dit bestand voordat echte gegevens worden gebruikt.\n', encoding='utf-8')
        self.stdout.write(self.style.SUCCESS(f'Demo aangemaakt. Lokale inloggegevens: {credentials}'))
