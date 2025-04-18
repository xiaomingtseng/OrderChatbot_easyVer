from flask import Flask, request, jsonify
import requests
import os
from infrastructure.orderRepo import OrderRepo  # 引入 OrderRepo
from infrastructure.database import Database  # 引入 Database
# 載入 LINE Message API 相關函式庫
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# 模擬用戶狀態儲存（可使用 Redis 或資料庫替代）
user_state = {}

# 初始化 OrderRepo
db = Database()  # 假設你有一個 Database 類別來處理 MongoDB 連接
order_repo = OrderRepo(db)

# LINE Messaging API Token
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')

LINE_REPLY_API = 'https://api.line.me/v2/bot/message/reply'

# 回復訊息給使用者
def reply_message(reply_token, text):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}'
    }
    data = {
        'replyToken': reply_token,
        'messages': [{'type': 'text', 'text': text}]
    }
    try:
        response = requests.post(LINE_REPLY_API, headers=headers, json=data)
        if response.status_code != 200:
            print(f"Error in reply_message: {response.status_code}, {response.text}")
            return {'error': response.text}, response.status_code
    except Exception as e:
        print(f"Exception in reply_message: {str(e)}")
        return {'error': str(e)}, 500

# 處理 LINE Webhook
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        body = request.json
        print(f"Request body: {body}")  # 調試用
        events = body.get('events', [])
        if not events:
            return {'error': 'No events found'}, 400

        for event in events:
            reply_token = event.get('replyToken')
            if not reply_token:
                print("Missing replyToken")
                continue

            user_id = event['source'].get('userId')
            if not user_id:
                print("Missing userId")
                continue

            # 處理 Postback 事件
            if event['type'] == 'postback':
                data = event['postback'].get('data')
                if not data:
                    print("Missing postback data")
                    continue

                if data == 'action=start_order':
                    # 設置用戶狀態為等待餐點名稱
                    user_state[user_id] = {'step': 'waiting_for_meal'}
                    reply_message(reply_token, "請輸入餐點名稱：")

                elif data == 'action=view_cart':
                    # 查看購物車
                    orders = order_repo.get_orders(user_id)
                    if not orders:
                        reply_message(reply_token, "您的購物車是空的！")
                    else:
                        cart_details = "\n".join([f"{order['meal_name']} - {order['price']} 元" for order in orders])
                        reply_message(reply_token, f"您的購物車內容：\n{cart_details}")

                elif data == 'action=clear_cart':
                    # 清空購物車
                    order_repo.clear_orders(user_id)
                    reply_message(reply_token, "您的購物車已清空！")

                elif data == 'action=total_price':
                    # 計算總金額
                    orders = order_repo.get_orders(user_id)
                    if not orders:
                        reply_message(reply_token, "您的購物車是空的！")
                    else:
                        total_price = sum(int(order['price']) for order in orders)
                        reply_message(reply_token, f"您的購物車總金額為：{total_price} 元")

            # 處理文字訊息事件
            elif event['type'] == 'message' and event['message']['type'] == 'text':
                user_message = event['message']['text']
                user_status = user_state.get(user_id, {})

                if user_status.get('step') == 'waiting_for_meal':
                    # 儲存餐點名稱，要求輸入金額
                    user_state[user_id]['meal_name'] = user_message
                    user_state[user_id]['step'] = 'waiting_for_price'
                    reply_message(reply_token, "請輸入金額：")

                elif user_status.get('step') == 'waiting_for_price':
                    # 儲存金額並回復確認訊息
                    meal_name = user_status.get('meal_name')
                    price = user_message

                    # 將餐點數據存入資料庫
                    order_data = {"user_id": user_id, "meal_name": meal_name, "price": price}
                    order_repo.add_order(order_data)

                    reply_message(reply_token, f"餐點：{meal_name}\n金額：{price} 元\n感謝您的點餐！")
                    # 清除用戶狀態
                    user_state.pop(user_id, None)

        return 'OK', 200

    except Exception as e:
        print(f"Exception in webhook: {str(e)}")
        return {'error': str(e)}, 500

if __name__ == '__main__':
    app.run(port=5000)