PROJECT_NAME=w7-chat-proxy

APP_BASE=$(shell pwd)
APP_BIN=$(APP_BASE)/bin

build: clean
        pyinstaller -F -c main.py --name=${PROJECT_NAME}

clean:
        rm -rf ./build & rm -rf ./dist

help:
        @echo "make - 编译 Python 代码, 生成二进制文件"