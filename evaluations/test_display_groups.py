from datetime import date
from django.test import TestCase
from accounts.models import User
from .models import Year, Subject, Classroom, Lesson, LessonGoal, LessonPoint, LessonStudent, Score


class DisplayGroupTests(TestCase):
    def setUp(self):
        user = User.objects.create_user('grouping', can_evaluate=True)
        year = Year.objects.create(owner=user, name='2026')
        subject = Subject.objects.create(owner=user, year=year, name='Praktijk')
        room = Classroom.objects.create(owner=user, year=year, name='6A', grade=6)
        self.lesson = Lesson.objects.create(owner=user, classroom=room, subject=subject,
                                          grade=6, title='Test', date=date(2026, 10, 4))
        self.learner = LessonStudent.objects.create(lesson=self.lesson, name='Testleerling')
        self.goals = []
        self.points = []
        for i, title in enumerate(['Veilig werken', 'Ander doel', 'Veilig werken']):
            goal = LessonGoal.objects.create(lesson=self.lesson, code=f'BK{i}', title=title, position=i)
            point = LessonPoint.objects.create(goal=goal, title=f'Subdoel {i}', position=0)
            self.goals.append(goal)
            self.points.append(point)
        Score.objects.create(point=self.points[0], learner=self.learner, value=0)
        Score.objects.create(point=self.points[2], learner=self.learner, value=80)
        self.client.force_login(user)

    def test_grouping_keeps_ids_and_weights_zero_in_combined_total(self):
        response = self.client.get(f'/lessen/{self.lesson.pk}/')
        groups = response.context['display_groups']
        self.assertEqual(len(groups), 2)
        self.assertEqual(groups[0]['ids'], f'{self.goals[0].pk},{self.goals[2].pk}')
        self.assertEqual(groups[0]['students'][0]['total'], 80)
        self.assertEqual(groups[0]['students'][0]['maximum'], 160)
        self.assertEqual(groups[0]['students'][0]['average'], 40)
        self.assertContains(response, '<strong class="point-code">BK0:</strong>')
        self.assertContains(response, '<strong class="point-code">BK2:</strong>')
        self.assertContains(response, '<strong class="goal-number">BK1</strong>')
        for point in self.points:
            self.assertContains(response, f'name="score_{point.pk}_{self.learner.pk}"', count=1)
        self.assertEqual(self.lesson.goals.count(), 3)

    def test_reordering_group_preserves_every_score_and_reappears_after_save(self):
        order = [self.goals[1].pk, self.goals[0].pk, self.goals[2].pk]
        payload = {'goal_order': ','.join(map(str, order)), 'revision': 0,
                   'title': 'Test', 'date': '2026-10-04', 'feedback': '',
                   f'feedback_{self.learner.pk}': 'Goed gewerkt'}
        for point, value in zip(self.points, ['0', '', '80']):
            payload[f'score_{point.pk}_{self.learner.pk}'] = value
        response = self.client.post(f'/lessen/{self.lesson.pk}/', payload, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(self.lesson.goals.values_list('pk', flat=True)), order)
        self.assertEqual(response.context['display_order'], ','.join(map(str, order)))
        self.assertEqual(sorted(Score.objects.values_list('value', flat=True)), [0, 80])
        self.assertEqual(self.lesson.roster.get().feedback, 'Goed gewerkt')
