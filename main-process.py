import json
import multiprocessing
import os
import time
import uuid

import redis
import yaml
from revChatGPT.V1 import Chatbot


def config():
    try:
        with open("./config.yaml") as configFile:
            return yaml.load(stream=configFile, Loader=yaml.Loader)
    except Exception as e:
        raise RuntimeError("加载配置失败")


def ping(r):
    # 一直执行ping命令，防止连接丢失
    while 1:
        try:
            r.ping()
            print("ping redis %s, 剩余 %s 个任务" % (
                time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), myRedis.llen(REDIS_QUESTION_QUEUE)))
        except:
            pass
        finally:
            time.sleep(1)


def question(c, t):
    print("%s get a task %s" % (multiprocessing.current_process().name, t["message"]))
    chatbot = Chatbot(config={
        "access_token": c["chat"]["access_token"],
        "proxy": c["chat"]["proxy"],
        "accept_language": c["chat"]["accept_language"]
    })
    prevText = ""
    prevConversationId = ""
    for data in chatbot.ask(prompt=t["message"]):
        message = data["message"][len(prevText):]
        print(message, end="", flush=True)
        prevText = data["message"]
        prevConversationId = data["conversation_id"]
    print()

def answer1(q):
    while True:
        print(q.get())

def answer(a):
    print('end_time:', time.ctime())
    print(a)

def answer_error(e):
    print(e)

REDIS_QUESTION_QUEUE = "openai-chat-question"
REDIS_ANSWER_QUEUE = "openai-chat-answer"

# 每次启动服务时，切换id，避免遗留数据获取不到上下文导致出错
REDIS_CONVERSATION_ID_KEY = "openai-chat-cid-" + str(uuid.uuid4()) + "-"

QUESTION_COUNT = 1

if __name__ == '__main__':
    myConfig = config()
    redisPool = redis.ConnectionPool(host=myConfig["redis"]["host"],
                                     port=myConfig["redis"]["port"],
                                     username=myConfig["redis"]["username"],
                                     password=myConfig["redis"]["password"],
                                     db=myConfig["redis"]["database"])
    myRedis = redis.Redis(connection_pool=redisPool)
    myRedis.ltrim(REDIS_QUESTION_QUEUE, myRedis.llen(REDIS_QUESTION_QUEUE), 0)

    processPool = multiprocessing.Pool(processes=QUESTION_COUNT)
    processQueue = multiprocessing.Manager().Queue()

    while True:
        message = myRedis.rpop(REDIS_QUESTION_QUEUE)
        if message:
            task = json.loads(message)
            print(task)
            result = processPool.apply_async(func=question, args=(myConfig, task,), callback=answer, error_callback=answer_error)
            print(result)
        else:
            print("waiting.... %s " % (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))
            time.sleep(1)