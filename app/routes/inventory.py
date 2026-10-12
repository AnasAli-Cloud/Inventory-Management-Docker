from flask import Blueprint, render_template, request, redirect, url_for, flash
from database import query_db, get_db_cursor

inventory_bp = Blueprint('inventory', __name__)


@inventory_bp.route('/inventory')
def index():
    products = query_db("""
        SELECT p.*, c.name AS category_name
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        ORDER BY p.name ASC
    """)

    logs = query_db("""
        SELECT il.*, p.name AS product_name, p.sku
        FROM inventory_logs il
        JOIN products p ON il.product_id = p.id
        ORDER BY il.created_at DESC
        LIMIT 50
    """)

    # Compute status labels
    for p in products:
        if p['quantity'] <= 0:
            p['status'] = 'Out of Stock'
            p['badge_class'] = 'bg-danger'
        elif p['quantity'] <= p['min_threshold']:
            p['status'] = 'Low Stock'
            p['badge_class'] = 'bg-warning text-dark'
        else:
            p['status'] = 'Optimal'
            p['badge_class'] = 'bg-success'

    return render_template('inventory.html', products=products, logs=logs)


@inventory_bp.route('/inventory/adjust', methods=['POST'])
def adjust_stock():
    product_id = request.form.get('product_id')
    change_type = request.form.get('change_type')  # 'IN' or 'OUT'
    quantity = request.form.get('quantity')
    reason = request.form.get('reason', '').strip()

    if not product_id or not change_type or not quantity:
        flash('Product, change type, and quantity are required.', 'danger')
        return redirect(url_for('inventory.index'))

    try:
        product_id = int(product_id)
        quantity = int(quantity)
        if quantity <= 0:
            flash('Quantity must be greater than zero.', 'danger')
            return redirect(url_for('inventory.index'))
    except ValueError:
        flash('Invalid numeric inputs.', 'danger')
        return redirect(url_for('inventory.index'))

    if change_type not in ('IN', 'OUT'):
        flash('Invalid change type specified.', 'danger')
        return redirect(url_for('inventory.index'))

    default_reason = f"Manual Stock {'Arrival' if change_type == 'IN' else 'Deduction'}"
    final_reason = reason if reason else default_reason

    try:
        with get_db_cursor(commit=True) as cursor:
            # Lock the row for update to ensure atomic calculation
            cursor.execute("SELECT id, name, quantity FROM products WHERE id = %s FOR UPDATE", (product_id,))
            product = cursor.fetchone()

            if not product:
                flash('Product not found.', 'danger')
                return redirect(url_for('inventory.index'))

            current_qty = product['quantity']

            if change_type == 'OUT' and current_qty < quantity:
                flash(f'Cannot stock out {quantity} units of "{product["name"]}". Only {current_qty} currently in stock.', 'danger')
                return redirect(url_for('inventory.index'))

            new_qty = current_qty + quantity if change_type == 'IN' else current_qty - quantity

            cursor.execute("UPDATE products SET quantity = %s WHERE id = %s", (new_qty, product_id))
            cursor.execute(
                """
                INSERT INTO inventory_logs (product_id, change_type, quantity, reason)
                VALUES (%s, %s, %s, %s)
                """,
                (product_id, change_type, quantity, final_reason)
            )

        action_word = "Added to" if change_type == 'IN' else "Removed from"
        flash(f'Stock updated: {action_word} "{product["name"]}" by {quantity} units (Current: {new_qty}).', 'success')

    except Exception as e:
        flash(f'Failed to adjust inventory: {e}', 'danger')

    return redirect(url_for('inventory.index'))
