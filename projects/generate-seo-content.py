#!/usr/bin/env python3
"""
SEO 内容预生成器
为所有文章生成 SEO 标题和描述，输出为 JSON 格式供后续导入使用
"""

import json
import re
from datetime import datetime

# Page 6 已获取的实际文章数据
PAGES_DATA = {
    6: [
        {"id": 34196, "title": "笑聲背後的熱力學真相：為什麼幽默感是你最強的大腦冷卻系統", "excerpt": "別再以為笑只是情緒反應，這其實是一場精密的熱力學災難！本文從物理學視角拆解笑聲本質"},
        {"id": 34190, "title": "ADHD 奇點時刻：停止追求穩定輸出，靠 AI 協作拿回屬於你的創意主場", "excerpt": "還在為「沒定性」感到挫折？在 AI 時代，執行力已變廉價，你那關不掉的創意噪音才是真金"},
        {"id": 34185, "title": "OpenAI Frontier：當 AI 終於領到識別證，走進你的辦公室", "excerpt": "別再餵 ChatGPT 廢話了。OpenAI Frontier 賦予 AI 實體帳號與權限"},
        {"id": 34173, "title": "GPT-5.3-Codex 強勢登場：跨越程式界限，它是你最全能的數位白領", "excerpt": "別再把 AI 當成只會吐代碼的投幣機！GPT-5.3-Codex 實現了「自我進化」與「互動引導」"},
        {"id": 34171, "title": "16 個分身同時開工？Claude Opus 4.6 徹底終結 AI 單兵作戰時代", "excerpt": "還在把 AI 當聊天機器人？Claude Opus 4.6 引入「代理團隊」架構"},
        {"id": 34153, "title": "AI智能體正在覺醒？四塊拼圖決定它是助手還是生命 | Soul, User, Skills, Memory", "excerpt": "你的AI為什麼永遠像新手？四塊關鍵拼圖決定它是工具還是數位生命"},
        {"id": 34147, "title": "VIBE CODING 一週年! 從氛圍到工程：2026 年你必須掌握的 Agentic Engineering 開發新範式", "excerpt": "別再死背語法了！Andrej Karpathy 預言：99% 的程式碼將由 AI 生成"},
        {"id": 34136, "title": "2026 必看《潮鞋總動員》全解析：頂級嘻哈配音陣容與球鞋哲學辯證", "excerpt": "限量球鞋只是橡膠與布料？這部片會讓你重新定義信仰"},
        {"id": 34132, "title": "中華隊亮點：花滑李宇翔、競速滑冰陳映竹、雪車林欣蓉等七位好手", "excerpt": "別再說台灣沒雪了！2026米蘭冬奧中華隊強勢出征"},
        {"id": 34126, "title": "等了19年河正宇終於回歸！新劇《成為房東的方法》與5年祕戀喜訊全公開", "excerpt": "19年才等到這一次！影帝河正宇拋下大銀幕身段"},
        {"id": 34120, "title": "世紀血案電影爭議全解析：《世紀血案》如何面對林家 45 年的眼淚？", "excerpt": "林宅血案搬上大銀幕，這場「世紀血案」究竟是還原真相"},
        {"id": 34112, "title": "V.K克 2026 巡演攻略：台北私密、高雄壯闊，未發表新曲搶先聽", "excerpt": "還在聽數位音源？那只是 V.K克靈魂的碎屑"},
        {"id": 34108, "title": "拒絕平庸週二！Morgan Jay 音樂喜劇革命登台：把尷尬人生唱成傳奇", "excerpt": "別再隔著螢幕看短影音流口水！Morgan Jay 帶著 R&B 吉他空降台北"},
        {"id": 34104, "title": "別讓考卷成為遺書：鹿特丹影展《自殺通告》撕開菁英教育的窒息真相", "excerpt": "為什麼優等生的眼淚總是被隱藏？周冠威新作《自殺通告》在鹿特丹影展引爆"},
        {"id": 34099, "title": "2026 浮現祭生存指南：紫雨林強勢回歸、百組陣容解構，直衝清水冒險", "excerpt": "拋棄冬天的陰鬱！2026 浮現祭聯手韓國傳奇紫雨林"},
        {"id": 34091, "title": "龍蝦智能體：當 AI 擁有人格與獨立 ID，這場轉型革命你跟上了嗎？", "excerpt": "別再只會把 AI 當搜尋工具。AI 正在領取身分證"},
        {"id": 34086, "title": "SPEC driven?別再寫幾十頁指令！為什麼「完美計畫」正毀掉你的 AI 專案？", "excerpt": "耗費數小時寫規格文檔卻換來平庸成果？別再用過時的瀑布流思維"},
        {"id": 34082, "title": "AI 正在重新定義「價值」：從矽谷傳奇投資人 Marc Andreessen 的反直覺預判", "excerpt": "算力已商品化，平庸將被放大，但卓越將變得更貴"},
        {"id": 34077, "title": "為何努力沒用？富蘭克林藏了 200 年的「人類作業系統」開源了", "excerpt": "別再盲目努力！富蘭克林之所以從學徒翻身為巨人"},
        {"id": 34072, "title": "等了18年的平交道！【秒速5公分真人版】如何用132頁數據重現新海誠孤寂？", "excerpt": "曾讓你心碎的平交道，這次以「職人級」誠意重現"}
    ]
}

class SEOContentGenerator:
    """SEO 内容生成器"""

    def generate_title(self, original_title: str) -> str:
        """生成 SEO 标题 (55-60 字符)"""
        # 清理 HTML 和特殊字符
        title = self._clean_html(original_title)

        # 限制长度
        if len(title) > 60:
            # 尝试在标点符号处截断
            for i in range(60, 50, -1):
                if title[i] in '，、；：':
                    return title[:i]
            return title[:57] + "..."
        return title

    def generate_description(self, excerpt: str, title: str = "") -> str:
        """生成 SEO 描述 (155-160 字符)"""
        excerpt = self._clean_html(excerpt)

        # 补充上下文
        if len(excerpt) < 150 and title:
            # 从标题提取关键词作为补充
            keywords = title.split('：')[0] if '：' in title else title.split('|')[0]
            excerpt = f"{excerpt} 深入了解{keywords}的前景与影响。"

        # 限制长度
        if len(excerpt) > 160:
            return excerpt[:157] + "..."
        return excerpt

    def _clean_html(self, text: str) -> str:
        """清理 HTML"""
        # 移除 HTML 标签
        text = re.sub(r'<[^>]+>', '', text)
        # 替换 HTML 实体
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&#038;', '&')
        # 移除多余空格
        text = ' '.join(text.split())
        return text.strip()

    def generate_all_seo(self, pages_data: dict) -> dict:
        """为所有文章生成 SEO 内容"""
        result = {}

        for page_num, posts in pages_data.items():
            result[page_num] = []
            for post in posts:
                post_id = post['id']
                title = post['title']
                excerpt = post['excerpt']

                seo_title = self.generate_title(title)
                seo_desc = self.generate_description(excerpt, title)

                result[page_num].append({
                    'id': post_id,
                    'original_title': title,
                    'seo_title': seo_title,
                    'seo_title_length': len(seo_title),
                    'seo_description': seo_desc,
                    'seo_description_length': len(seo_desc)
                })

        return result

def main():
    generator = SEOContentGenerator()

    # 生成 SEO 内容
    seo_content = generator.generate_all_seo(PAGES_DATA)

    # 输出为 JSON
    output = {
        'generated_at': datetime.now().isoformat(),
        'total_pages': len(seo_content),
        'total_posts': sum(len(posts) for posts in seo_content.values()),
        'pages': seo_content
    }

    # 保存到文件
    output_file = '/c/DEX_data/Claude Code DEV/projects/seo-content-generated.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"✅ SEO 内容已生成")
    print(f"📊 统计：{output['total_posts']} 篇文章")
    print(f"💾 保存到：{output_file}")

    # 显示样本
    print(f"\n📋 样本预览 (Post 34196):")
    sample = seo_content[6][0]
    print(f"  原标题: {sample['original_title']}")
    print(f"  SEO标题: {sample['seo_title']} ({sample['seo_title_length']}字)")
    print(f"  SEO描述: {sample['seo_description'][:80]}... ({sample['seo_description_length']}字)")

if __name__ == '__main__':
    main()
