from django.test import TestCase
from courses.models import Course
from .models import Report
from django.contrib.auth import get_user_model

User = get_user_model()

class ReportModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='john_doe', password='testpass123')
        self.course = Course.objects.create(title='Mathematics 101', code='MTH101', ects_credit=4)
        
        self.report = Report.objects.create(
            student=self.user,
            course=self.course,
            grade='AA',
            comments='Excellent performance!'
        )

    def test_report_creation(self):
        self.assertEqual(self.report.student.username, 'john_doe')
        self.assertEqual(self.report.course.title, 'Mathematics 101')
        self.assertEqual(self.report.grade, 'AA')

    def test_string_representation(self):
        expected_str = f"john_doe - Mathematics 101 (AA)"
        self.assertEqual(str(self.report), expected_str)

    def test_update_report(self):
        self.report.grade = 'BA'
        self.report.save()
        self.assertEqual(Report.objects.get(id=self.report.id).grade, 'BA')

    def test_delete_report(self):
        report_id = self.report.id
        self.report.delete()
        self.assertFalse(Report.objects.filter(id=report_id).exists())