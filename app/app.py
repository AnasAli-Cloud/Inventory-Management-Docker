import os
from flask import Flask, render_template, jsonify
from database import query_db, get_db_connection
from routes.products import products_bp
from routes.inventory import inventory_bp
from routes.sales import sales_bp

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'inventory-docker-secret-key-2024')

# Register modular blueprints
app.register_blueprint(products_bp)
app.register_blueprint(inventory_bp)
app.register_blueprint(sales_bp)


# Custom Jinja filters
@app.template_filter('currency')
def currency_filter(value):
    try:
        return f"${float(value):,.2f}"
    except (ValueError, TypeError):
        return "$0.00"


@app.route('/')
def dashboard():
    # 1. Total Products Count
    prod_stat = query_db("SELECT COUNT(*) AS total_products, COALESCE(SUM(quantity), 0) AS total_units, COALESCE(SUM(quantity * price), 0) AS total_valuation FROM products", one=True)
    total_products = prod_stat['total_products'] if prod_stat else 0
    total_units = prod_stat['total_units'] if prod_stat else 0
    total_valuation = prod_stat['total_valuation'] if prod_stat else 0

    # 2. Low Stock Alerts
    low_stock_items = query_db("""
        SELECT p.*, c.name AS category_name
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE p.quantity <= p.min_threshold
        ORDER BY p.quantity ASC
    """)
    low_stock_count = len(low_stock_items)

    # 3. Sales Metrics
    sales_stat = query_db("SELECT COUNT(*) AS total_orders, COALESCE(SUM(total_price), 0) AS total_revenue FROM sales", one=True)
    total_orders = sales_stat['total_orders'] if sales_stat else 0
    total_revenue = sales_stat['total_revenue'] if sales_stat else 0

    # 4. Recent Activities
    recent_sales = query_db("""
        SELECT s.*, p.name AS product_name
        FROM sales s
        JOIN products p ON s.product_id = p.id
        ORDER BY s.sale_date DESC
        LIMIT 6
    """)

    recent_logs = query_db("""
        SELECT il.*, p.name AS product_name
        FROM inventory_logs il
        JOIN products p ON il.product_id = p.id
        ORDER BY il.created_at DESC
        LIMIT 6
    """)

    return render_template(
        'index.html',
        total_products=total_products,
        total_units=total_units,
        total_valuation=total_valuation,
        low_stock_count=low_stock_count,
        low_stock_items=low_stock_items,
        total_orders=total_orders,
        total_revenue=total_revenue,
        recent_sales=recent_sales,
        recent_logs=recent_logs
    )


@app.route('/api/dashboard/charts')
def dashboard_charts():
    # Sales Trend by Day (last 7 days)
    sales_by_day = query_db("""
        SELECT DATE(sale_date) AS day,
               SUM(total_price) AS daily_revenue,
               SUM(quantity) AS daily_units
        FROM sales
        GROUP BY DATE(sale_date)
        ORDER BY day ASC
        LIMIT 7
    """)

    # Category Stock Breakdown
    category_stock = query_db("""
        SELECT COALESCE(c.name, 'Uncategorized') AS category,
               SUM(p.quantity) AS total_stock
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        GROUP BY c.name
    """)

    formatted_sales = [
        {
            "day": str(row['day']),
            "daily_revenue": float(row['daily_revenue'] or 0),
            "daily_units": int(row['daily_units'] or 0)
        }
        for row in (sales_by_day or [])
    ]

    formatted_categories = [
        {
            "category": str(row['category']),
            "total_stock": int(row['total_stock'] or 0)
        }
        for row in (category_stock or [])
    ]

    return jsonify({
        "sales_trend": formatted_sales,
        "category_distribution": formatted_categories
    })


@app.route('/health')
def health_check():
    """Container healthcheck endpoint for Docker / orchestration"""
    try:
        conn = get_db_connection(max_retries=1, delay=0)
        conn.close()
        return jsonify({"status": "healthy", "database": "connected"}), 200
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 503


@app.errorhandler(404)
def not_found(e):
    return render_template('base.html', not_found=True), 404


@app.errorhandler(500)
def server_error(e):
    return render_template('base.html', server_error=True), 500


if __name__ == '__main__':
    # Listen on 0.0.0.0 inside the container so Docker port mapping works
    app.run(host='0.0.0.0', port=5000, debug=True)
