"""Tests for the Flask web application."""
import unittest
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import app, warehouses, next_id


class TestApp(unittest.TestCase):
    """Test cases for the Flask web application."""

    def setUp(self):
        """Set up test client and clear warehouses."""
        global warehouses, next_id
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()
        warehouses.clear()
        # Reset next_id by modifying the module variable
        import app as app_module
        app_module.next_id = 1

    def test_index_page_loads(self):
        """Test that the index page loads successfully."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Warehouse Manager', response.data)

    def test_create_warehouse_page_loads(self):
        """Test that the create warehouse page loads."""
        response = self.client.get('/warehouse/new')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Create New Warehouse', response.data)

    def test_create_warehouse_success(self):
        """Test creating a warehouse successfully."""
        response = self.client.post('/warehouse/new', data={
            'name': 'Test Warehouse',
            'capacity': '100',
            'initial_balance': '50'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Warehouse', response.data)
        self.assertIn(b'created successfully', response.data)

    def test_create_warehouse_empty_name(self):
        """Test creating a warehouse with empty name fails."""
        response = self.client.post('/warehouse/new', data={
            'name': '',
            'capacity': '100',
            'initial_balance': '0'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Warehouse name is required', response.data)

    def test_create_warehouse_invalid_capacity(self):
        """Test creating a warehouse with invalid capacity fails."""
        response = self.client.post('/warehouse/new', data={
            'name': 'Test',
            'capacity': '-10',
            'initial_balance': '0'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Capacity must be a positive number', response.data)

    def test_view_warehouse(self):
        """Test viewing a warehouse."""
        # First create a warehouse
        self.client.post('/warehouse/new', data={
            'name': 'View Test',
            'capacity': '100',
            'initial_balance': '25'
        })
        response = self.client.get('/warehouse/1')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'View Test', response.data)

    def test_view_nonexistent_warehouse(self):
        """Test viewing a nonexistent warehouse redirects."""
        response = self.client.get('/warehouse/999', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Warehouse not found', response.data)

    def test_edit_warehouse(self):
        """Test editing a warehouse name."""
        # First create a warehouse
        self.client.post('/warehouse/new', data={
            'name': 'Original Name',
            'capacity': '100',
            'initial_balance': '0'
        })
        response = self.client.post('/warehouse/1/edit', data={
            'name': 'New Name'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'New Name', response.data)
        self.assertIn(b'updated successfully', response.data)

    def test_delete_warehouse(self):
        """Test deleting a warehouse."""
        # First create a warehouse
        self.client.post('/warehouse/new', data={
            'name': 'To Delete',
            'capacity': '100',
            'initial_balance': '0'
        })
        response = self.client.post('/warehouse/1/delete', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'deleted successfully', response.data)

    def test_add_content(self):
        """Test adding content to a warehouse."""
        # First create a warehouse
        self.client.post('/warehouse/new', data={
            'name': 'Add Test',
            'capacity': '100',
            'initial_balance': '0'
        })
        response = self.client.post('/warehouse/1/add', data={
            'amount': '50'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Added', response.data)

    def test_add_content_exceeds_capacity(self):
        """Test adding more content than capacity allows."""
        # First create a warehouse
        self.client.post('/warehouse/new', data={
            'name': 'Overflow Test',
            'capacity': '100',
            'initial_balance': '90'
        })
        response = self.client.post('/warehouse/1/add', data={
            'amount': '50'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'limited by capacity', response.data)

    def test_remove_content(self):
        """Test removing content from a warehouse."""
        # First create a warehouse with some content
        self.client.post('/warehouse/new', data={
            'name': 'Remove Test',
            'capacity': '100',
            'initial_balance': '50'
        })
        response = self.client.post('/warehouse/1/remove', data={
            'amount': '25'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Removed', response.data)

    def test_remove_content_exceeds_balance(self):
        """Test removing more content than available."""
        # First create a warehouse
        self.client.post('/warehouse/new', data={
            'name': 'Empty Test',
            'capacity': '100',
            'initial_balance': '20'
        })
        response = self.client.post('/warehouse/1/remove', data={
            'amount': '50'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'was available', response.data)


if __name__ == '__main__':
    unittest.main()
