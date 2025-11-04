from django.test import TestCase
from .models import Grade
from django.urls import reverse

class GradeAverageViewTest(TestCase):
    def setUp(self):
        Grade.objects.create(score=90)
        Grade.objects.create(score=80)
        Grade.objects.create(score=70)

    def test_average_view(self):
        response = self.client.get(reverse('average'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "80.0")
