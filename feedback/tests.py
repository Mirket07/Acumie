from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from feedback.models import Feedback, FeedbackLike, FeedbackComment, FeedbackRequest
from courses.models import Course, Assessment
import json

User = get_user_model()

class FeedbackBaseSetup(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            username='studentuser', 
            email='student@test.com', 
            password='testpassword', 
            role='STUDENT'
        )
        self.instructor = User.objects.create_user(
            username='instructoruser', 
            email='instructor@test.com', 
            password='testpassword', 
            role='INSTRUCTOR'
        )
        self.client = Client()
        
        self.course = Course.objects.create(
            name="Test Course", 
            code="CS101"
        )
        self.assessment = Assessment.objects.create(
            course=self.course, 
            title="Midterm Exam", 
            type='EXAM'
        )
        
        self.feedback1 = Feedback.objects.create(
            feedback_text="Great course, needs more interaction.",
            course=self.course
        )
        self.feedback2 = Feedback.objects.create(
            feedback_text="Another general feedback.",
            course=None
        )
        
        self.feed_url = reverse('feedback:feed')
        self.submit_url = reverse('feedback:submit')
        self.toggle_like_url = reverse('feedback:toggle_like', args=[self.feedback1.id])
        self.add_comment_url = reverse('feedback:add_comment', args=[self.feedback1.id])
        self.request_feedback_url = reverse('feedback:request_feedback', args=[self.assessment.id])

class FeedbackModelTest(FeedbackBaseSetup):
    
    def test_feedback_creation(self):
        feedback = Feedback.objects.get(id=self.feedback1.id)
        self.assertTrue(isinstance(feedback, Feedback))
        self.assertEqual(feedback.feedback_text, "Great course, needs more interaction.")
        self.assertEqual(feedback.course.code, "CS101")
        self.assertEqual(feedback.likes_count, 0)

    def test_feedback_request_unique_constraint(self):
        FeedbackRequest.objects.create(student=self.student, assessment=self.assessment)
        
        with self.assertRaises(Exception):
            FeedbackRequest.objects.create(student=self.student, assessment=self.assessment)

    def test_feedback_like_creation(self):
        FeedbackLike.objects.create(user=self.student, feedback=self.feedback1)
        self.assertEqual(FeedbackLike.objects.count(), 1)
        self.assertEqual(FeedbackLike.objects.filter(feedback=self.feedback1).count(), 1)

class FeedbackViewTest(FeedbackBaseSetup):

    def test_feed_view_requires_login(self):
        response = self.client.get(self.feed_url)
        self.assertEqual(response.status_code, 302)

    def test_feed_view_logged_in_access(self):
        self.client.force_login(self.student)
        response = self.client.get(self.feed_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'feedback/feed.html')
        self.assertContains(response, self.feedback1.feedback_text)
        self.assertContains(response, self.feedback2.feedback_text)
        
    def test_feedback_submission(self):
        self.client.force_login(self.student)
        new_feedback_data = {
            'feedback_text': 'This is a new submission test.',
            'course': self.course.id,
        }
        response = self.client.post(self.submit_url, new_feedback_data, follow=True) 
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Feedback.objects.filter(feedback_text='This is a new submission test.').exists())

    def test_toggle_like_add(self):
        self.client.force_login(self.student)
        response = self.client.post(self.toggle_like_url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['liked'])
        self.assertEqual(data['likes_count'], 1)
        self.assertTrue(FeedbackLike.objects.filter(user=self.student, feedback=self.feedback1).exists())
        self.assertEqual(Feedback.objects.get(id=self.feedback1.id).likes_count, 1)

    def test_toggle_like_remove(self):
        FeedbackLike.objects.create(user=self.student, feedback=self.feedback1)
        self.feedback1.likes_count = 1
        self.feedback1.save()
        
        self.client.force_login(self.student)
        response = self.client.post(self.toggle_like_url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data['liked'])
        self.assertEqual(data['likes_count'], 0)
        self.assertFalse(FeedbackLike.objects.filter(user=self.student, feedback=self.feedback1).exists())
        self.assertEqual(Feedback.objects.get(id=self.feedback1.id).likes_count, 0)
        
    def test_add_comment_success(self):
        self.client.force_login(self.student)
        comment_data = {
            'comment_text': 'I agree with this feedback!',
        }
        response = self.client.post(self.add_comment_url, comment_data, follow=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(FeedbackComment.objects.filter(comment_text='I agree with this feedback!').exists())
        comment = FeedbackComment.objects.first()
        self.assertEqual(comment.user, self.student)
        self.assertEqual(comment.feedback, self.feedback1)

    def test_request_feedback_by_student(self):
        self.client.force_login(self.student)
        response = self.client.post(self.request_feedback_url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
        self.assertTrue(FeedbackRequest.objects.filter(student=self.student, assessment=self.assessment).exists())

    def test_request_feedback_by_instructor_denied(self):
        self.client.force_login(self.instructor)
        response = self.client.post(self.request_feedback_url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'error')
        self.assertFalse(FeedbackRequest.objects.filter(student=self.instructor).exists())

    def test_request_feedback_duplicate(self):
        FeedbackRequest.objects.create(student=self.student, assessment=self.assessment)
        
        self.client.force_login(self.student)
        response = self.client.post(self.request_feedback_url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'warning')
        self.assertEqual(FeedbackRequest.objects.count(), 1)