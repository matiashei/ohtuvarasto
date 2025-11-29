"""Flask web application for warehouse management."""
import os
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', os.urandom(24))

# In-memory storage for warehouses
warehouses: dict[int, dict] = {}
next_id = 1
next_item_id = 1

# Secondary unit types (informational only, don't affect storage space)
SECONDARY_UNITS = {
    'liters': {'name': 'Liters (L)'},
    'kg': {'name': 'Kilograms (kg)'},
    'units': {'name': 'Units/Bottles'}
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
        total += item['space_m3']
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
        secondary_units=SECONDARY_UNITS
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
    secondary_unit = request.form.get('secondary_unit', 'liters')

    if not item_name:
        flash('Item name is required', 'error')
        return redirect(url_for('view_warehouse', warehouse_id=warehouse_id))

    # Parse space in cubic meters (required)
    try:
        space_m3 = float(request.form.get('space_m3', 0))
    except ValueError:
        flash('Space (m³) must be a valid number', 'error')
        return redirect(url_for('view_warehouse', warehouse_id=warehouse_id))

    if space_m3 <= 0:
        flash('Space (m³) must be a positive number', 'error')
        return redirect(url_for('view_warehouse', warehouse_id=warehouse_id))

    # Parse secondary quantity (optional informational value)
    try:
        secondary_qty = float(request.form.get('secondary_qty', 0))
    except ValueError:
        secondary_qty = 0

    if secondary_unit not in SECONDARY_UNITS:
        secondary_unit = 'liters'

    available_space = calculate_available_space(warehouse)

    if space_m3 > available_space:
        flash(
            f'Not enough space. Need {space_m3:.4f} m³, '
            f'available {available_space:.4f} m³',
            'error'
        )
        return redirect(url_for('view_warehouse', warehouse_id=warehouse_id))

    item_id = get_next_item_id()
    warehouse['stored_items'][item_id] = {
        'id': item_id,
        'name': item_name,
        'space_m3': space_m3,
        'secondary_qty': secondary_qty,
        'secondary_unit': secondary_unit
    }

    unit_name = SECONDARY_UNITS[secondary_unit]['name']
    if secondary_qty > 0:
        flash(
            f'Added "{item_name}" ({space_m3:.4f} m³, '
            f'{secondary_qty:.2f} {unit_name})',
            'success'
        )
    else:
        flash(f'Added "{item_name}" ({space_m3:.4f} m³)', 'success')
    return redirect(url_for('view_warehouse', warehouse_id=warehouse_id))


@app.route('/warehouse/<int:warehouse_id>/item/<int:item_id>/update',
           methods=['POST'])
def update_item(warehouse_id, item_id):
    """Update item space and secondary quantity in a warehouse."""
    warehouse = warehouses.get(warehouse_id)
    if not warehouse:
        flash('Warehouse not found', 'error')
        return redirect(url_for('index'))

    item = warehouse['stored_items'].get(item_id)
    if not item:
        flash('Item not found', 'error')
        return redirect(url_for('view_warehouse', warehouse_id=warehouse_id))

    try:
        new_space_m3 = float(request.form.get('space_m3', 0))
    except ValueError:
        flash('Space (m³) must be a valid number', 'error')
        return redirect(url_for('view_warehouse', warehouse_id=warehouse_id))

    if new_space_m3 < 0:
        flash('Space (m³) cannot be negative', 'error')
        return redirect(url_for('view_warehouse', warehouse_id=warehouse_id))

    try:
        new_secondary_qty = float(request.form.get('secondary_qty', 0))
    except ValueError:
        new_secondary_qty = item.get('secondary_qty', 0) if 'secondary_qty' in item else 0

    # Calculate space difference
    old_space = item['space_m3']
    space_diff = new_space_m3 - old_space

    if space_diff > 0:
        available = calculate_available_space(warehouse)
        if space_diff > available:
            flash(
                f'Not enough space. Need {space_diff:.4f} m³ more, '
                f'available {available:.4f} m³',
                'error'
            )
            return redirect(url_for('view_warehouse', warehouse_id=warehouse_id))

    item['space_m3'] = new_space_m3
    item['secondary_qty'] = new_secondary_qty
    flash(f'Updated "{item["name"]}"', 'success')
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
