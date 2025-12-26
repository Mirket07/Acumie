from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from courses.models import Course, Assessment 
from .models import Grade

User = get_user_model()

class GradeDashboardViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='teststudent', password='testpass123', role='STUDENT')

        self.course = Course.objects.create(
            code="CSE321", 
            title="Software Engineering", 
            ects_credit=5.0
        )

        self.assessment = Assessment.objects.create(
            type="MIDTERM", 
            course=self.course,
            weight_percentage=30.0
        )
        
        self.url = reverse('grades:dashboard')

    def test_dashboard_view_access(self):
        Grade.objects.create(score_percentage=90.0, student=self.user, assessment=self.assessment)
        Grade.objects.create(score_percentage=80.0, student=self.user, assessment=self.assessment)
        Grade.objects.create(score_percentage=70.0, student=self.user, assessment=self.assessment)

        self.client.force_login(self.user)

        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "teststudent")