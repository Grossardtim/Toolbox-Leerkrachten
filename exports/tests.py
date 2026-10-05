import io
import json
import zipfile
from datetime import date
from unittest.mock import patch
from xml.etree import ElementTree as ET
from django.test import TestCase
from accounts.models import User
from evaluations.models import Year, Classroom, Subject, Student, Lesson, LessonStudent, Goal, Point, Score
from evaluations.services import snapshot_goal
from .services import export_payload, render_excel
from .views import export_filename

NS = {'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}

class ExportTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user=User.objects.create_user('exportteacher', view_all_teachers=False,can_evaluate=True)
        cls.other=User.objects.create_user('otherteacher', view_all_teachers=False,can_evaluate=True)
        cls.year=Year.objects.create(owner=cls.user,name='2026–2027')
        cls.subject=Subject.objects.create(owner=cls.user,year=cls.year,name='Praktijk')
        cls.room=Classroom.objects.create(owner=cls.user,year=cls.year,name='6HV',direction='Haarzorg',grade=6)
        cls.room.subjects.add(cls.subject)
        cls.student=Student.objects.create(classroom=cls.room,name='Eigen Leerling')
        cls.peer=Student.objects.create(classroom=cls.room,name='GEHEIME MEDELEERLING')
        cls.lesson=Lesson.objects.create(owner=cls.user,classroom=cls.room,subject=cls.subject,grade=6,title='Les A',date=date(2026,10,4),feedback='GEHEIME KLASFEEDBACK')
        cls.learner=LessonStudent.objects.create(lesson=cls.lesson,student=cls.student,name=cls.student.name,feedback='Eigen feedback')
        cls.peer_roster=LessonStudent.objects.create(lesson=cls.lesson,student=cls.peer,name=cls.peer.name,feedback='GEHEIME FEEDBACK MEDELEERLING')
        g=Goal.objects.create(owner=cls.user,stage=3,code='DOEL1',title='Veilig werken')

        for i in range(3): Point.objects.create(goal=g,title=f'Punt {i+1}',position=i)
        cls.goal=snapshot_goal(cls.lesson,g)
        points=list(cls.goal.points.all())
        Score.objects.create(point=points[0],learner=cls.learner,value=0)
        Score.objects.create(point=points[1],learner=cls.learner,status='absent',value=None)
        Score.objects.create(point=points[2],learner=cls.learner,value=80)
        Score.objects.create(point=points[0],learner=cls.peer_roster,value=20)

    def setUp(self):
        self.client.force_login(self.user)

    def url(self): return f'/export/?year={self.year.pk}&classroom={self.room.pk}'
    def post(self,mode='class',**extra):
        return self.client.post(self.url(),{'mode':mode,'lessons':[str(self.lesson.pk)],'student':str(self.student.pk) if mode=='student' else '',**extra})

    def test_export_page_and_lesson_link(self):
        self.assertContains(self.client.get(self.url()),'Puntenlijsten om te delen')
        self.assertContains(self.client.get(f'/lessen/{self.lesson.pk}/'),'Excel-export')

    def test_payload_contains_only_selected_student(self):
        payload=export_payload([self.lesson],self.room,self.student)
        body=json.dumps(payload,ensure_ascii=False)
        for secret in ['GEHEIME MEDELEERLING','GEHEIME KLASFEEDBACK','GEHEIME FEEDBACK MEDELEERLING']:
            self.assertNotIn(secret,body)
        self.assertEqual(payload['lessons'][0]['goals'][0]['points'][0]['values'],[0])
        self.assertEqual(payload['lessons'][0]['goals'][0]['points'][1]['values'],[80])

    def test_class_payload_has_all_students_and_feedback(self):
        payload=export_payload([self.lesson],self.room)
        self.assertEqual(len(payload['lessons'][0]['students']),2)
        self.assertEqual(payload['lessons'][0]['classFeedback'],'GEHEIME KLASFEEDBACK')

    def test_empty_rows_and_peer_only_rows_are_filtered_per_student(self):
        from evaluations.models import LessonPoint
        empty=LessonPoint.objects.create(goal=self.goal,title='Leeg punt',position=3)
        peer_only=LessonPoint.objects.create(goal=self.goal,title='Alleen medeleerling',position=4)
        Score.objects.create(point=peer_only,learner=self.peer_roster,value=60)
        personal=export_payload([self.lesson],self.room,self.student)
        personal_points=personal['lessons'][0]['goals'][0]['points']
        self.assertEqual([p['title'] for p in personal_points],['Punt 1','Punt 3'])
        class_points=export_payload([self.lesson],self.room)['lessons'][0]['goals'][0]['points']
        self.assertEqual([p['title'] for p in class_points],['Punt 1','Punt 3','Alleen medeleerling'])
        Score.objects.filter(point__goal=self.goal).delete()
        self.assertEqual(export_payload([self.lesson],self.room,self.student)['lessons'][0]['goals'],[])

    def test_filename_and_export_screen_structure(self):
        self.assertEqual(export_filename(self.year,self.room,[self.lesson]), '2026–2027 - 6HV - Praktijk - Les A - 2026-10-04.xlsx')
        self.assertEqual(export_filename(self.year,self.room,[self.lesson],self.student), '2026–2027 - 6HV - Praktijk - Eigen Leerling - Les A - 2026-10-04.xlsx')
        self.lesson.title='Pad / onveilig: "test"'
        self.assertNotIn('/',export_filename(self.year,self.room,[self.lesson]))
        response=self.client.get(self.url())
        self.assertNotContains(response,'Les wissen')
        self.assertNotContains(response,'data-table-search')
        html=response.content.decode()
        self.assertLess(html.index('1. Soort export'),html.index('2. Selecties'))
        self.assertLess(html.index('2. Selecties'),html.index('3. Gevonden lessen'))

    @patch('exports.views.render_excel',return_value=b'workbook')
    def test_download_is_attachment_and_not_cacheable(self,renderer):
        response=self.post('student')
        self.assertEqual(response.status_code,200)
        self.assertEqual(response['Content-Type'],'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        self.assertIn('attachment;',response['Content-Disposition'])
        self.assertIn('no-store',response['Cache-Control'])
        self.assertEqual(renderer.call_args.args[0]['mode'],'student')

    @patch('exports.views.render_excel')
    def test_other_teacher_cannot_export_class(self,renderer):
        self.client.force_login(self.other)
        self.assertEqual(self.post().status_code,200)  # Shared class is selectable; hidden lessons are rejected by the form.
        renderer.assert_not_called()

    @patch('exports.views.render_excel')
    def test_module_access_can_be_revoked(self,renderer):
        self.user.can_export=False;self.user.save()
        self.assertEqual(self.post().status_code,403)
        renderer.assert_not_called()

    @patch('exports.views.render_excel')
    def test_student_and_lesson_ids_cannot_be_forged(self,renderer):
        self.assertContains(self.post('student',student='999999'),'Selecteer een geldige keuze')
        self.assertContains(self.post(lessons=['999999']),'Selecteer een geldige keuze')
        renderer.assert_not_called()

    @patch('exports.views.render_excel')
    def test_student_required(self,renderer):
        self.assertContains(self.post('student',student=''),'Kies de leerling')
        renderer.assert_not_called()

    def test_date_and_subject_filter(self):
        self.assertNotContains(self.client.get(self.url()+'&from=2026-10-05'),'Les A')
        self.assertContains(self.client.get(self.url()+'&from=2026-10-10&to=2026-10-01'),'Kies een geldige periode')

    def test_changed_lesson_rejected(self):
        Lesson.objects.filter(pk=self.lesson.pk).update(revision=1)
        with self.assertRaisesMessage(ValueError,'tijdens de export gewijzigd'):
            export_payload([self.lesson],self.room,self.student)

    def test_actual_student_xlsx_has_no_peers_and_correct_cached_average(self):
        self.learner.feedback='=HYPERLINK("https://example.invalid","niet uitvoeren")'
        self.learner.save()
        response=self.post('student')
        self.assertEqual(response.status_code,200)
        self.assertEqual(response['Content-Type'],'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        workbook=response.content
        with zipfile.ZipFile(io.BytesIO(workbook)) as archive:
            xml='\n'.join(archive.read(n).decode('utf-8') for n in archive.namelist() if n.endswith('.xml'))
            for secret in ['GEHEIME MEDELEERLING','GEHEIME KLASFEEDBACK','GEHEIME FEEDBACK MEDELEERLING']:
                self.assertNotIn(secret,xml)
            self.assertIn('Eigen Leerling',xml)
            self.assertNotIn('state="hidden"',xml)
            self.assertFalse(any('externalLinks' in n for n in archive.namelist()))
            formulas=[f.text or '' for name in archive.namelist() if name.startswith('xl/worksheets/sheet') and name.endswith('.xml')
                for f in ET.fromstring(archive.read(name)).findall('.//m:f',NS)]
            self.assertFalse(any('HYPERLINK' in f for f in formulas))
            sheet=ET.fromstring(archive.read('xl/worksheets/sheet2.xml'))
            averages=[cell.find('m:v',NS).text for cell in sheet.findall('.//m:c',NS)
                if cell.find('m:f',NS) is not None and 'AVERAGE(' in (cell.find('m:f',NS).text or '')]
            self.assertEqual([float(value) for value in averages],[40])

    def test_actual_class_xlsx_includes_peers(self):
        workbook=render_excel(export_payload([self.lesson],self.room))
        with zipfile.ZipFile(io.BytesIO(workbook)) as archive:
            xml='\n'.join(archive.read(n).decode('utf-8') for n in archive.namelist() if n.endswith('.xml'))
            self.assertIn('GEHEIME MEDELEERLING',xml)
            self.assertIn('GEHEIME KLASFEEDBACK',xml)

    def test_normalized_totals_are_numeric_formulas_with_correct_cache(self):
        workbook=render_excel(export_payload([self.lesson],self.room,self.student))
        with zipfile.ZipFile(io.BytesIO(workbook)) as archive:
            for name in ('xl/worksheets/sheet1.xml','xl/worksheets/sheet2.xml'):
                sheet=ET.fromstring(archive.read(name))
                totals=[c for c in sheet.findall('.//m:c',NS) if c.find('m:f',NS) is not None
                        and '*80)*100' in c.find('m:f',NS).text]
                self.assertTrue(totals)
                self.assertTrue(all(float(c.find('m:v',NS).text)==50 for c in totals))


    def test_print_setup_and_shared_teacher_export(self):
        self.lesson.owner=self.other;self.lesson.save()
        data=export_payload([self.lesson],self.room)
        self.assertEqual(data['lessons'][0]['teacher'],self.other.username)
        with zipfile.ZipFile(io.BytesIO(render_excel(data))) as archive:
            book=ET.fromstring(archive.read('xl/workbook.xml'))
            self.assertEqual(book.find('m:sheets/m:sheet',NS).get('name'),'Klasoverzicht evaluaties')
            titles=[n.text for n in book.findall('m:definedNames/m:definedName',NS) if n.get('name')=='_xlnm.Print_Titles']
            self.assertEqual(len(titles),3)
            for name in ['sheet1','sheet2','sheet3']:
                sheet=ET.fromstring(archive.read(f'xl/worksheets/{name}.xml'))
                setup=sheet.find('m:pageSetup',NS)
                self.assertEqual(setup.get('orientation'),'landscape')
                self.assertEqual(setup.get('paperSize'),'9')
                self.assertEqual(setup.get('fitToHeight'),'0')
                self.assertIn('&A',sheet.find('m:headerFooter/m:oddHeader',NS).text)
                footer=sheet.find('m:headerFooter/m:oddFooter',NS).text
                self.assertIn(self.other.username,footer)
                self.assertIn('&P',footer)
                self.assertIsNone(sheet.find('m:colBreaks',NS))
