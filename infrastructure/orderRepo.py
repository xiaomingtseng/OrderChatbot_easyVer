
from infrastructure.database import Database

class OrderRepo:
    def __init__(self, db):
        self.db = Database()
        self.order_collection = self.db.get_collection('orders')

    def get_orders(self):
        return self.db.get_collection('orders').find()

# add an order
    def add_order(self, order_data):
        return self.db.get_collection('orders').insert_one(order_data)

# delete all orders
    
    def delete_orders(self):
        return self.db.get_collection('orders').delete_many({})