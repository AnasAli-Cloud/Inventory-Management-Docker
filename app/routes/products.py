from flask import Blueprint, render_template, request, redirect, url_for, flash
from database import query_db, execute_db, get_db_cursor
import pymysql

products_bp = Blueprint('products', __name__)


@products_bp.route('/products')
def index():
    search_query = request.args.get('q', '').strip()
    category_filter = request.args.get('category_id', '').strip()

    sql = """
        SELECT p.*, c.name AS category_name
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE 1=1
    """
    params = []

    if search_query:
        sql += " AND (p.name LIKE %s OR p.sku LIKE %s)"
        params.extend([f"%{search_query}%", f"%{search_query}%"])

    if category_filter and category_filter.isdigit():
        sql += " AND p.category_id = %s"
        params.append(int(category_filter))

    sql += " ORDER BY p.id DESC"
    products = query_db(sql, tuple(params))
    categories = query_db("SELECT * FROM categories ORDER BY name ASC")

    # Add calculated status for UI display
    for p in products:
        if p['quantity'] <= 0:
            p['status'] = 'Out of Stock'
            p['badge_class'] = 'bg-danger'
        elif p['quantity'] <= p['min_threshold']:
            p['status'] = 'Low Stock'
            p['badge_class'] = 'bg-warning text-dark'
        else:
            p['status'] = 'In Stock'
            p['badge_class'] = 'bg-success'

    return render_template('products.html', products=products, categories=categories,
                           search_query=search_query, category_filter=category_filter)


@products_bp.route('/products/add', methods=['POST'])
def add_product():
    name = request.form.get('name', '').strip()
    sku = request.form.get('sku', '').strip()
    category_id = request.form.get('category_id') or None
    price = request.form.get('price', '0')
    quantity = request.form.get('quantity', '0')
    min_threshold = request.form.get('min_threshold', '5')

    if not name or not sku:
        flash('Product name and SKU are required.', 'danger')
        return redirect(url_for('products.index'))

    try:
        price = float(price)
        quantity = int(quantity)
        min_threshold = int(min_threshold)
    except ValueError:
        flash('Price and quantities must be valid numbers.', 'danger')
        return redirect(url_for('products.index'))

    try:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(
                """
                INSERT INTO products (name, sku, category_id, price, quantity, min_threshold)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (name, sku, category_id if category_id else None, price, quantity, min_threshold)
            )
            product_id = cursor.lastrowid

            if quantity > 0:
                cursor.execute(
                    """
                    INSERT INTO inventory_logs (product_id, change_type, quantity, reason)
                    VALUES (%s, 'IN', %s, 'Initial stock entry upon creation')
                    """,
                    (product_id, quantity)
                )

        flash(f'Product "{name}" created successfully!', 'success')
    except pymysql.err.IntegrityError as e:
        if 'sku' in str(e).lower():
            flash(f'Error: SKU "{sku}" already exists. Please choose a unique SKU.', 'danger')
        else:
            flash(f'Database integrity error: {e}', 'danger')
    except Exception as e:
        flash(f'Failed to add product: {e}', 'danger')

    return redirect(url_for('products.index'))


@products_bp.route('/products/edit/<int:product_id>', methods=['POST'])
def edit_product(product_id):
    name = request.form.get('name', '').strip()
    sku = request.form.get('sku', '').strip()
    category_id = request.form.get('category_id') or None
    price = request.form.get('price', '0')
    min_threshold = request.form.get('min_threshold', '5')

    if not name or not sku:
        flash('Product name and SKU cannot be empty.', 'danger')
        return redirect(url_for('products.index'))

    try:
        price = float(price)
        min_threshold = int(min_threshold)
    except ValueError:
        flash('Invalid numeric format for price or threshold.', 'danger')
        return redirect(url_for('products.index'))

    try:
        execute_db(
            """
            UPDATE products
            SET name = %s, sku = %s, category_id = %s, price = %s, min_threshold = %s
            WHERE id = %s
            """,
            (name, sku, category_id if category_id else None, price, min_threshold, product_id)
        )
        flash('Product updated successfully!', 'success')
    except pymysql.err.IntegrityError as e:
        flash(f'Update failed: SKU may already be in use ({e})', 'danger')
    except Exception as e:
        flash(f'Failed to update product: {e}', 'danger')

    return redirect(url_for('products.index'))


@products_bp.route('/products/delete/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    try:
        # Check if product is referenced in sales
        sales_count = query_db("SELECT COUNT(*) AS cnt FROM sales WHERE product_id = %s", (product_id,), one=True)
        if sales_count and sales_count['cnt'] > 0:
            flash(f'Cannot delete this product because it has {sales_count["cnt"]} associated sales records.', 'warning')
            return redirect(url_for('products.index'))

        execute_db("DELETE FROM products WHERE id = %s", (product_id,))
        flash('Product deleted successfully.', 'success')
    except Exception as e:
        flash(f'Error deleting product: {e}', 'danger')

    return redirect(url_for('products.index'))


@products_bp.route('/categories/add', methods=['POST'])
def add_category():
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()

    if not name:
        flash('Category name is required.', 'danger')
        return redirect(url_for('products.index'))

    try:
        execute_db("INSERT INTO categories (name, description) VALUES (%s, %s)", (name, description))
        flash(f'Category "{name}" added successfully!', 'success')
    except pymysql.err.IntegrityError:
        flash(f'Category "{name}" already exists.', 'warning')
    except Exception as e:
        flash(f'Error adding category: {e}', 'danger')

    return redirect(url_for('products.index'))
