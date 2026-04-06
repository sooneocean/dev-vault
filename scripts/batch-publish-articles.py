#!/usr/bin/env python3
"""
WordPress REST API Batch Publisher
發佈 5 篇 Tech 文章到 yololab.net
使用方法: python batch-publish-articles.py
需要設置環境變量: WP_USER, WP_PASSWORD, WP_SITE
"""

import requests
import json
import sys
from datetime import datetime
import base64

# WordPress 配置
WP_SITE = "https://yololab.net"
WP_USER = "yololab.life@gmail.com"
WP_PASSWORD = "1jaT SIl8 rnuj fs4D 8OHK UdHT"

# 5 篇文章元數據 + 內容
ARTICLES = [
    {
        "title": "LLM模型完整對比2026｜GPT-4o vs Claude vs Gemini vs Llama最強評測",
        "slug": "llm-model-comparison-2026",
        "excerpt": "2026年LLM模型全面對比：性能、成本、速度完整評測。GPT-4o vs Claude 3.5 Opus vs Gemini 2.0最新對比。",
        "date": "2026-04-07T09:00:00",
        "categories": [96990383],
        "tags": ["LLM", "AI", "GPT-4", "Claude", "模型對比", "2026"],
        "content_file": "C:\\DEX_data\\Claude Code DEV\\resources\\llm-model-comparison-2026.md"
    },
    {
        "title": "提示詞工程完全指南｜Chain-of-Thought × Few-Shot × 角色扮演最強技巧",
        "slug": "prompt-engineering-complete-guide",
        "excerpt": "提示詞工程完全指南：Chain-of-Thought、Few-Shot、角色扮演等10大技巧。讓ChatGPT和Claude輸出品質翻倍的終極秘籍。",
        "date": "2026-04-08T09:00:00",
        "categories": [96990383],
        "tags": ["提示詞", "Prompt", "ChatGPT", "Claude", "AI使用技巧"],
        "content_file": "C:\\DEX_data\\Claude Code DEV\\resources\\prompt-engineering-complete-guide.md"
    },
    {
        "title": "AI智能體框架完全對比｜LangGraph vs Claude SDK vs AutoGPT 2026最新評測",
        "slug": "ai-agent-framework-comparison",
        "excerpt": "AI智能體完全對比：LangGraph vs Claude SDK vs AutoGPT。2026最強Agent框架選型指南。",
        "date": "2026-04-09T09:00:00",
        "categories": [96990383],
        "tags": ["AI Agent", "LangGraph", "Claude SDK", "智能體"],
        "content_file": "C:\\DEX_data\\Claude Code DEV\\docs\\articles\\2026-04-03-ai-agent-framework-comparison.md"
    },
    {
        "title": "向量數據庫選型指南2026｜Pinecone vs Weaviate vs Milvus vs Qdrant",
        "slug": "vector-database-selection-guide",
        "excerpt": "向量數據庫完整選型指南：Pinecone vs Weaviate vs Milvus成本對比。RAG系統最佳實踐。",
        "date": "2026-04-10T09:00:00",
        "categories": [96990383],
        "tags": ["向量數據庫", "Embedding", "RAG", "Pinecone"],
        "content_file": "C:\\DEX_data\\Claude Code DEV\\content\\vector-database-selection-guide-2026.md"
    },
    {
        "title": "AI編程助手工作流完整優化指南｜GitHub Copilot vs Claude Code vs Cursor",
        "slug": "ai-coding-assistant-workflow-optimization",
        "excerpt": "AI編程助手工作流完整優化指南：GitHub Copilot vs Claude Code vs Cursor效率對比。程式開發提效40%的終極秘籍。",
        "date": "2026-04-11T09:00:00",
        "categories": [96990383],
        "tags": ["GitHub Copilot", "Claude Code", "Cursor", "AI編程"],
        "content_file": "C:\\DEX_data\\Claude Code DEV\\docs\\articles\\2026-04-03-ai-coding-assistant-workflow-optimization.md"
    }
]

def read_article_content(file_path):
    """讀取文章內容"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"❌ 文件不存在: {file_path}")
        return None

def get_auth_header(user, password):
    """生成 Basic Auth 標頭"""
    credentials = f"{user}:{password}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return {"Authorization": f"Basic {encoded}"}

def get_or_create_tags(tag_names, auth_header):
    """獲取或創建標籤，返回標籤 ID 列表"""
    tag_ids = []

    for tag_name in tag_names:
        try:
            # 先查詢標籤是否已存在
            url = f"{WP_SITE}/wp-json/wp/v2/tags?search={tag_name}"
            response = requests.get(url, headers=auth_header, timeout=10)

            if response.status_code == 200:
                tags = response.json()
                if tags:
                    tag_ids.append(tags[0]['id'])
                else:
                    # 標籤不存在，創建新標籤
                    create_url = f"{WP_SITE}/wp-json/wp/v2/tags"
                    payload = {"name": tag_name}
                    create_response = requests.post(create_url, json=payload, headers=auth_header, timeout=10)
                    if create_response.status_code in [200, 201]:
                        tag_ids.append(create_response.json()['id'])
        except:
            pass

    return tag_ids

def publish_article(article_data, auth_header):
    """發佈單篇文章"""
    # 讀取文章內容
    content = read_article_content(article_data["content_file"])
    if not content:
        return False

    # 獲取或創建標籤 ID
    tag_ids = get_or_create_tags(article_data.get("tags", []), auth_header)

    # 準備 API 請求
    url = f"{WP_SITE}/wp-json/wp/v2/posts"

    payload = {
        "title": article_data["title"],
        "content": content,
        "excerpt": article_data["excerpt"],
        "date": article_data["date"],
        "status": "publish",
        "categories": article_data["categories"],
        "slug": article_data["slug"]
    }

    # 如果有標籤 ID，加入 payload
    if tag_ids:
        payload["tags"] = tag_ids

    # 添加元數據
    if tag_ids or article_data.get("tags"):
        payload["meta"] = {
            "internal_links": "ai-ide-agent-collaboration-survival-guide,ai-computing-power-rationing-survival,tech-pillar"
        }

    headers = {
        **auth_header,
        "Content-Type": "application/json"
    }

    try:
        print(f"\n📝 發佈: {article_data['title']}")
        print(f"   時間: {article_data['date']}")

        response = requests.post(url, json=payload, headers=headers, timeout=30)

        if response.status_code in [200, 201]:
            data = response.json()
            post_id = data.get('id')
            post_link = data.get('link')
            print(f"✅ 成功! ID: {post_id}")
            print(f"   URL: {post_link}")
            return True
        else:
            print(f"❌ 失敗 (HTTP {response.status_code})")
            print(f"   回應: {response.text[:200]}")
            return False

    except Exception as e:
        print(f"❌ 錯誤: {str(e)}")
        return False

def main():
    """主程式"""
    print("=" * 60)
    print("🚀 WordPress REST API 批量發佈工具")
    print("=" * 60)

    # 檢查憑證
    if not WP_USER or not WP_PASSWORD:
        print("\n❌ 錯誤: 未設置 WP_USER 或 WP_PASSWORD")
        print("\n設置方法:")
        print("1. 編輯此檔案，設置 WP_USER 和 WP_PASSWORD")
        print("2. 或設置環境變量:")
        print("   export WP_USER='your_username'")
        print("   export WP_PASSWORD='your_app_password'")
        sys.exit(1)

    # 生成認證標頭
    auth_header = get_auth_header(WP_USER, WP_PASSWORD)

    # 發佈文章
    success_count = 0
    for i, article in enumerate(ARTICLES, 1):
        print(f"\n[{i}/{len(ARTICLES)}]", end="")
        if publish_article(article, auth_header):
            success_count += 1

    # 總結
    print("\n" + "=" * 60)
    print(f"📊 發佈完成: {success_count}/{len(ARTICLES)} 篇成功")
    print("=" * 60)

    if success_count == len(ARTICLES):
        print("\n✅ 所有文章發佈成功!")
        print("\n📌 下一步: 提交 Google Search Console 索引")
        print("   文章 URL:")
        for article in ARTICLES:
            print(f"   - https://yololab.net/archives/{article['slug']}")
        return 0
    else:
        print(f"\n⚠️  {len(ARTICLES) - success_count} 篇發佈失敗，請檢查錯誤")
        return 1

if __name__ == "__main__":
    sys.exit(main())
