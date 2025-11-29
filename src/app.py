"""Flask web application for warehouse management."""
import os
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', os.urandom(24))

# In-memory storage for warehouses
warehouses: dict[int, dict] = {}
next_id = 1
next_item_id = 1

# Unit types and their conversion to cubic meters
UNIT_TYPES = {
    'm3': {'name': 'Cubic Meters (m³)', 'to_m3': 1.0},
    'liters': {'name': 'Liters (L)', 'to_m3': 0.001},
    'units': {'name': 'Units/Bottles', 'to_m3': 0.001}  # Approx 1L per unit
}


def get_next_id():
    """Get the next available warehouse ID."""
    global next_id
    current_id = next_id
    next_id += 1
    return current_id


def get_next_item_id():
    """Get the next available item ID."""
    global next_item_id
    current_id = next_item_id
    next_item_id += 1
    return current_id


def calculate_used_space(warehouse):
    """Calculate total used space in m³ from all items."""
    total = 0.0
    for item in warehouse.get('stored_items', {}).values():
        unit_info = UNIT_TYPES.get(item['unit'], UNIT_TYPES['m3'])
        total += item['quantity'] * unit_info['to_m3']
    return total


def calculate_available_space(warehouse):
    """Calculate available space in m³."""
    return warehouse['capacity_m3'] - calculate_used_space(warehouse)


@app.route('/')
def index():
    """Display all warehouses."""
    # Pre-calculate space info for each warehouse
    warehouse_info = {}
    for wid, w in warehouses.items():
        warehouse_info[wid] = {
            'used_space': calculate_used_space(w),
            'available_space': calculate_available_space(w)
        }
    return render_template(
        'index.html',
        warehouses=warehouses,
        warehouse_info=warehouse_info
    )


@app.route('/warehouse/new', methods=['GET', 'POST'])
def create_warehouse():
    """Create a new warehouse."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        try:
            capacity = float(request.form.get('capacity', 0))
        except ValueError:
            flash('Capacity must be a valid number', 'error')
            return render_template('create_warehouse.html')

        if not name:
            flash('Warehouse name is required', 'error')
            return render_template('create_warehouse.html')

        if capacity <= 0:
            flash('Capacity must be a positive number', 'error')
            return render_template('create_warehouse.html')

        warehouse_id = get_next_id()
        warehouses[warehouse_id] = {
            'id': warehouse_id,
            'name': name,
            'capacity_m3': capacity,
            'stored_items': {}  # Dictionary of items in the warehouse
        }
        flash(f'Warehouse "{name}" created successfully', 'success')
        return redirect(url_for('index'))

    return render_template('create_warehouse.html')


@app.route('/warehouse/<int:warehouse_id>')
def view_warehouse(warehouse_id):
    """View a specific warehouse."""
    warehouse = warehouses.get(warehouse_id)
    if not warehouse:
        flash('Warehouse not found', 'error')
        return redirect(url_for('index'))
    used_space = calculate_used_space(warehouse)
    available_space = calculate_available_space(warehouse)
    return render_template(
        'view_warehouse.html',
        warehouse=warehouse,
        used_space=used_space,
        available_space=available_space,
        unit_types=UNIT_TYPES
    )


@app.route('/warehouse/<int:warehouse_id>/edit', methods=['GET', 'POST'])
def edit_warehouse(warehouse_id):
    """Edit a warehouse."""
    warehouse = warehouses.get(warehouse_id)
    if not warehouse:
        flash('Warehouse not found', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            flash('Warehouse name is required', 'error')
            return render_template('edit_warehouse.html', warehouse=warehouse)

        warehouse['name'] = name
        flash(f'Warehouse "{name}" updated successfully', 'success')
        return redirect(url_for('view_warehouse', warehouse_id=warehouse_id))

    return render_template('edit_warehouse.html', warehouse=warehouse)


@app.route('/warehouse/<int:warehouse_id>/delete', methods=['POST'])
def delete_warehouse(warehouse_id):
    """Delete a warehouse."""
    warehouse = warehouses.get(warehouse_id)
    if not warehouse:
        flash('Warehouse not found', 'error')
        return redirect(url_for('index'))

    name = warehouse['name']
    del warehouses[warehouse_id]
    flash(f'Warehouse "{name}" deleted successfully', 'success')
    return redirect(url_for('index'))


@app.route('/warehouse/<int:warehouse_id>/add', methods=['POST'])
def add_item(warehouse_id):
    """Add an item to a warehouse."""
    warehouse = warehouses.get(warehouse_id)
    if not warehouse:
        flash('Warehouse not found', 'error')
        return redirect(url_for('index'))

    item_name = request.form.get('item_name', '').strip()
    unit = request.form.get('unit', 'm3')

    if not item_name:
        flash('Item name is required', 'error')
        return redirect(url_for('view_warehouse', warehouse_id=warehouse_id))

    try:
        quantity = float(request.form.get('quantity', 0))
    except ValueError:
        flash('Quantity must be a valid number', 'error')
        return redirect(url_for('view_warehouse', warehouse_id=warehouse_id))

    if quantity <= 0:
        flash('Quantity must be a positive number', 'error')
        return redirect(url_for('view_warehouse', warehouse_id=warehouse_id))

    if unit not in UNIT_TYPES:
        flash('Invalid unit type', 'error')
        return redirect(url_for('view_warehouse', warehouse_id=warehouse_id))

    # Calculate space needed in m³
    unit_info = UNIT_TYPES[unit]
    space_needed = quantity * unit_info['to_m3']
    available_space = calculate_available_space(warehouse)

    if space_needed > available_space:
        flash(
            f'Not enough space. Need {space_needed:.4f} m³, '
            f'available {available_space:.4f} m³',
            'error'
        )
        return redirect(url_for('view_warehouse', warehouse_id=warehouse_id))

    item_id = get_next_item_id()
    warehouse['stored_items'][item_id] = {
        'id': item_id,
        'name': item_name,
        'quantity': quantity,
        'unit': unit
    }

    flash(f'Added {quantity:.2f} {unit_info["name"]} of "{item_name}"', 'success')
    return redirect(url_for('view_warehouse', warehouse_id=warehouse_id))


@app.route('/warehouse/<int:warehouse_id>/item/<int:item_id>/update',
           methods=['POST'])
def update_item(warehouse_id, item_id):
    """Update item quantity in a warehouse."""
    warehouse = warehouses.get(warehouse_id)
    if not warehouse:
        flash('Warehouse not found', 'error')
        return redirect(url_for('index'))

    item = warehouse['stored_items'].get(item_id)
    if not item:
        flash('Item not found', 'error')
        return redirect(url_for('view_warehouse', warehouse_id=warehouse_id))

    try:
        new_quantity = float(request.form.get('quantity', 0))
    except ValueError:
        flash('Quantity must be a valid number', 'error')
        return redirect(url_for('view_warehouse', warehouse_id=warehouse_id))

    if new_quantity < 0:
        flash('Quantity cannot be negative', 'error')
        return redirect(url_for('view_warehouse', warehouse_id=warehouse_id))

    # Calculate space difference
    unit_info = UNIT_TYPES[item['unit']]
    old_space = item['quantity'] * unit_info['to_m3']
    new_space = new_quantity * unit_info['to_m3']
    space_diff = new_space - old_space

    if space_diff > 0:
        available = calculate_available_space(warehouse)
        if space_diff > available:
            flash(
                f'Not enough space. Need {space_diff:.4f} m³ more, '
                f'available {available:.4f} m³',
                'error'
            )
            return redirect(url_for('view_warehouse', warehouse_id=warehouse_id))

    item['quantity'] = new_quantity
    flash(f'Updated "{item["name"]}" to {new_quantity:.2f}', 'success')
    return redirect(url_for('view_warehouse', warehouse_id=warehouse_id))


@app.route('/warehouse/<int:warehouse_id>/item/<int:item_id>/delete',
           methods=['POST'])
def delete_item(warehouse_id, item_id):
    """Remove an item from a warehouse."""
    warehouse = warehouses.get(warehouse_id)
    if not warehouse:
        flash('Warehouse not found', 'error')
        return redirect(url_for('index'))

    item = warehouse['stored_items'].get(item_id)
    if not item:
        flash('Item not found', 'error')
        return redirect(url_for('view_warehouse', warehouse_id=warehouse_id))

    item_name = item['name']
    del warehouse['stored_items'][item_id]
    flash(f'Removed "{item_name}" from warehouse', 'success')
    return redirect(url_for('view_warehouse', warehouse_id=warehouse_id))


if __name__ == '__main__':
    debug_mode = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)
