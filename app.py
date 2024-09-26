# app.py
from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
import os
from enum import Enum

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)


class Unit(Enum):
    KG = 'kg'
    PIECE = 'adet'


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    stock = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    production_date = db.Column(db.DateTime, nullable=False)
    unit = db.Column(db.Enum(Unit), nullable=False)

    @staticmethod
    def get_unit_for_product(name):
        name = name.lower()
        if 'kadayıf' in name or 'mantı' in name:
            return Unit.KG
        elif 'yufka' in name:
            return Unit.PIECE
        else:
            return Unit.KG  # Default to KG if unsure


class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    product_name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit = db.Column(db.Enum(Unit), nullable=False)
    sale_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/api/products', methods=['GET', 'POST'])
def handle_products():
    if request.method == 'POST':
        data = request.json
        unit = Product.get_unit_for_product(data['name'])
        new_product = Product(
            name=data['name'],
            stock=float(data['stock']),
            price=float(data['price']),
            production_date=datetime.fromisoformat(data['productionDate']),
            unit=unit
        )
        db.session.add(new_product)
        db.session.commit()
        return jsonify({"message": "Ürün başarıyla eklendi!"}), 201
    else:
        products = Product.query.all()
        return jsonify([{
            "id": p.id,
            "name": p.name,
            "stock": p.stock,
            "price": p.price,
            "productionDate": p.production_date.isoformat(),
            "unit": p.unit.value
        } for p in products])


@app.route('/api/products/<int:product_id>', methods=['PUT', 'DELETE'])
def update_delete_product(product_id):
    product = Product.query.get_or_404(product_id)

    if request.method == 'PUT':
        data = request.json
        product.name = data.get('name', product.name)
        product.stock = float(data.get('stock', product.stock))
        product.price = float(data.get('price', product.price))
        product.production_date = datetime.fromisoformat(
            data.get('productionDate', product.production_date.isoformat()))
        product.unit = Product.get_unit_for_product(data.get('name', product.name))
        db.session.commit()
        return jsonify({"message": "Ürün başarıyla güncellendi!"}), 200

    elif request.method == 'DELETE':
        db.session.delete(product)
        db.session.commit()
        return jsonify({"message": "Ürün başarıyla silindi!"}), 200


@app.route('/api/sales', methods=['GET', 'POST'])
def handle_sales():
    if request.method == 'POST':
        data = request.json
        product = Product.query.get(data['productId'])
        if not product:
            return jsonify({"message": "Ürün bulunamadı!"}), 404
        if product.stock < float(data['quantity']):
            return jsonify({"message": "Stok yetersiz!"}), 400

        new_sale = Sale(
            product_id=data['productId'],
            product_name=product.name,
            quantity=float(data['quantity']),
            unit=product.unit,
            sale_date=datetime.utcnow()
        )
        product.stock -= float(data['quantity'])

        db.session.add(new_sale)
        db.session.commit()
        return jsonify({"message": "Satış başarıyla oluşturuldu", "saleId": new_sale.id}), 201
    else:
        sales = Sale.query.all()
        return jsonify([{
            "saleId": s.id,
            "productName": s.product_name,
            "quantity": s.quantity,
            "unit": s.unit.value,
            "saleDate": s.sale_date.isoformat()
        } for s in sales])


def init_db():
    db_path = 'instance/inventory.db'
    if not os.path.exists(db_path):
        with app.app_context():
            db.create_all()
            print("Database created.")
    else:
        print("Database already exists.")


if __name__ == '__main__':
    init_db()
    app.run()