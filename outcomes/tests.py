from django.test import TestCase
from outcomes.models import ProgramOutcome

class OutcomeModelTest(TestCase):
    def setUp(self):
        self.outcome = ProgramOutcome.objects.create(
            code="PO-01",
            title="Test Outcome",
            description="Sample description"
        )

    def test_outcome_created(self):
        self.assertEqual(self.outcome.title, "Test Outcome")
        self.assertEqual(self.outcome.description, "Sample description")
        self.assertEqual(self.outcome.code, "PO-01")

    def test_string_representation(self):
        self.assertEqual(str(self.outcome), "PO-01 - Test Outcome")

    def test_update_outcome(self):
        self.outcome.title = "Updated Title"
        self.outcome.save()
        self.outcome.refresh_from_db()
        self.assertEqual(self.outcome.title, "Updated Title")

    def test_delete_outcome(self):
        pk = self.outcome.pk
        self.outcome.delete()
        self.assertFalse(ProgramOutcome.objects.filter(pk=pk).exists())