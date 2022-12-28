import google
from flask import Flask, request, abort
import os
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import LineBotApiError
from linebot.exceptions import InvalidSignatureError
import requests
from linebot.models import MessageEvent, TextMessage, TextSendMessage, TemplateSendMessage, ButtonsTemplate, MessageTemplateAction, FlexSendMessage, PostbackEvent
from datetime import datetime as dt
from datetime import timedelta
import random
import json
from datetime import timedelta
# import time

# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/Users/annybearlee/PycharmProjects/test1118/annybearlee-linebot-test-c60aa6a850c3.json"
WEATHER_KEY="CWB-72EFCFC1-4EF5-4A47-AC7E-8F33110D0F1B"

# WEATHER API
# WEATHER_KEY = os.environ["WEATHER_KEY"]
# 在local測試資料庫時再使用
# GOOGLE_APPLICATION_CREDENTIALS = os.environ["GOOGLE_APPLICATION_CREDENTIALS"]

# Imports the Google Cloud client library
from google.cloud import datastore

# Instantiates a client
datastore_client = datastore.Client()

app = Flask(__name__)


# today = dt.now().date()


# LINE 聊天機器人的基本資料
line_bot_api = LineBotApi('7d1g9wCrKfTEoxYDJ/xBDz1431u5ghkL7jz9Xma3jbvQXyJ6DhYegZc4+xTqVZ66RxWdmcxWVouqk+i35L1XapgE1b0V5oRwiiRFrZSKPHYzYDIjT7cHg0tCcdMtXmSJvjcaNwEFVt3D/D4w+MFxMAdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('a9d95660b8fa434c63c8997e2135c41b')
# LINE_API = os.environ["LINE_API"]
# line_bot_api = LineBotApi(LINE_API)
# HANDLER = os.environ["HANDLER"]
# handler = WebhookHandler(HANDLER)



@app.route('/', methods=['GET','POST'])
def home():
    return "Hello"


@app.route("/callback", methods=['GET','POST'])
def callback():
    signature = request.headers['X-Line-Signature']

    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


def get_user_id(event):
    try:
        _id = event.source.user_id
        return _id
    except LineBotApiError as e:
        # error handle
        return "Cannot get User ID"


def get_quote():
    response = requests.get("https://api.kanye.rest")
    data = response.json()
    quote = data['quote']
    return quote


info = ['天氣狀況','最低溫','最高溫','舒適度','降雨機率']


# Weather
order = [0,2,4,3,1]
def get_weather2(message, weather_data):
    response = requests.get("https://opendata.cwb.gov.tw/api/v1/rest/datastore/F-C0032-001?Authorization=CWB-72EFCFC1-4EF5-4A47-AC7E-8F33110D0F1B&format=JSON")
    datas = response.json()
    # 氣象局使用的為“臺”
    if "台" in message:
        message = message.replace("台", "臺")
    for data in datas['records']['location']:
        if message in data['locationName']:
            for i in range(len(order)):
                data_to_append = data['weatherElement'][order[i]]['time'][0]['parameter']['parameterName']
                if i == 1 or i == 2:
                    data_to_append += "°C"
                elif i == 4:
                    data_to_append += "%"
                weather_data.append(data_to_append)
            weather_data.append(data['locationName'])
            return weather_data
    # 萬一輸入錯誤
    else:
        return "請輸入正確的縣市名稱，或是輸入q以結束天氣模式"


# 猜數字遊戲
def check_number(num, task):
    # 如果使用者輸入q, 那就結束遊戲
    if num == 'q':
        task['game-mode'] = 0
        # task['score'] = 0
        datastore_client.put(task)
        return f"終止, secret number為{task['secret-number']}"
    try:
        number = int(num)
    except:
        return "請輸入阿拉伯數字或輸入q以結束遊戲"

    # 如果零分的話
    if task['score'] == 0:
        task['game-mode'] = 0
        datastore_client.put(task)
        return f"終止, the secret number is {task['secret-number']}"

    if number == task["secret-number"]:
        task['game-mode'] = 0
        datastore_client.put(task)
        return f"答對 {task['score']}"
        # return f"恭喜答對了，正確答案是{task['secret-number']}，最後分數:{new_score}/20"
    elif number < task["secret-number"]:
        task['score'] -= 1
        datastore_client.put(task)
        return f"太小了，請猜大一點的數字，目前分數：{task['score']}/20"
    else:
        task['score'] -= 1
        datastore_client.put(task)
        return f"太大了，請猜小一點的數字，目前分數：{task['score']}/20"


cards = [11, 2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10]
def deal_card():
    card = random.choice(cards)
    return card


def calculate_score(cards):
    for i in range(len(cards)):
        cards[i] = int (cards[i])
    if sum(cards)==21 and len(cards)==2:
        return 0

    if 11 in cards and sum(cards)>21:
        cards.remove(11)
        cards.append(1)

    return sum(cards)


def compare(user_score, computer_score):
    if user_score == computer_score:
        return "平局 :))"

    elif computer_score == 0:
        return "電腦Blackjack，你輸了:("

    elif user_score == 0:
        return "獲得Blackjack，你贏了！"

    elif user_score > 21:
        return "超過21點，請再接再厲 :(("

    elif computer_score > 21:
        return "電腦超過21點，你贏了!!"

    elif user_score > computer_score:
        return "恭喜贏了！"

    else:
        return "輸了:(( 請再接再厲！"


# 條列式產出待辦清單
def display_to_do(send,task):
    i = 1
    for t in task:
        send += f"{i}. "
        if i == 1:
            send += " "
        send += t
        send += "\n"
        i += 1
    send = send.strip()
    return send


# 產出flex message底下的按鈕
symbol_list = ["+", "#", "$"]
def generate_button(j, label):
    global symbol_list
    for i in range(0, 3):
        j['footer']['contents'][i]['action']['text'] = f"{symbol_list[i]}{label}"

# 檢查使用者是否想要結束某個模式
def check_if_quit_mode(message,event,task,mode):
    if message == 'q':
        if mode == 'game-21':
            task[mode]['mode'] = 0
            datastore_client.put(task)
        else:
            task[mode] = 0
            datastore_client.put(task)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(f"結束{mode}模式"))

# 發現尚未建立待辦事項時回覆
def no_todo_found_reply(event, date):
    j = json.load(open('no_todo_found.json', 'r', encoding='utf-8'))
    j['body']['contents'][0]['contents'][0]['contents'][0]['text'] = f"您在{date}尚未建立待辦事項"
    j['footer']['contents'][0]['action']['text'] = f"+{date}"
    flex_message = FlexSendMessage(
        alt_text='no-todo-found',
        contents=j
    )
    line_bot_api.reply_message(event.reply_token, flex_message)

# 顯示今日待辦事項(今日的待辦事項會顯示件數及加油鼓勵)
def display_today(event, j, task, today):
    send = f"您今天尚有{len(task['to-do'][today])}件待辦事項，加油！\n"
    send += "\n"
    j['body']['contents'][0]['text'] = "今日待辦"
    j['body']['contents'][2]['contents'][0]['contents'][0]['text'] = display_to_do(send,
                                                                                   task['to-do'][today])
    generate_button(j, today)
    flex_message = FlexSendMessage(
        alt_text='to-do-list',
        contents=j
    )
    line_bot_api.reply_message(event.reply_token, flex_message)

# 顯示其他日期的待辦事項
def display_other_day(event,j,task,send,type):
    if "!" in type:
        type = type.replace("!","")
        print(type)
        j['body']['contents'][2]['contents'][0]['contents'][0]['text'] = display_to_do(send, task['to-do'][type])
        generate_button(j, type)
    else:
        j['body']['contents'][2]['contents'][0]['contents'][0]['text'] = display_to_do(send, task['to-do'][task[type]])
        generate_button(j, task[type])
    flex_message = FlexSendMessage(
        alt_text="to-do",
        contents=j
    )
    line_bot_api.reply_message(event.reply_token, flex_message)

# 資料庫初次創建
def initialize_db(key):
    task = datastore.Entity(key=key)
    # task = datastore_client.get(key=key)
    task['game-21'] = {}
    task['game-21']['mode'] = 0
    task['game-21']["user_cards"] = []
    task['game-21']["computer_cards"] = []
    task['game-21']['user_score'] = 0
    task['game-21']['computer_score'] = 0
    task['game-21']['round'] = 0
    task['weather-mode'] = 0
    task['view-mode'] = 0
    task['edit-mode'] = 0
    task['delete-mode'] = 0
    task['add-mode'] = 0
    task['game-mode'] = 0
    task['to-do'] = {}
    task['score'] = 20
    task['secret-number'] = 0
    task['date-to-add'] = 0
    datastore_client.put(task)
    task = datastore_client.get(key=key)
    return task

# Version II----------------------------------------------------------------------------

@handler.add(PostbackEvent)
def handle_postback(event):
    id = get_user_id(event)
    key = datastore_client.key('Task4', id)
    try:
        task = datastore_client.get(key=key)
        r = task['add-mode']

    # 若尚未建置，則建一個資料庫
    except:
        task = initialize_db(key)

    if task['view-mode'] == 2:
        date = event.postback.params['date']
        send = f"您在{date}的待辦事項有:\n"
        send += "\n"
        j = json.load(open('brown2.json', 'r', encoding='utf-8'))
        try:
            # 檢查該日期是否已建檔
            to_do = task['to-do'][date]
            # 可能該日期有建檔但裡面資料已被刪光, length為0
            if len(to_do) == 0:
                task['view-mode'] = 0
                datastore_client.put(task)
                no_todo_found_reply(event,date)

            else:
                today = str(dt.now().date())
                if date == today:
                    task['view-mode'] = 0
                    datastore_client.put(task)
                    display_today(event, j, task, today)
                else:
                    date += "!"
                    task['view-mode'] = 0
                    datastore_client.put(task)
                    display_other_day(event, j, task, send, date)

        # 可能該日期尚未建檔
        except:
            task['view-mode'] = 0
            datastore_client.put(task)
            no_todo_found_reply(event, date)


    elif task['add-mode'] == 2:
        date = event.postback.params['date']
        send= f"您選擇了{date}, 請輸入該日欲新增之事項："
        task['add-mode'] = 3
        task['date-to-add'] = date
        datastore_client.put(task)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(send))


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    message = event.message.text
    id = get_user_id(event)
    key = datastore_client.key('Task4', id)
    # 先檢查資料庫是否已建好
    try:
        task = datastore_client.get(key=key)
        r = task['add-mode']

    # 若尚未建置，則建一個資料庫
    except:
        task = initialize_db(key)

    # ------------------------------------- 新增待辦模式 ------------------------------------------------#
    if task['add-mode'] == 2:
        check_if_quit_mode(message, event, task, 'add-mode')
        j = json.load(open('pick_date_to_add.json','r',encoding='utf-8'))
        j['body']['contents'][0]['text'] = "請以日期選擇器選取日期，或輸入q以退出新增編輯模式"
        flex_message = FlexSendMessage(
            alt_text='選擇日期',
            contents=j
        )
        line_bot_api.reply_message(event.reply_token, flex_message)

    # 透過flex message button新增待辦，已知日期
    elif task['add-mode'] == 3:
        today = str(dt.now().date())
        # 檢查使用者所輸入的日期是否已建好list
        try:
            task['to-do'][task['date-to-add']].append(message)
        except:
            task['to-do'][task['date-to-add']]=[]
            task['to-do'][task['date-to-add']].append(message)

        task['add-mode'] = 0
        datastore_client.put(task)
        j = json.load(open('brown2.json', 'r', encoding='utf-8'))
        if task['date-to-add'] == today:
            display_today(event,j,task,today)
        send = f"您已新增成功，您在{task['date-to-add']}的待辦事項有:\n"
        send += "\n"
        display_other_day(event,j,task,send,"date-to-add")


    # ---------------------------- 查看待辦模式 ----------------------------------------------------#

    elif "@" in message:
        message = message.replace("@","")
        if message =="其他日期":
            task['view-mode'] = 2
            datastore_client.put(task)
            j = json.load(open('pick_a_date.json','r',encoding='utf-8'))
            flex_message = FlexSendMessage(
                alt_text='pick a date',
                contents=j
            )
            line_bot_api.reply_message(event.reply_token, flex_message)

        else:
            j = json.load(open('brown2.json', 'r', encoding='utf-8'))

            send = f"您在{message}的待辦事項有:\n"
            send += "\n"
            try:
                # 檢查該日期是否已建檔
                to_do = task['to-do'][message]
                # 可能該日期有建檔但裡面資料已被刪光, length為0
                if len(to_do) == 0:
                    task['view-mode'] = 0
                    datastore_client.put(task)
                    no_todo_found_reply(event,message)
                else:
                    today = str(dt.now().date())
                    task['view-mode'] = 0
                    datastore_client.put(task)
                    if message == today:
                        display_today(event,j,task,today)
                    else:
                        message += "!"
                        display_other_day(event,j,task,send,message)
            # 可能該日期尚未建檔
            except:
                task['view-mode'] = 0
                datastore_client.put(task)
                no_todo_found_reply(event, message)

    # ---------------------------- 編輯待辦模式 -----------------------------------------------------#
    # 接收使用者欲輸入事項的index
    elif task['edit-mode'] == 1:
        check_if_quit_mode(message, event, task, "edit-mode")
        success = 1

        # 1. 檢查使用者所輸入的是否為阿拉伯數字
        try:
            index = int(message)-1
        except:
            success = 0
            line_bot_api.reply_message(event.reply_token, TextSendMessage("請輸入阿拉伯數字，或輸入q以退出編輯模式"))

        # 2. 檢查使用者所輸入的數字是否大於零
        if success == 1:
            if int(message) > 0:
                success = 2
            else:
                line_bot_api.reply_message(event.reply_token, TextSendMessage("請輸入大於零的數字，或輸入q以退出編輯模式"))

        # 3. 檢查使用者所輸入的數字是否在清單範圍之內
        if success == 2:
            try:
                to_do = task['to-do'][task['date-to-edit']][int(message)-1]
                task['edit-index'] = int(message)-1
                task['edit-mode'] = 2
                datastore_client.put(task)
                line_bot_api.reply_message(event.reply_token, TextSendMessage("請輸入欲編輯之文字："))
            # out of range
            except:
                line_bot_api.reply_message(event.reply_token, TextSendMessage("請輸入清單範圍內的數字，或輸入q以退出編輯模式"))

    # 接收使用者所輸入的編輯文字
    elif task['edit-mode'] == 2:
        check_if_quit_mode(message, event, task, "edit-mode")
        task['to-do'][task['date-to-edit']][task['edit-index']] = message
        task['edit-mode'] = 0
        datastore_client.put(task)
        today = str(dt.now().date())
        j = json.load(open('brown2.json', 'r', encoding='utf-8'))
        if task['date-to-edit'] == today:
            display_today(event,j,task,today)
        send = f"您已編輯成功，您在{task['date-to-edit']}的待辦事項有：\n"
        send += "\n"
        display_other_day(event,j,task,send,"date-to-edit")

    # ----------------------------------- 刪除待辦模式 --------------------------------------------------#

    elif task['delete-mode'] == 1:
        check_if_quit_mode(message, event, task, "delete-mode")
        # 檢查是否為阿拉伯數字
        index = 0
        success = 1
        try:
            index = int(message)-1
        except:
            success = 0
            line_bot_api.reply_message(event.reply_token, TextSendMessage("請輸入阿拉伯數字，或輸入q以退出刪除模式"))
        # 檢查所輸入的數字是否大於零
        if success == 1:
            if int(message)>0:
                success = 2
            else:
                line_bot_api.reply_message(event.reply_token, TextSendMessage("請輸入大於零的數字，或輸入q以退出刪除模式"))
        # 檢查數字是否在清單範圍內
        if success == 2:
            try:
                # 刪除
                task['to-do'][task['date-to-delete']].pop(index)
                task['delete-mode'] = 0
                datastore_client.put(task)
                # 刪除後清單內已無待辦：
                if len(task['to-do'][task['date-to-delete']]) == 0:
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(f"您已刪除成功，您在{task['date-to-delete']}已無待辦事項"))
                # 刪除後仍有待辦須列出：
                today = str(dt.now().date())
                j = json.load(open('brown2.json', 'r', encoding='utf-8'))
                # 刪除的是今天的話，以今天待辦的模式呈現
                if task['date-to-delete'] == today:
                    display_today(event,j,task,today)
                # 是其他天的話：
                send = f"您已刪除成功，您在{task['date-to-delete']}的待辦事項有：\n"
                send += "\n"
                display_other_day(event,j,task,send,"date-to-delete")
            except:
                line_bot_api.reply_message(event.reply_token, TextSendMessage("請輸入清單範圍內的數字，或輸入q以退出刪除模式"))
    # ----------------------------------- 天氣模式 --------------------------------------------------#
    # 天氣flex message版本
    elif task['weather-mode'] == 1:
        check_if_quit_mode(message, event, task, "weather-mode")
        # 取得天氣資訊
        data = []
        weather_data = get_weather2(message, data)
        # 輸入錯誤的話，給予錯誤訊息請使用者重新輸入一次
        if type(weather_data) == str:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(weather_data))
        # 把天氣資訊套入flex message裡傳送
        else:
            j = json.load(open('weather.json', 'r', encoding='utf-8'))
            j['body']['contents'][0]['text'] = f"{dt.now().date()} {weather_data[-1]}天氣"
            for i in range(0, 5):
                j['body']['contents'][1]['contents'][i]['contents'][1]['text'] = weather_data[i]
            remind = []
            if int(weather_data[4].split("%")[0]) >= 30:
                remind.append("請記得帶傘")
            if "寒" in weather_data[3]:
                remind.append("請注意保暖")
            if len(remind)>0:
                send = ""
                for text in remind:
                    send += text
                    send += ";"
                send = send.strip(";")
                j['body']['contents'][1]['contents'][5]['contents'][1]['text'] = send

            flex_message = FlexSendMessage(
                alt_text='weather',
                contents=j
            )
            task['weather-mode'] = 0
            datastore_client.put(task)
            line_bot_api.reply_message(event.reply_token, flex_message)

    # ----------------------------------- 猜數字模式 --------------------------------------------------#
    elif task['game-mode'] == 1:
        check_if_quit_mode(message,event,task,'game-mode')
        # 依照使用者所選取的數字區間來隨機產出數字
        try:
            message = message.split("~")
            task['secret-number'] = random.randint(int(message[0]), int(message[1]))
            # task['score'] = int(message[1])
            task['game-mode'] = 2
            datastore_client.put(task)
            line_bot_api.reply_message(event.reply_token, TextSendMessage(f"來玩猜數字吧，請選{message[0]}~{message[1]}中的一個數字"))
        # 若沒選取，則再叫使用者選取一次，或輸入q已退出遊戲模式
        except:
            j = json.load(open('guess_menu_2.json', 'r', encoding='utf-8'))
            flex_message = FlexSendMessage(
                alt_text='guess_number_menu',
                contents=j
            )
            line_bot_api.reply_message(event.reply_token, flex_message)

    elif task['game-mode'] == 2:
        reply = check_number(message, task)
        # 答對的話會產出flex message顯示答案與最終分數
        if "答對" in reply or "終止" in reply:
            j = json.load(open('game_2.json', 'r', encoding='utf-8'))
            # 如果選擇退出遊戲或分數已達到0，顯示「挑戰失敗」
            if "終止" in reply:
                j['body']['contents'][0]['text'] = "挑戰失敗"
            j['body']['contents'][1]['contents'][0]['contents'][1]['text'] = str(task['secret-number'])
            j['body']['contents'][1]['contents'][1]['contents'][1]['text'] = f"{task['score']}/20"
            flex_message = FlexSendMessage(
                alt_text='congrats',
                contents=j
            )
            line_bot_api.reply_message(event.reply_token, flex_message)
        # 沒答對就繼續玩
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(reply))
    # ----------------------------------- 21點模式 --------------------------------------------------#
    elif task['game-21']['mode'] == 1:
        message =message.strip().lower()
        check_if_quit_mode(message,event,task,'game-21')

        user_wanna_end = False
        task['game-21']['round'] += 1
        datastore_client.put(task)
        # 第一輪時，一開始玩家與電腦各抽兩張卡
        if task['game-21']['round'] == 1:
            for _ in range(2):
                task['game-21']['user_cards'].append(deal_card())
                task['game-21']['computer_cards'].append(deal_card())
                datastore_client.put(task)
        # 第一輪以後，如果玩家想繼續抽則再抽一張牌
        if task['game-21']['round'] >=2 and message == 'y':
            task['game-21']['user_cards'].append(deal_card())
            datastore_client.put(task)
        # 若玩家不想繼續抽
        elif task['game-21']['round'] >=2 and message == 'n':
            user_wanna_end = True
            task['game-21']['mode'] = 0
            datastore_client.put(task)
        # 計算玩家與電腦的卡牌分數
        task['game-21']['user_score'] = calculate_score(task['game-21']['user_cards'])
        task['game-21']['computer_score'] = calculate_score(task['game-21']['computer_cards'])
        datastore_client.put(task)
        send = ""
        # 印出玩家抽到的牌與分數 & 電腦抽到的第一張牌
        if user_wanna_end is False:
            send = f"♣您的卡片: {task['game-21']['user_cards']}, 目前分數: {task['game-21']['user_score']}\n"
            send += f"♣電腦抽到的第一張卡: {task['game-21']['computer_cards'][0]}\n"
            send += "\n"
        # 檢查：如果玩家抽到blackjack或電腦抽到blackjack或玩家的牌已爆掉，則遊戲自動結束
        if task['game-21']['user_score'] == 0 or task['game-21']['computer_score'] == 0 or task['game-21']['user_score'] > 21 or user_wanna_end==True:
            task['game-21']['mode'] = 0
            datastore_client.put(task)
        # 如果沒有達成終止遊戲條件，則詢問玩家是否繼續抽牌
        else:
                send += "請問是否繼續抽牌？ 若要繼續抽請回答y,若不繼續請回答n"
                line_bot_api.reply_message(event.reply_token, TextSendMessage(send))

        # 最後結算(若遊戲達成自動終止條件或是玩家自己不想繼續抽牌)
        if task['game-21']['mode'] == 0 or user_wanna_end is True:
            # 確定遊戲將終止，電腦把牌抽完&結算分數
            while task['game-21']['computer_score'] != 0 and task['game-21']['computer_score'] < 17:
                task['game-21']['computer_cards'].append(deal_card())
                task['game-21']['computer_score'] = calculate_score(task['game-21']['computer_cards'])
                datastore_client.put(task)
                # 比較玩家與電腦的最終分數，比較結果
            j = json.load(open('game-21.json','r',encoding='utf-8'))
            j['body']['contents'][0]['text']= compare(task['game-21']['user_score'],task['game-21']['computer_score'])
            j['body']['contents'][1]['contents'][0]['contents'][1]['text'] = str(task['game-21']['user_cards'])
            j['body']['contents'][1]['contents'][1]['contents'][1]['text'] = str(task['game-21']['user_score'])
            j['body']['contents'][1]['contents'][2]['contents'][1]['text'] = str(task['game-21']['computer_cards'])
            j['body']['contents'][1]['contents'][3]['contents'][1]['text'] = str(task['game-21']['computer_score'])
            flex_message = FlexSendMessage(
                alt_text='final_result',
                contents=j
            )
            line_bot_api.reply_message(event.reply_token, flex_message)
    # ----------------------------------- 其他模式 --------------------------------------------------#

    elif "鼓勵" in message:
        j = json.load(open('quoting.json','r',encoding='utf-8'))
        j['body']['contents'][0]['contents'][0]['contents'][0]['text'] = get_quote()
        flex_message = FlexSendMessage(
            alt_text='quotes',
            contents=j
        )
        line_bot_api.reply_message(event.reply_token, flex_message)
    elif "遊戲" in message:
        j = json.load(open('game_menu.json','r',encoding='utf-8'))
        flex_message = FlexSendMessage(
            alt_text='game_menu',
            contents=j
        )
        line_bot_api.reply_message(event.reply_token, flex_message)

    elif "猜數字" in message:
        # 將遊戲數值初始化
        task['game-mode'] = 1
        task['score'] = 20
        datastore_client.put(task)
        j = json.load(open('guess_number_menu.json','r', encoding='utf-8'))
        flex_message = FlexSendMessage(
            alt_text='guess_number_menu',
            contents=j
        )
        line_bot_api.reply_message(event.reply_token, flex_message)

    elif "天氣" in message:
        task['weather-mode']=1
        datastore_client.put(task)
        line_bot_api.reply_message(event.reply_token, TextSendMessage("請輸入欲查詢之縣市，例:台北"))
    elif "21點" in message:
        task['game-21']['mode'] = 1
        task['game-21']['user_cards']=[]
        task['game-21']['computer_cards']=[]
        task['game-21']['user_score']=0
        task['game-21']['computer_score']=0
        task['game-21']['round']=0
        datastore_client.put(task)
        line_bot_api.reply_message(event.reply_token, TextSendMessage("歡迎來玩21點，請輸入y以抽卡"))

    elif message == "待辦":
        j = json.load(open('todo_start.json', 'r', encoding='utf-8'))
        flex_message = FlexSendMessage(
            alt_text='to-do',
            contents=j
        )
        line_bot_api.reply_message(event.reply_token, flex_message)

    elif "新增待辦" in message:
        task["add-mode"] = 2
        datastore_client.put(task)
        j = json.load(open('pick_date_to_add.json','r',encoding='utf-8'))
        flex_message = FlexSendMessage(
            alt_text='pick a date',
            contents=j
        )
        line_bot_api.reply_message(event.reply_token, flex_message)

    elif "查看" in message:
        j = json.load(open('to_do_menu.json','r',encoding='utf-8'))
        today = dt.now().date()
        tomorrow = str(today+timedelta(days=1))
        today_plus_2 = str(today+timedelta(days=2))
        today_plus_3 = str(today+timedelta(days=3))
        today_plus_4 = str(today+timedelta(days=4))
        label_list = ["今天","明天","後天",today_plus_3,today_plus_4,"其他日期"]
        day_list = [str(today),tomorrow,today_plus_2,today_plus_3,today_plus_4,"其他日期"]
        for i in range(len(j['footer']['contents'])):
            j['footer']['contents'][i]['action']['label'] = label_list[i]
            j['footer']['contents'][i]['action']['text'] = f"@{day_list[i]}"
        flex_message = FlexSendMessage(
            alt_text='to_do_menu',
            contents=j
        )
        task["view-mode"] = 1
        datastore_client.put(task)
        line_bot_api.reply_message(event.reply_token, flex_message)

    elif "+" in message:
        date = message.replace("+", "")
        task['date-to-add'] = date
        task['add-mode'] = 3
        datastore_client.put(task)
        line_bot_api.reply_message(event.reply_token, TextSendMessage("請輸入欲新增的待辦事項："))

    # 編輯待辦
    elif "#" in message:
        m = message.replace("#", "")
        send = f"您在{m}的待辦事項有:\n"
        m_to_send = display_to_do(send, task['to-do'][m])
        m_to_send += "\n"
        m_to_send += "\n請輸入欲編輯事項之編號："
        task['edit-mode'] = 1
        task['date-to-edit'] = m
        datastore_client.put(task)

        line_bot_api.reply_message(event.reply_token, TextSendMessage(m_to_send))

    # 刪除待辦
    elif "$" in message:
        m = message.replace("$", "")
        send = f"您在{m}的待辦事項有:\n"
        try:
            m_to_send = display_to_do(send, task['to-do'][m])
            m_to_send += "\n"
            m_to_send += "\n請輸入欲刪除事項之編號："
            task['delete-mode'] = 1
            task['date-to-delete'] = m
            datastore_client.put(task)
            line_bot_api.reply_message(event.reply_token, TextSendMessage(m_to_send))
        except:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(f"您在{m}尚未建立待辦事項"))

    # 顯示今日待辦
    elif message == "今日":
        today = dt.now().date()
        today = str(today)
        j = json.load(open('brown2.json','r',encoding='utf-8'))
        try:
            # 檢查該日期是否已建檔
            to_do = task['to-do'][today]
            # 可能該日期有建檔但裡面資料已被刪光, length為0
            if len(to_do) == 0:
                no_todo_found_reply(event, today)

            else:
                display_today(event,j,task,today)
        # 可能該日期尚未建檔
        except:
            no_todo_found_reply(event, today)

    elif message == "疑難雜症":
        j = json.load(open('questions.json','r',encoding='utf-8'))
        flex_message = FlexSendMessage(
            alt_text='contact',
            contents=j
        )
        line_bot_api.reply_message(event.reply_token, flex_message)

    else:
        message +=" 機器人讀取中..."
        line_bot_api.reply_message(event.reply_token, TextSendMessage(message))


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)