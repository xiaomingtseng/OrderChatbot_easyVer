from infrastructure.database import Database

class OrderRepo:
    def __init__(self, db):
        self.collection = db.get_collection('orders')  # 使用 get_collection 方法

    def add_order(self, order_data):
        self.collection.insert_one(order_data)

    def get_orders(self, user_id):
        return list(self.collection.find({"user_id": user_id}, {"_id": 0}))

    def clear_orders(self, user_id):
        self.collection.delete_many({"user_id": user_id})