#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试讯飞API WebSocket连接
"""

import os
import json
import time
import hmac
import hashlib
import base64
import websocket
from pathlib import Path


def load_config():
    """从.env文件加载配置"""
    env_path = Path(__file__).resolve().parent.parent / "config" / ".env"
    print(f"[INFO] 加载配置文件: {env_path}")
    
    if not env_path.exists():
        print(f"[ERROR] 配置文件不存在: {env_path}")
        return None
    
    config = {}
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                key, value = line.split('=', 1)
                # 去除可能的引号和空格
                value = value.strip().strip('"').strip("'")
                config[key] = value
        
        # 验证必要的配置
        required_keys = ['XF_APP_ID', 'XF_API_KEY', 'XF_API_SECRET']
        for key in required_keys:
            if key not in config or not config[key]:
                print(f"[ERROR] 缺少必要的配置: {key}")
                return None
        
        print("[INFO] 配置加载成功")
        print(f"[INFO] APP_ID: {config['XF_APP_ID'][:4]}****")
        print(f"[INFO] API_KEY: {config['XF_API_KEY'][:4]}****")
        print(f"[INFO] API_SECRET: {config['XF_API_SECRET'][:4]}****")
        
        # 设置默认值
        config.setdefault('XF_DOMAIN', 'ultra')
        print(f"[INFO] DOMAIN: {config['XF_DOMAIN']}")
        
        return config
    except Exception as e:
        print(f"[ERROR] 加载配置时出错: {str(e)}")
        return None


def generate_signature(api_secret, timestamp):
    """生成签名"""
    # 拼接字符串
    message = f"host: spark-api.xf-yun.com\ndate: {timestamp}\nGET /v3.1/chat HTTP/1.1"
    print(f"[DEBUG] 签名消息: {repr(message)}")
    
    # 使用api_secret对message进行hmac-sha256加密
    signature = hmac.new(
        api_secret.encode('utf-8'),
        message.encode('utf-8'),
        digestmod=hashlib.sha256
    ).digest()
    
    # 对结果进行base64编码
    signature = base64.b64encode(signature).decode('utf-8')
    print(f"[DEBUG] 生成的签名: {signature[:20]}...")
    return signature


def build_url(config):
    """构建WebSocket连接URL"""
    timestamp = time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime())
    print(f"[DEBUG] 生成的时间戳: {timestamp}")
    
    signature = generate_signature(config['XF_API_SECRET'], timestamp)
    
    # 构建URL
    url = f"wss://spark-api.xf-yun.com/v3.1/chat?app_id={config['XF_APP_ID']}&api_key={config['XF_API_KEY']}&signature={signature}&date={timestamp}&host=spark-api.xf-yun.com"
    
    # 打印隐藏敏感信息的URL
    masked_url = url.replace(config['XF_API_KEY'], '****').replace(signature, '****')
    print(f"[INFO] 生成的WebSocket URL: {masked_url}")
    return url


def test_connection():
    """测试与讯飞API的WebSocket连接"""
    print("\n=== 开始测试讯飞API WebSocket连接 ===\n")
    
    # 加载配置
    config = load_config()
    if not config:
        print("[ERROR] 配置加载失败，无法继续测试")
        return False
    
    # 构建URL
    url = build_url(config)
    
    # 测试连接
    print("\n[INFO] 开始建立WebSocket连接...")
    ws = None
    try:
        # 建立连接
        ws = websocket.create_connection(url, timeout=10)
        print("[INFO] WebSocket连接成功建立")
        
        # 构建测试请求
        test_prompt = "你好，这是一个测试请求"
        request_data = {
            "header": {
                "app_id": config['XF_APP_ID'],
                "uid": "test_user"
            },
            "parameter": {
                "chat": {
                    "domain": config['XF_DOMAIN'],
                    "temperature": 0.7,
                    "max_tokens": 100
                }
            },
            "payload": {
                "message": {
                    "text": [
                        {"role": "user", "content": test_prompt}
                    ]
                }
            }
        }
        
        # 发送请求
        print(f"[INFO] 发送测试请求: {test_prompt}")
        ws.send(json.dumps(request_data))
        print("[INFO] 请求发送成功")
        
        # 接收响应
        print("[INFO] 等待API响应...")
        result = ""
        start_time = time.time()
        timeout = 30
        
        while time.time() - start_time < timeout:
            try:
                # 设置接收超时
                ws.settimeout(5)
                message = ws.recv()
                print(f"[DEBUG] 收到消息: {message[:200]}...")
                
                # 解析响应
                data = json.loads(message)
                
                # 检查错误
                header = data.get('header', {})
                code = header.get('code', 0)
                if code != 0:
                    error_msg = f"API错误: {header.get('message', '未知错误')} (代码: {code})"
                    print(f"[ERROR] {error_msg}")
                    return False
                
                # 提取内容
                payload = data.get('payload', {})
                choices = payload.get('choices', {})
                status = choices.get('status', 0)
                text = choices.get('text', [])
                
                if text:
                    for item in text:
                        if 'content' in item:
                            result += item['content']
                            print(f"[INFO] 收到响应内容: {item['content']}")
                
                # 检查是否结束
                if status == 2:
                    print("[INFO] API响应完成")
                    break
                    
            except websocket.WebSocketTimeoutException:
                print("[WARNING] WebSocket接收超时")
                continue
            except json.JSONDecodeError:
                print("[WARNING] 收到非JSON消息")
                continue
            except Exception as e:
                print(f"[ERROR] 处理消息时出错: {str(e)}")
                break
        
        # 检查结果
        if result:
            print(f"\n[SUCCESS] 测试成功! 收到响应: {result}")
            return True
        else:
            print("[ERROR] 未收到API响应内容")
            return False
            
    except Exception as e:
        print(f"[ERROR] 连接测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if ws:
            try:
                ws.close()
                print("[INFO] WebSocket连接已关闭")
            except:
                pass
    

if __name__ == "__main__":
    success = test_connection()
    print(f"\n=== 测试结果: {'成功' if success else '失败'} ===")