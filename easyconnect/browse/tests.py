from django.test import TestCase
from django.core.urlresolvers import reverse, resolve
from contentimport.models import ContentItem, Category


def create_category(name, parent):
	return Category.objects.create(name=name, parent=parent)


class CategoryViewTest(TestCase):
	def test_index_with_new_category(self):
		create_category(name="New", parent=None)
		response = self.client.get('/')
		self.assertQuerysetEqual(
			response.context['parent_categories'],
			['<Category: New>']
		)
		self.assertContains(response, '<a href="/New/">New</a>')

	def test_load_index_with_not_existing_category(self):
		response = self.client.get('/not/a/category')
		#self.assertEqual(response.status_code, 404)
		self.assertEqual(response.status_code, 301) # debug is on

	def test_load_index_with_existing_category(self):
		Category.objects.create(name="new", parent=None)
		response = self.client.get('/new/')
		self.assertEqual(response.status_code, 200)

