# chatgpt-bridge

基于 https://github.com/acheong08/ChatGPT 项目，通过队列的形式与其它语言进行交互。

### 示例代码

#### 问题队列 openai-chat-question

```php
$message = [
    'session_id' => '123456789',
    'message' => '你好呀，今天天气如何'
];
Cache::lpush('openai-chat-question', json_encode($message));

$message = [
    'session_id' => '123456789',
    'message' => '我刚才问什么问题了？'
];
Cache::lpush('openai-chat-question', json_encode($message));

sleep(1);
```

#### 回答队列 openai-chat-answer

```php
while (true) {
    $message = Cache::rpop('openai-chat-answer');
    $message = json_decode($message, true);
    if (json_last_error() == JSON_ERROR_NONE) {
        echo $message['message'], PHP_EOL;
        ob_flush();
        flush();
    } else {
        sleep(1);
    }
}
```

#### 构建静像

```
docker build -t chat:v1.0.0 .
docker run --name chat -it -d -e REDIS_HOST=172.16.1.13 -e REDIS_DATABASE=11 -e REDIS_PORT=6379 -e REDIS_DATABASE=11 -e APP_DEBUG=true chat:v1.0.0
```