"""Flask web application for warehouse management."""
import os
from flask import Flask, render_template, request, redirect, url_for, flash
from varasto import Varasto

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', os.urandom(24))

# In-memory storage for warehouses
warehouses: dict[int, dict] = {}
next_id = 1


def get_next_id():
    """Get the next available warehouse ID."""
    global next_id
    current_id = next_id
    next_id += 1
    return current_id


@app.route('/')
def index():
    """Display all warehouses."""
    return render_template('index.html', warehouses=warehouses)


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

        try:
            initial_balance = float(request.form.get('initial_balance', 0))
        except ValueError:
            flash('Initial balance must be a valid number', 'error')
            return render_template('create_warehouse.html')

        if not name:
            flash('Warehouse name is required', 'error')
            return render_template('create_warehouse.html')

        if capacity <= 0:
            flash('Capacity must be a positive number', 'error')
            return render_template('create_warehouse.html')

        warehouse_id = get_next_id()
        varasto = Varasto(capacity, initial_balance)
        warehouses[warehouse_id] = {
            'id': warehouse_id,
            'name': name,
            'varasto': varasto
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
    return render_template('view_warehouse.html', warehouse=warehouse)


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
def add_content(warehouse_id):
    """Add content to a warehouse."""
    warehouse = warehouses.get(warehouse_id)
    if not warehouse:
        flash('Warehouse not found', 'error')
        return redirect(url_for('index'))

    try:
        amount = float(request.form.get('amount', 0))
    except ValueError:
        flash('Amount must be a valid number', 'error')
        return redirect(url_for('view_warehouse', warehouse_id=warehouse_id))

    if amount <= 0:
        flash('Amount must be a positive number', 'error')
        return redirect(url_for('view_warehouse', warehouse_id=warehouse_id))

    varasto = warehouse['varasto']
    space_available = varasto.paljonko_mahtuu()

    if amount > space_available:
        varasto.lisaa_varastoon(amount)  # Will add what fits
        msg = (f'Added {space_available:.2f} '
               f'(requested {amount:.2f}, limited by capacity)')
        flash(msg, 'warning')
    else:
        varasto.lisaa_varastoon(amount)
        flash(f'Added {amount:.2f} to warehouse', 'success')

    return redirect(url_for('view_warehouse', warehouse_id=warehouse_id))


@app.route('/warehouse/<int:warehouse_id>/remove', methods=['POST'])
def remove_content(warehouse_id):
    """Remove content from a warehouse."""
    warehouse = warehouses.get(warehouse_id)
    if not warehouse:
        flash('Warehouse not found', 'error')
        return redirect(url_for('index'))

    try:
        amount = float(request.form.get('amount', 0))
    except ValueError:
        flash('Amount must be a valid number', 'error')
        return redirect(url_for('view_warehouse', warehouse_id=warehouse_id))

    if amount <= 0:
        flash('Amount must be a positive number', 'error')
        return redirect(url_for('view_warehouse', warehouse_id=warehouse_id))

    varasto = warehouse['varasto']
    actual_removed = varasto.ota_varastosta(amount)

    if actual_removed < amount:
        msg = f'Only {actual_removed:.2f} was available. Removed all.'
        flash(msg, 'warning')
    else:
        flash(f'Removed {actual_removed:.2f} from warehouse', 'success')

    return redirect(url_for('view_warehouse', warehouse_id=warehouse_id))


if __name__ == '__main__':
    debug_mode = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)
