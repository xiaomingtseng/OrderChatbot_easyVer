from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# 模擬用戶狀態儲存（可使用 Redis 或資料庫替代）
user_state = {}

# LINE Messaging API Token
LINE_CHANNEL_ACCESS_TOKEN = 'YOUR_CHANNEL_ACCESS_TOKEN'
LINE_REPLY_API = 'https://api.line.me/v2/bot/message/reply'

# 處理 LINE Webhook
@app.route('/webhook', methods=['POST'])
def webhook():
    body = request.json
    events = body.get('events', [])
    
    for event in events:
        user_id = event['source']['userId']
        
        # 處理 Postback 事件
        if event['type'] == 'postback':
            data = event['postback']['data']
            if data == 'action=start_order':
                # 設置用戶狀態為等待餐點名稱
                user_state[user_id] = {'step': 'waiting_for_meal'}
                reply_message(event['replyToken'], "請輸入餐點名稱：")
        
        # 處理文字訊息事件
        elif event['type'] == 'message' and event['message']['type'] == 'text':
            user_message = event['message']['text']
            user_status = user_state.get(user_id, {})
            
            if user_status.get('step') == 'waiting_for_meal':
                # 儲存餐點名稱，要求輸入金額
                user_state[user_id]['meal_name'] = user_message
                user_state[user_id]['step'] = 'waiting_for_price'
                reply_message(event['replyToken'], "請輸入金額：")
            
            elif user_status.get('step') == 'waiting_for_price':
                # 儲存金額並回復確認訊息
                meal_name = user_status.get('meal_name')
                price = user_message
                reply_message(event['replyToken'], f"餐點：{meal_name}\n金額：{price} 元\n感謝您的點餐！")
                # 清除用戶狀態
                user_state.pop(user_id, None)
    
    return 'OK', 200

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
    requests.post(LINE_REPLY_API, headers=headers, json=data)

if __name__ == '__main__':
    app.run(port=5000)