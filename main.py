import json
import logging
import threading
import time
import uuid

import redis
import erb.yml as yaml
from revChatGPT.V1 import Chatbot


def config():
    try:
        with open("./config.yaml") as configFile:
            return yaml.load(configFile.read())
    except Exception as e:
        raise RuntimeError("加载配置失败")


def ping(r):
    # 一直执行ping命令，防止连接丢失
    while 1:
        try:
            r.ping()
            logging.debug("ping redis %s, 剩余 %s 个任务" % (
            time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), myRedis.llen(REDIS_QUESTION_QUEUE)))
        except:
            pass
        finally:
            time.sleep(1)


def question():
    c = chatbotList[threading.current_thread().name]
    print(c)
    while 1:
        message = myRedis.rpop(REDIS_QUESTION_QUEUE)
        if message:
            task = json.loads(message)
            print("%s get a task %s" % (threading.current_thread().name, task["message"]))

            prev_text = ""
            conversationId = myRedis.get(REDIS_CONVERSATION_ID_KEY + task["session_id"])
            if not conversationId:
                conversationId = None
            else:
                conversationId = conversationId.decode()

            for data in c.ask(prompt=task["message"], conversation_id=conversationId):
                message = data["message"][len(prev_text):]
                print(message, end="", flush=True)
                prev_text = data["message"]
                if data["conversation_id"]:
                    myRedis.set(REDIS_CONVERSATION_ID_KEY + task["session_id"], str(data["conversation_id"]))
                myRedis.lpush(REDIS_ANSWER_QUEUE, json.dumps({"session_id": task["session_id"], "message": message}))
            print(chatbot.conversation_mapping)
            print()


def answer():
    pass


REDIS_QUESTION_QUEUE = "openai-chat-question"
REDIS_ANSWER_QUEUE = "openai-chat-answer"

# 每次启��服务时，切换id，避免遗留数据获取不到上下文导致出错
REDIS_CONVERSATION_ID_KEY = "openai-chat-cid-" + str(uuid.uuid4()) + "-"

QUESTION_COUNT = 1

if __name__ == '__main__':
    myConfig = config()
    redisPool = redis.ConnectionPool(host=myConfig["redis"]["host"],
                                     port=myConfig["redis"]["port"],
                                     password=myConfig["redis"]["password"],
                                     db=myConfig["redis"]["database"])
    myRedis = redis.Redis(connection_pool=redisPool)
    myRedis.ltrim(REDIS_QUESTION_QUEUE, myRedis.llen(REDIS_QUESTION_QUEUE), 0)
    myRedis.ltrim(REDIS_ANSWER_QUEUE, myRedis.llen(REDIS_ANSWER_QUEUE), 0)

    if myConfig["app"]['debug']:
        logging.basicConfig(filename='run.log', encoding='utf-8', level=logging.DEBUG)

    chatbot = Chatbot(config={
        "access_token": myConfig["chat"]["access_token"],
        "proxy": myConfig["chat"]["proxy"],
        "accept_language": myConfig["chat"]["accept_language"]
    })

    threadList = []
    chatbotList = {}
    threadPing = threading.Thread(target=ping, args=(myRedis,), daemon=True)
    threadList.append(threadPing)
    threadLock = threading.Lock()

    for i in range(QUESTION_COUNT):
        chatbotList["Q%s" % i] = Chatbot(config={
            "access_token": myConfig["chat"]["access_token"],
            "proxy": myConfig["chat"]["proxy"],
            "accept_language": myConfig["chat"]["accept_language"]
        })
        threadQuestion = threading.Thread(target=question, name="Q%s" % i)
        threadList.append(threadQuestion)

    for th in threadList:
        th.start()