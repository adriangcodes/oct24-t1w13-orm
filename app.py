from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

app = Flask(__name__)

# Database connection string
# <protocol>://<user>:<password>@<host>:<port>/<db_name>
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://orm_dev:123456@localhost:5432/orm_db'

db = SQLAlchemy(app)
ma = Marshmallow(app)

# Model
# This just declares and configures the model in memory - the physical DB is unaffected.
class Product(db.Model):
    __tablename__ = "products"
    
    id = db.Column(db.Integer, primary_key=True)
    
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float(precision=2), nullable=False)
    stock = db.Column(db.Integer, db.CheckConstraint('stock >= 0'), default=0)

# Marshmallow Schema
class ProductSchema(ma.Schema):
    class Meta: # Treated as metadata
        fields = ('id', 'name', 'description', 'price', 'stock')
    
# Home route
@app.route('/')
def home():
    return 'Hello!'

# Enables the use of flask init_db in Terminal
@app.cli.command('init_db')
def init_db():
    db.drop_all() # Deletes any existing tables
    db.create_all()
    print('Created tables.')

# C - Create (one)
@app.route('/products', methods=['POST'])
def create_product():
    # Parse the incoming JSON body from Bruno
    data = ProductSchema(exclude=['id']).load(request.json) # exclude prevents the ID from the allowed fields to be written into. include also works in the opposite way.
    # print(data)
    # Create a new instance
    new_product = Product(
        name = data['name'],
        description = data.get('description', ''), # get allows you to include a default entry
        price = data['price'],
        stock = data.get('stock') # get allows you to avoid a key error, and return null if input is not present (allows for default entry at model level)
    )
    # Add to db session
    db.session.add(new_product)
    # Commit to the db
    db.session.commit()
    return ProductSchema(many=False).dump(new_product), 201 # Returns code 201 "Created"

# R - Read (one)
@app.route('/products/<int:product_id>')
def get_one_product(product_id):
    # Query database for product with given id
    # SELECT * FROM Products where id = product_id;
    stmt = db.select(Product).filter_by(id=product_id)
    product = db.session.scalar(stmt)
    if product:
        return ProductSchema(many=False).dump(product)
    else:
        return {"error": f"Product with id {product_id} not found."}, 404

# R - Read (all)
@app.route('/products')
def get_all_products():
    # Generate a statement
    # SELECT * FROM Products;
    stmt = db.select(Product)
    # Execute the statement
    products = db.session.scalars(stmt)
    return ProductSchema(many=True).dump(products)

# U - Update (one)
# PUT - provide the whole object
# PATCH - replace part of the object - inefficient approach
# Create statement to select the product with the given product_id
# Execute the statement (scalar)
# If product exists, update the fields and commit
@app.route('/products/<int:product_id>', methods=['PUT'])
def update_one_product(product_id):
    # Load and parse the incoming body
    data = ProductSchema(exclude=['id']).load(request.json)
    # Select the product by product_id
    stmt = db.select(Product).filter_by(id=product_id)
    product = db.session.scalar(stmt)
    if product:
        # Update product attirbutes with incoming data
        product.name = data['name'],
        product.description = data.get('description', ''),
        product.price = data['price'],
        product.stock = data.get('stock')
        # Commit changes
        db.session.commit()
        return ProductSchema().dump(product), 200
    else:
        return {"error": f"Product with id {product_id} not found."}, 404

# D - Delete (one)
# DELETE /products/<int:id>
# Select the product with the given product_id
# Execute the statement (scalar)
# Delete the product (if exists), otherwise return error
# If deletion successful, return status code with no content
@app.route('/products/<int:product_id>', methods=['DELETE'])
def delete_one_product(product_id):
    # Delete Product with given id
    # SELECT * FROM products where id = product_id;
    stmt = db.select(Product).filter_by(id=product_id)
    product = db.session.scalar(stmt)
    if product:
        db.session.delete(product)
        db.session.commit()
        return {}, 204 # HTTP 204 code is "No Content"
    else:
        return {"error": f"Product with id {product_id} not found."}, 404

# Seeding database
@app.cli.command('seed_db')
def seed_db():
    products = [
        Product(
            name='Product 1',
            description='First product',
            price=12.99,
            stock=15
        ),
        Product(
            name='Product 2',
            description='Second product',
            price=2.99,
            stock=100
        )
    ]
    
    # db.session.add(product1) # Adds individual product
    # db.delete(Product) # Clears all instance of product 
    db.session.add_all(products)
    db.session.commit()
    print('DB seeded.')