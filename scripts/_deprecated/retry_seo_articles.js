import Anthropic from "@anthropic-ai/sdk";

const client = new Anthropic();

const articles = [
  {
    id: 19835,
    title: "新・里見八犬傳 4K修復影評：真田廣之與藥師丸博子的搖滾特攝神話",
    excerpt: "傳說再臨！深作欣二執導、真田廣之與藥師丸博子主演的《新・里見八犬傳》4K修復版上映。解析這部創下23億票房的昭和經典，如何以西洋搖滾撞擊東方武俠，定義了日本特攝電影的黃金年代。"
  },
  {
    id: 19718,
    title: "《你是我眼中的那道光》勇奪哥譚獎最佳國際電影 |描述居住在孟買的三個女人，她們的愛情與夢想的故事",
    excerpt: "印度女性電影《你是我眼中的那道光》繼勇奪坎城影展評審團大獎後，再次搶下哥譚獎「最佳國際電影」大獎。該片是導演帕亞爾卡帕迪亞的首部劇情片，描述居住在孟買的三個女人的愛情與夢想故事。"
  },
  {
    id: 19706,
    title: "《死命必達》年度壓軸『驚喜』火速登台，初戀男神馬力歐、頂流女星Freen 最強合體跨年！",
    excerpt: "2024年末壓軸泰式恐怖喜劇《死命必達》，將於12月27日全台大銀幕上映。主演陣容包括國民初戀男神馬力歐莫瑞爾與近期大熱的頂流女星莎露彩查金哈兩人共同演出，打造一場兼具歡樂與微驚悚的驚喜冒險。"
  },
  {
    id: 19800,
    title: "《忍者亂太郎》回來了 《劇場版 忍者亂太郎 毒竹忍者隊最強之軍師》帶來最強回憶殺 台灣將於2025年1月29日大年初一上映 陪伴觀眾開心賀歲",
    excerpt: "日本國民動畫《忍者亂太郎》誕生至今31年，今年《劇場版忍者亂太郎毒竹忍者隊最強之軍師》將帶著史上最強「忍蛋」強勢回歸，將於明年賀歲檔1月29日全台上映，熱血與感動兼具的全新冒險即將引爆大銀幕。"
  }
];

async function generateSEOOptimization(article) {
  const prompt = `你是專業的Traditional Chinese SEO 優化專家。

分析以下文章，生成最優化的SEO標題和Meta Description。

**原始標題：**
${article.title}

**文章摘要：**
${article.excerpt || "（無摘要）"}

**優化要求：**
1. SEO標題（jetpack_seo_html_title）：45-60字，自然包含主要關鍵字，提高點擊率
2. Meta Description（advanced_seo_description）：120-160字，自然流暢，清楚說明內容價值，適合Google搜尋結果展示

**回應格式（JSON）：**
{
  "jetpack_seo_html_title": "最優化的標題",
  "advanced_seo_description": "最優化的描述"
}`;

  try {
    const message = await client.messages.create({
      model: "claude-opus-4-6",
      max_tokens: 500,
      messages: [
        {
          role: "user",
          content: prompt,
        },
      ],
    });

    const content = message.content[0];
    if (content.type !== "text") {
      throw new Error("Unexpected response type from Claude");
    }

    const jsonMatch = content.text.match(/\{[\s\S]*\}/);
    if (!jsonMatch) {
      throw new Error("No JSON found in response");
    }
    
    return JSON.parse(jsonMatch[0]);
  } catch (error) {
    console.error(`Failed to generate SEO for article ${article.id}:`, error.message);
    throw error;
  }
}

async function main() {
  console.log("🔄 Generating optimized SEO metadata for 4 retry articles...\n");
  
  const results = [];
  
  for (const article of articles) {
    console.log(`Processing article #${article.id}...`);
    try {
      const seoData = await generateSEOOptimization(article);
      results.push({
        id: article.id,
        ...seoData
      });
      console.log(`✅ Generated SEO metadata`);
      console.log(`   Title: ${seoData.jetpack_seo_html_title}`);
      console.log(`   Description: ${seoData.advanced_seo_description.substring(0, 80)}...\n`);
      
      // Rate limiting
      await new Promise((resolve) => setTimeout(resolve, 500));
    } catch (error) {
      console.error(`❌ Failed for article #${article.id}: ${error.message}\n`);
    }
  }
  
  console.log("\n📋 Generated SEO Metadata Summary:\n");
  console.log(JSON.stringify(results, null, 2));
}

main().catch(console.error);
