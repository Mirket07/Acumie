from django.test import TestCase
from django.db.utils import IntegrityError
from decimal import Decimal
from .models import Course


class CourseModelTest(TestCase):
    def setUp(self):
        self.course = Course.objects.create(
            title="Introduction to Programming",
            code="CS101",
            ects_credit=Decimal('4.00')
        )

    def test_course_creation(self):
        self.assertEqual(self.course.title, "Introduction to Programming")
        self.assertEqual(self.course.code, "CS101")
        self.assertEqual(self.course.ects_credit, Decimal('4.00'))

    def test_string_representation(self):
        expected = "CS101 - Introduction to Programming"
        self.assertEqual(str(self.course), expected)

    def test_unique_course_code(self):
        with self.assertRaises(IntegrityError):
            Course.objects.create(
                title="Another Intro Course",
                code="CS101",
                ects_credit=Decimal('3.00')
            )

    def test_course_update(self):
        self.course.title = "Intro to Computer Science"
        self.course.save()
        updated = Course.objects.get(id=self.course.id)
        self.assertEqual(updated.title, "Intro to Computer Science")

    def test_course_delete(self):
        course_id = self.course.id
        self.course.delete()
        self.assertFalse(Course.objects.filter(id=course_id).exists())
