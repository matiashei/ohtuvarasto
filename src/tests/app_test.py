"""Tests for the Flask web application."""
import unittest
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import app, warehouses, next_id, next_item_id


class TestApp(unittest.TestCase):
    """Test cases for the Flask web application."""

    def setUp(self):
        """Set up test client and clear warehouses."""
        global warehouses, next_id, next_item_id
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()
        warehouses.clear()
        # Reset IDs by modifying the module variable
        import app as app_module
        app_module.next_id = 1
        app_module.next_item_id = 1

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
            'capacity': '100'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Warehouse', response.data)
        self.assertIn(b'created successfully', response.data)

    def test_create_warehouse_empty_name(self):
        """Test creating a warehouse with empty name fails."""
        response = self.client.post('/warehouse/new', data={
            'name': '',
            'capacity': '100'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Warehouse name is required', response.data)

    def test_create_warehouse_invalid_capacity(self):
        """Test creating a warehouse with invalid capacity fails."""
        response = self.client.post('/warehouse/new', data={
            'name': 'Test',
            'capacity': '-10'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Capacity must be a positive number', response.data)

    def test_view_warehouse(self):
        """Test viewing a warehouse."""
        # First create a warehouse
        self.client.post('/warehouse/new', data={
            'name': 'View Test',
            'capacity': '100'
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
            'capacity': '100'
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
            'capacity': '100'
        })
        response = self.client.post('/warehouse/1/delete', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'deleted successfully', response.data)

    def test_add_item(self):
        """Test adding an item to a warehouse."""
        # First create a warehouse
        self.client.post('/warehouse/new', data={
            'name': 'Add Test',
            'capacity': '100'
        })
        response = self.client.post('/warehouse/1/add', data={
            'item_name': 'Beer',
            'quantity': '50',
            'unit': 'liters'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Added', response.data)
        self.assertIn(b'Beer', response.data)

    def test_add_item_exceeds_capacity(self):
        """Test adding an item that exceeds capacity fails."""
        # First create a warehouse with small capacity
        self.client.post('/warehouse/new', data={
            'name': 'Overflow Test',
            'capacity': '1'  # 1 m³
        })
        # Try to add 2000 liters (2 m³)
        response = self.client.post('/warehouse/1/add', data={
            'item_name': 'Water',
            'quantity': '2000',
            'unit': 'liters'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Not enough space', response.data)

    def test_add_multiple_items(self):
        """Test adding multiple different items."""
        # Create warehouse
        self.client.post('/warehouse/new', data={
            'name': 'Multi Item Test',
            'capacity': '100'
        })
        # Add beer
        self.client.post('/warehouse/1/add', data={
            'item_name': 'Beer',
            'quantity': '100',
            'unit': 'units'
        })
        # Add wine
        response = self.client.post('/warehouse/1/add', data={
            'item_name': 'Wine',
            'quantity': '50',
            'unit': 'liters'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Beer', response.data)
        self.assertIn(b'Wine', response.data)

    def test_update_item_quantity(self):
        """Test updating item quantity."""
        # Create warehouse and add item
        self.client.post('/warehouse/new', data={
            'name': 'Update Test',
            'capacity': '100'
        })
        self.client.post('/warehouse/1/add', data={
            'item_name': 'Beer',
            'quantity': '50',
            'unit': 'liters'
        })
        # Update quantity
        response = self.client.post('/warehouse/1/item/1/update', data={
            'quantity': '75'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Updated', response.data)

    def test_delete_item(self):
        """Test removing an item from warehouse."""
        # Create warehouse and add item
        self.client.post('/warehouse/new', data={
            'name': 'Delete Item Test',
            'capacity': '100'
        })
        self.client.post('/warehouse/1/add', data={
            'item_name': 'Beer',
            'quantity': '50',
            'unit': 'liters'
        })
        response = self.client.post(
            '/warehouse/1/item/1/delete',
            follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Removed', response.data)

    def test_different_units(self):
        """Test items with different units."""
        # Create warehouse
        self.client.post('/warehouse/new', data={
            'name': 'Units Test',
            'capacity': '10'  # 10 m³
        })
        # Add in cubic meters
        self.client.post('/warehouse/1/add', data={
            'item_name': 'Bulk Grain',
            'quantity': '2',
            'unit': 'm3'
        })
        # Add in liters
        self.client.post('/warehouse/1/add', data={
            'item_name': 'Water',
            'quantity': '1000',
            'unit': 'liters'
        })
        # Add in units
        response = self.client.post('/warehouse/1/add', data={
            'item_name': 'Bottles',
            'quantity': '500',
            'unit': 'units'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Bulk Grain', response.data)
        self.assertIn(b'Water', response.data)
        self.assertIn(b'Bottles', response.data)


if __name__ == '__main__':
    unittest.main()
