import Anthropic from "@anthropic-ai/sdk";
import fs from "fs";

const client = new Anthropic();

const articles = [
  {
    id: 34372,
    title: "2026 年，陳孟賢到底在密謀什麼？隱忍 12 年的「全球巨星」攻頂計畫正式揭幕",
    excerpt: "如果你還僅止於把陳孟賢當成諧星，那你完全錯過了一個時代的崛起。這場 12 年的血淚承諾，不僅僅是生日會上的淚水，更是直指 2026 年個人演唱會的攻頂宣告。看他如何從 150 萬銷售額的帶貨王，跨界春河劇團淬鍊演技，並佈局兩年後的巔峰舞台。"
  },
  {
    id: 34366,
    title: "《捕風追影》7-11 預售攻略：搶文俊輝限量小卡與手繪看板打卡點",
    excerpt: "拒絕數位海報的冰冷！《捕風追影》聯手台南全美戲院手繪看板，讓成龍、梁家輝的熱血重現。2/17 鎖定 7-11 ibon 預售，入手文俊輝限量小卡與 3D 特典。"
  },
  {
    id: 34350,
    title: "LangChain 入門全解析：從地基架構到 LCEL 語法，打造永不過時的 AI 自動化流水線",
    excerpt: "還在乾等 AI 吐字？LangChain 讓你的 ChatGPT 具備連網、查資料與寄信的實戰力。本文拆解核心架構與 LCEL 語法，教你如何透過積木式開發打造高效、可監控且永不過時的 AI 生產線。"
  },
  {
    id: 34345,
    title: "【深度解讀】告別「單打獨鬥」的超級實習生：為什麼 Kimi 讓一百個 AI 同時為你打工，是通往未來的鑰匙？",
    excerpt: "還在等 AI 一次讀一份檔案？Kimi Agent Swarm 直接幫你雇 100 個員工，同步處理財報、寫論文、策劃產品。效率暴增 4.5 倍，這不再是工具升級，而是生產力降維打擊。"
  },
  {
    id: 34338,
    title: "2026 台中走春必去！ericoco 小虎馬限時快閃，四大療癒展區與拍貼攻略全解析",
    excerpt: "2026 開年最療癒的集體儀式！台中金典攜手 ericoco 打造 2.8 公尺巨型「小虎馬」，用醜萌美學暴力洗刷你的整年鳥事。展期僅 18 天，不收門票，只收你疲憊的靈魂。"
  },
  {
    id: 34331,
    title: "Apink 台北演唱會 3/7 開唱！15 年吞 CD 實力，Panda 必衝的巔峰盛宴",
    excerpt: "別再說二代女團回不來！Apink 迎來 15 週年巔峰，3/7 在 TICC 直球對決。想親耳體驗穿透天靈蓋的「吞 CD」實力？本篇彙整門票價格、優先購票時程與必看亮點。"
  },
  {
    id: 34325,
    title: "通心粉鉛筆 2026 台北開唱：Zepp 現場找回失落青春",
    excerpt: "別再隔著耳機流淚！通心粉鉛筆 2026 台北演唱會強勢降臨，剛結束巡演的「完全體」將帶來台灣限定私房歌單。這不是普通的表演，而是你與青春最深刻的對話。"
  },
  {
    id: 34317,
    title: "2026 LiSA 台北演唱會懶人包：攻蛋門票實名制、登記時間與 15 週年約定",
    excerpt: "終於等到 LiSA 攻下台北小巨蛋！這場 15 週年約定不容閃失。全面解析實名制抽選機制與搶票時程，徹底斷絕黃牛干擾。"
  },
  {
    id: 34310,
    title: "brkfstblend 台北專場攻略：Yogee 與 LUCKY TAPES 靈魂成員集結",
    excerpt: "還在耳機裡複習 LUCKY TAPES 的貝斯線？brkfstblend 帶著 Fuji Rock 震撼律動直衝台北左輪！集結東京獨立樂界精銳，這場全明星專場預售票僅 800 元，開賣即秒殺。"
  },
  {
    id: 34305,
    title: "黎智英獲刑 20 年：法庭上那抹最後的微笑，刻下香港新聞自由的終局",
    excerpt: "黎智英被重判 20 年，他在西九龍法院外的微笑讓政權顫抖。這是一場關於尊嚴的示範課，也是 78 歲老人用肉身寫下的最後社論。"
  }
];

async function generateSEO(title, excerpt) {
  const message = await client.messages.create({
    model: "claude-opus-4-6",
    max_tokens: 300,
    messages: [
      {
        role: "user",
        content: `快速優化中文 SEO 標題和描述，適合音樂/電影/科技/新聞主題。

**原標題：** ${title}
**摘要：** ${excerpt || "無"}

返回 JSON：
{
  "optimizedTitle": "45-60字內，含關鍵詞，吸引人",
  "metaDescription": "120-160字內，具體、有吸引力、包含主要訊息"
}`,
      },
    ],
  });

  const text = message.content[0].text;
  const match = text.match(/\{[\s\S]*\}/);
  if (!match) throw new Error("No JSON in response");
  return JSON.parse(match[0]);
}

async function main() {
  console.log("🚀 批次 6 (page=9): 生成 SEO 優化\n");
  const results = [];

  for (const article of articles) {
    try {
      console.log(`⏳ 處理文章 #${article.id}...`);
      const seo = await generateSEO(article.title, article.excerpt);
      results.push({
        id: article.id,
        optimizedTitle: seo.optimizedTitle,
        metaDescription: seo.metaDescription,
      });
      console.log(`✅ #${article.id} (${seo.optimizedTitle.length}字)`);
    } catch (error) {
      console.log(`❌ #${article.id}: ${error.message}`);
    }
  }

  console.log(`\n✅ 完成: ${results.length}/10 篇`);
  fs.writeFileSync("seo-optimization-output/batch6_seo.json", JSON.stringify(results, null, 2));
  console.log("💾 已保存到 seo-optimization-output/batch6_seo.json");
}

main().catch(console.error);
