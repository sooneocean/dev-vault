#!/usr/bin/env python3
"""
快速預覽：優化 YOLO LAB 前 5 篇熱門文章
"""

import json
from ai_optimizer import AIOptimizer, Post, OptimizationResult
from cost_calculator import CostCalculator

# 前 5 篇熱門文章的實際數據
top_5_articles = [
    {
        "id": 34844,
        "title": "Kodaline 解散震撼彈！8/24 台北站告別巡演搶票全攻略",
        "content": """
青春裡的那首救贖之歌，Kodaline Farewell Tour 台北站最終告別

那些在無數個失眠夜晚單曲循環〈All I Want〉的日子裡，我們都在史蒂夫·加里根破碎卻溫柔的嗓音裡找到活下去的勇氣。13年的歲月裡，他們從都柏林街頭的青澀彈唱出發，一路陪伴我們走過失戀、迷惘與人生低谷。現在，這段互相扶持的旅程即將畫下句點。Kodaline 拋出了震撼彈，正式宣布解散並展開告別巡迴。

8月24日，台北國際會議中心（TICC）將化為全台灣最大的情緒收容所。Live Nation 會員請在4月1日上午11點就位，準備好你的手指搶先卡位。4月2日上午11點拓元售票系統全面啟動。
        """,
        "excerpt": "Kodaline 宣佈解散！這場 Farewell Tour 是你與青春和解的最後機會。15 億次點聽的〈All I Want〉將在 TICC 響起，8/24 僅此一場。別等遺憾才流淚，4/1 搶票戰開打，立即鎖定這張通往回憶的單程車票！",
        "category": "music",
        "views": 44
    },
    {
        "id": 34848,
        "title": "5/22 南港見！拍謝少年 x PEDRO 門票即將開賣，搶不到只能等死",
        "content": """
轟碎虛擬世界的指指點點：拍謝少年與PEDRO《Outta My Way》台日巡迴台灣場

你一定遇過這種狀況。一堆不認識的臉孔，帶著面具對你的生活指手畫腳。讚美也好，批評也罷，那些雜音把我們逼得喘不過氣。網路社群把所有人綁在一起，情緒的漩渦輕易吞噬了純粹的自我。拍謝少年懂這種感覺。他們找來日本龐克搖滾猛團 PEDRO，要陪我們一起吼出心底憋了許久的髒話。

5月22日南港 SUB Live，這場演出的每一張票，都是通往我們青春記憶的最後一張單程車票。
        """,
        "excerpt": "被社群雜音逼到窒息？拍謝少年聯手日本龐克 PEDRO 與傳奇吉他手田渕ひさ子，要用炸裂破音撕碎虛偽的面具。5/22 南港 SUB Live，這是一場集體釋放憤怒的搖滾救贖，限量預售票即將開搶，錯過這次，你還要憋多久？",
        "category": "music",
        "views": 39
    },
    {
        "id": 34853,
        "title": "4月2日算力大崩塌 ! OpenAI 算力配給真相：為什麼你的 20 美金買不到龍蝦的無限產能？",
        "content": """
算力配給制的殘酷真相：如何餵飽你大腦皮層上的 Openclaw「 龍蝦 」？

4月2日即將到來，一場無聲的數位限電即將席捲所有依賴 AI 的工作者。你或許以為每個月刷卡付給 OpenAI 的 20 美金，買到的是一個隨叫隨到的全知助理。現實極其骨感：你買的只是一張「限時限量」的算力配給票。

我們正處於一個前所未有的算力蜜月期，系統大發慈悲地給予了雙倍的運算額度，讓你產生了資源無限的錯覺。時間一到，閘門落下，習慣了暴飲暴食的生產力工作流，即將面臨嚴峻的斷糧危機。
        """,
        "excerpt": "別以為 20 美金能買到無限 AI！4 月 2 日算力配額即將腰斬，你的生產力流程正面臨斷電危機。本文揭露科技巨頭補貼背後的殘酷真相，並教你如何在算力飢荒中建立備援機制，避免在死線前退回石器時代。",
        "category": "tech",
        "views": 36
    },
    {
        "id": 34870,
        "title": "影史首部 MotoGP 授權！《Moto極速傳奇》竟讓攝影機在 300 公里搏命？",
        "content": """
視覺與聽覺的極限撕裂：全球首部 MotoGP 授權電影《Moto極速傳奇》大銀幕狂飆

準備好讓你的腎上腺素在影廳內徹底失控，這是全球賽車迷苦等十年的終極感官救贖。

拋棄那些依賴綠幕與劣質電腦動畫的工業流水線產品。導演麥特懷特克勞斯直接把攝影機架設在時速三百公里的重機上。這部耗費十年心血的巨作獲得 MotoGP 官方全面解禁授權。
        """,
        "excerpt": "拋棄綠幕假象！《Moto極速傳奇》直接將攝影機架在時速 300 公里的戰馬之上。這場賽車迷苦等十年的救贖，將於 5 月 8 日全台重磅引爆。準備好讓引擎聲浪撕裂感官，在大銀幕見證最硬核的賽道真章，錯過再等下個十年。",
        "category": "movies",
        "views": 32
    },
    {
        "id": 34875,
        "title": "伯朗黑糖奶茶實測：100%台灣黑糖重擊味蕾，35元挑戰手搖極限！",
        "content": """
封裝於580ml內的感官臨界點：伯朗黑糖奶茶的焦香革命

城市高壓生活需要一劑精準的糖分直擊，咱等的就是這口無須排隊的純粹爆發力。

研發團隊這次端出了怪物級的硬體規格。100%台灣在地黑糖構成風味引擎的絕對核心。高溫淬鍊出的炭焙焦香如同重低音般直擊味蕾。淡雅茶香與溫潤奶韻展現了精準的味覺調校。
        """,
        "excerpt": "伯朗這次來真的！100%台灣黑糖熬出爆發性炭焙焦香，580ml巨量只賣35元，直接對決街頭手搖店。這罐披著香檳金外衣的怪物級新品到底多神？立刻點擊解鎖冷藏櫃裡的味覺革命，用純粹太妃甜香拯救你的糖分焦慮！",
        "category": "lifestyle",
        "views": 28
    }
]

def main():
    optimizer = AIOptimizer()
    calculator = CostCalculator()

    print("=" * 80)
    print("🚀 YOLO LAB 前 5 篇熱門文章 SEO 優化預覽")
    print("=" * 80)

    results = []

    for i, article in enumerate(top_5_articles, 1):
        print(f"\n📄 [{i}/5] 文章 ID {article['id']} - 《{article['title'][:40]}...》")
        print(f"   類別: {article['category']} | 流量: {article['views']} views")
        print("-" * 80)

        # 構造 Post 對象
        post = Post(
            id=article['id'],
            title=article['title'],
            content=article['content'],
            excerpt=article['excerpt'],
            category=article['category'],
            views_30d=article['views']
        )

        # 執行優化
        print("   ⏳ 生成優化建議中...")
        try:
            result = optimizer.optimize_post(post)
            results.append(result)

            # 展示改前/改後
            print("\n   改前 (Before):")
            print(f"   ├─ Title ({len(article['title'])} 字): {article['title']}")
            print(f"   ├─ Description ({len(article['excerpt'])} 字): {article['excerpt'][:80]}...")

            print("\n   改後 (After):")
            title_opt = result.optimizations['titles'][0] if result.optimizations['titles'] else None
            if title_opt:
                print(f"   ├─ Title ({title_opt['length']} 字): {title_opt['text']}")

            if result.optimizations['description']:
                desc = result.optimizations['description']
                print(f"   ├─ Description ({len(desc)} 字): {desc[:80]}...")

            print(f"   ├─ 內部連結: +{len(result.optimizations['internal_links'])} 個")
            print(f"   └─ FAQ: +{len(result.optimizations['faq'])} 個問答")

        except Exception as e:
            print(f"   ❌ 錯誤: {str(e)}")

    # 成本估算
    print("\n\n" + "=" * 80)
    print("💰 成本估算")
    print("=" * 80)

    cost_opus = calculator.estimate_batch_cost(len(top_5_articles), model="opus")
    cost_sonnet = calculator.estimate_batch_cost(len(top_5_articles), model="sonnet")
    cost_haiku = calculator.estimate_batch_cost(len(top_5_articles), model="haiku")

    print(f"\n前 5 篇預覽成本:")
    print(f"  Opus 4.6:   ${cost_opus['total_cost']:.2f}")
    print(f"  Sonnet 4.6: ${cost_sonnet['total_cost']:.2f} ⭐ 推薦")
    print(f"  Haiku 4.5:  ${cost_haiku['total_cost']:.2f}")

    # 全 1000 篇 (Tier 1+2) 成本
    print(f"\n全 1000 篇 (Tier 1+2) 預估成本:")
    full_cost_opus = calculator.estimate_batch_cost(1000, model="opus")
    full_cost_sonnet = calculator.estimate_batch_cost(1000, model="sonnet")
    full_cost_haiku = calculator.estimate_batch_cost(1000, model="haiku")

    print(f"  Opus 4.6:   ${full_cost_opus['total_cost']:.2f}")
    print(f"  Sonnet 4.6: ${full_cost_sonnet['total_cost']:.2f} ⭐ 推薦")
    print(f"  Haiku 4.5:  ${full_cost_haiku['total_cost']:.2f}")

    # 導出結果
    print(f"\n📊 優化結果已保存到: top5_optimizations.jsonl")
    with open('top5_optimizations.jsonl', 'w', encoding='utf-8') as f:
        for result in results:
            f.write(result.to_json() + '\n')

    print("\n✅ 預覽完成！")
    print("   下一步：執行 batch_updater.py 進行實際推送")

if __name__ == "__main__":
    main()
