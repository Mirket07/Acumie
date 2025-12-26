from django.test import TestCase
from django.contrib.auth.models import User
from courses.models import Course
from .models import Report


class ReportModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='john_doe', password='testpass123')
        self.course = Course.objects.create(name='Mathematics 101', code='MTH101')
        self.report = Report.objects.create(
            student=self.user,
            course=self.course,
            assignment_score=85.5,
            exam_score=90.0,
            attendance_rate=95.0,
            overall_grade='A',
            teacher_comments='Excellent performance!'
        )

    def test_report_creation(self):
        self.assertEqual(self.report.student.username, 'john_doe')
        self.assertEqual(self.report.course.name, 'Mathematics 101')
        self.assertEqual(self.report.overall_grade, 'A')

    def test_report_average_calculation(self):
        avg = self.report.calculate_average()
        self.assertEqual(avg, 87.75) 

    def test_string_representation(self):
        expected_str = f"{self.user.username} - {self.course.name}"
        self.assertEqual(str(self.report), expected_str)

    def test_update_report(self):
        self.report.overall_grade = 'A+'
        self.report.save()
        self.assertEqual(Report.objects.get(id=self.report.id).overall_grade, 'A+')

    def test_delete_report(self):
        report_id = self.report.id
        self.report.delete()
        self.assertFalse(Report.objects.filter(id=report_id).exists())
