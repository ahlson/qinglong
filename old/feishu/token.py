import os
import json
import requests
import time
from datetime import datetime

# ================== 配置 ==================
# 青龙会自动注入环境变量，无需修改代码
FEISHU_APP_ID = os.getenv("FEISHU_APP_ID", "").strip()
FEISHU_APP_SECRET = os.getenv("FEISHU_APP_SECRET", "").strip()

# 要更新的环境变量名（青龙中必须已存在这个变量）
TARGET_VAR_NAME = "FEISHU_TOKEN"

# 青龙开放API地址（根据你的青龙实际地址修改，端口和协议）
QL_URL = os.getenv("qinglong_host", "").strip()

# 青龙开放API的 Client ID 和 Client Secret（必须在青龙后台 → 系统设置 → 应用设置 中新建一个应用）
QL_CLIENT_ID = os.getenv("QL_CLIENT_ID", "").strip()
QL_CLIENT_SECRET = os.getenv("QL_CLIENT_SECRET", "").strip()

# =================================================
def get_ql_token():
    """获取青龙自身的开放API token"""
    if not QL_CLIENT_ID or not QL_CLIENT_SECRET:
        print("[ERROR] 未配置 QL_CLIENT_ID 或 QL_CLIENT_SECRET，无法更新环境变量")
        return None

    url = f"{QL_URL}/open/auth/token?client_id={QL_CLIENT_ID}&client_secret={QL_CLIENT_SECRET}"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        if data.get("code") == 200:
            return data["data"]["token"]
        else:
            print(f"[ERROR] 获取青龙token失败: {data}")
            return None
    except Exception as e:
        print(f"[ERROR] 请求青龙token异常: {e}")
        return None

def get_feishu_tenant_token():
    """获取飞书 tenant_access_token"""
    if not FEISHU_APP_ID or not FEISHU_APP_SECRET:
        print("[ERROR] 未配置 FEISHU_APP_ID 或 FEISHU_APP_SECRET")
        return None

    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    payload = {
        "app_id": FEISHU_APP_ID,
        "app_secret": FEISHU_APP_SECRET
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        data = resp.json()
        if data.get("code") == 0:
            token = data["tenant_access_token"]
            expire = data.get("expire", 7200)
            print(f"[SUCCESS] 获取飞书 token 成功，有效期 {expire} 秒")
            return token
        else:
            print(f"[ERROR] 获取飞书 token 失败: {data.get('msg')}")
            return None
    except Exception as e:
        print(f"[ERROR] 请求飞书接口异常: {e}")
        return None

def update_ql_env_var(token):
    """更新青龙环境变量 FEISHU_TOKEN"""
    ql_token = get_ql_token()
    if not ql_token:
        return False

    headers = {
        "Authorization": f"Bearer {ql_token}",
        "Content-Type": "application/json"
    }

    # 1. 先查询现有变量
    search_url = f"{QL_URL}/open/envs?searchValue={TARGET_VAR_NAME}"
    try:
        resp = requests.get(search_url, headers=headers, timeout=10)
        data = resp.json()
        if data.get("code") != 200:
            print(f"[ERROR] 查询环境变量失败: {data}")
            return False

        items = data.get("data", [])
        exist_item = None
        for item in items:
            if item.get("name") == TARGET_VAR_NAME:
                exist_item = item
                break

        # 2. 更新或新增
        if exist_item:
            # 更新（PUT）
            put_url = f"{QL_URL}/open/envs"
            payload = {
                "id": exist_item["id"],
                "name": TARGET_VAR_NAME,
                "value": token
            }
            resp = requests.put(put_url, headers=headers, json=payload, timeout=10)
        else:
            # 新增（POST）
            post_url = f"{QL_URL}/open/envs"
            payload = [{
                "name": TARGET_VAR_NAME,
                "value": token
            }]
            resp = requests.post(post_url, headers=headers, json=payload, timeout=10)

        result = resp.json()
        if result.get("code") == 200:
            print(f"[SUCCESS] 环境变量 {TARGET_VAR_NAME} 已更新为最新飞书 token")
            return True
        else:
            print(f"[ERROR] 更新环境变量失败: {result}")
            return False

    except Exception as e:
        print(f"[ERROR] 操作青龙环境变量异常: {e}")
        return False

def main():
    print(f"[START] 飞书 Token 更新任务 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    new_token = get_feishu_tenant_token()
    if not new_token:
        print("[END] 获取飞书 token 失败，任务结束")
        return

    success = update_ql_env_var(new_token)
    if success:
        print("[END] 飞书 token 已成功更新到青龙环境变量 FEISHU_TOKEN")
    else:
        print("[END] 更新环境变量失败，请检查青龙开放API配置")

if __name__ == "__main__":
    main()
