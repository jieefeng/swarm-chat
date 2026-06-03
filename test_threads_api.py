import requests
import json

BASE_URL = "http://localhost:7010"
HEADERS = {"X-API-Key": "dev-secret-key", "Content-Type": "application/json"}

print("=== 测试会话 API ===\n")

# 测试 1: 创建会话
print("1. 创建会话...")
resp1 = requests.post(f"{BASE_URL}/api/threads",
                      json={"title": "测试会话 1"},
                      headers=HEADERS)
print(f"   状态码: {resp1.status_code}")
print(f"   响应: {resp1.json()}")
thread1_id = resp1.json().get("id")

resp2 = requests.post(f"{BASE_URL}/api/threads",
                      json={"title": "测试会话 2"},
                      headers=HEADERS)
print(f"   状态码: {resp2.status_code}")
print(f"   响应: {resp2.json()}")
thread2_id = resp2.json().get("id")

# 测试 2: 获取会话列表
print("\n2. 获取会话列表...")
resp = requests.get(f"{BASE_URL}/api/threads", headers=HEADERS)
print(f"   状态码: {resp.status_code}")
threads = resp.json().get("threads", [])
print(f"   会话数量: {len(threads)}")
for t in threads:
    print(f"   - {t['id']}: {t['title']}")

# 测试 3: 获取会话消息
print("\n3. 获取会话消息...")
resp = requests.get(f"{BASE_URL}/api/threads/{thread1_id}/messages", headers=HEADERS)
print(f"   状态码: {resp.status_code}")
print(f"   消息数量: {len(resp.json().get('messages', []))}")

# 测试 4: 删除会话
print("\n4. 删除会话...")
resp = requests.delete(f"{BASE_URL}/api/threads/{thread2_id}", headers=HEADERS)
print(f"   状态码: {resp.status_code}")
print(f"   响应: {resp.json()}")

# 测试 5: 验证删除后列表
print("\n5. 验证删除后列表...")
resp = requests.get(f"{BASE_URL}/api/threads", headers=HEADERS)
threads = resp.json().get("threads", [])
print(f"   会话数量: {len(threads)}")
for t in threads:
    print(f"   - {t['id']}: {t['title']}")

print("\n=== 测试完成 ===")