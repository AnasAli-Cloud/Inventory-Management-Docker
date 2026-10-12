from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from database import query_db, get_db_cursor

sales_bp = Blueprint('sales', __name__)


@sales_bp.route('/sales')
def index():
    sales = query_db("""
        SELECT s.*, p.name AS product_name, p.sku
        FROM sales s
        JOIN products p ON s.product_id = p.id
        ORDER BY s.sale_date DESC
    """)

    products = query_db("""
        SELECT id, name, sku, price, quantity
        FROM products
        WHERE quantity > 0
        ORDER BY name ASC
    """)

    # Aggregate stats
    total_sales_count = len(sales)
    total_revenue = sum(float(s['total_price']) for s in sales)
    total_units_sold = sum(s['quantity'] for s in sales)

    return render_template(
        'sales.html',
        sales=sales,
        products=products,
        total_sales_count=total_sales_count,
        total_revenue=total_revenue,
        total_units_sold=total_units_sold
    )


@sales_bp.route('/sales/create', methods=['POST'])
def create_sale():
    product_id = request.form.get('product_id')
    quantity = request.form.get('quantity')
    customer_name = request.form.get('customer_name', 'Walk-in Customer').strip()

    if not product_id or not quantity:
        flash('Please select a product and provide quantity.', 'danger')
        return redirect(url_for('sales.index'))

    try:
        product_id = int(product_id)
        quantity = int(quantity)
        if quantity <= 0:
            flash('Sale quantity must be at least 1.', 'danger')
            return redirect(url_for('sales.index'))
    except ValueError:
        flash('Invalid quantity format.', 'danger')
        return redirect(url_for('sales.index'))

    if not customer_name:
        customer_name = 'Walk-in Customer'

    try:
        with get_db_cursor(commit=True) as cursor:
            # Atomic inventory check with row-level lock
            cursor.execute("SELECT id, name, price, quantity FROM products WHERE id = %s FOR UPDATE", (product_id,))
            product = cursor.fetchone()

            if not product:
                flash('Selected product does not exist.', 'danger')
                return redirect(url_for('sales.index'))

            if product['quantity'] < quantity:
                flash(
                    f'Insufficient stock for "{product["name"]}". Requested: {quantity}, Available: {product["quantity"]}.',
                    'danger'
                )
                return redirect(url_for('sales.index'))

            unit_price = float(product['price'])
            total_price = round(unit_price * quantity, 2)
            new_quantity = product['quantity'] - quantity

            # 1. Deduct stock from products
            cursor.execute("UPDATE products SET quantity = %s WHERE id = %s", (new_quantity, product_id))

            # 2. Record sale
            cursor.execute(
                """
                INSERT INTO sales (product_id, quantity, unit_price, total_price, customer_name)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (product_id, quantity, unit_price, total_price, customer_name)
            )
            sale_id = cursor.lastrowid

            # 3. Record audit trail in inventory_logs
            cursor.execute(
                """
                INSERT INTO inventory_logs (product_id, change_type, quantity, reason)
                VALUES (%s, 'OUT', %s, %s)
                """,
                (product_id, quantity, f"Sale Order #{sale_id} - {customer_name}")
            )

        flash(f'Sale recorded successfully! Invoice #{sale_id} | Total: ${total_price:,.2f} ({quantity}x {product["name"]})', 'success')

    except Exception as e:
        flash(f'Error processing sale: {e}', 'danger')

    return redirect(url_for('sales.index'))


@sales_bp.route('/api/products/<int:product_id>')
def get_product_details(product_id):
    product = query_db(
        "SELECT id, name, sku, price, quantity FROM products WHERE id = %s",
        (product_id,),
        one=True
    )
    if not product:
        return jsonify({"error": "Product not found"}), 404

    return jsonify({
        "id": product["id"],
        "name": product["name"],
        "sku": product["sku"],
        "price": float(product["price"]),
        "quantity": product["quantity"]
    })
