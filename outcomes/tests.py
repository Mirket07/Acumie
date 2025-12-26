from django.test import TestCase
from outcomes.models import ProgramOutcome, LearningOutcome

class OutcomeModelTest(TestCase):
    def setUp(self):
        self.outcome = ProgramOutcome.objects.create(
            title="Test Outcome",
            description="Sample description",
            score=90
        )

    def test_outcome_created(self):
        self.assertEqual(self.outcome.title, "Test Outcome")
        self.assertEqual(self.outcome.description, "Sample description")
        self.assertEqual(self.outcome.score, 90)

    def test_string_representation(self):
        self.assertEqual(str(self.outcome), self.outcome.title)

    def test_update_outcome(self):
        self.outcome.score = 95
        self.outcome.save()
        self.outcome.refresh_from_db()
        self.assertEqual(self.outcome.score, 95)

    def test_delete_outcome(self):
        pk = self.outcome.pk
        self.outcome.delete()
        self.assertFalse(ProgramOutcome.objects.filter(pk=pk).exists())
