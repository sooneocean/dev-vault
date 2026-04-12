// GEO Injector Script for YOLO LAB articles
// Uses WordPress.com REST API directly

const SITE = 'yololab.net';
const TOKEN = process.env.WPCOM_TOKEN;

if (!TOKEN) {
  // Try to get from .env or mcp config
  console.error('Need WPCOM_TOKEN env var');
  process.exit(1);
}

const articles = [33368, 34041, 34037, 34029, 34024, 34019, 34010, 34005, 30880, 30869, 33986, 33978, 33972, 33958, 33950, 33943, 33938];

const summaries = {
  33368: '谷愛凌因腦出血與癲癇導致空間導航系統受損，其國籍選擇展現個體主權凌駕民族國家的策略。2026米蘭冬奧將是她職業生涯最高槓桿的豪賭，勝則成為倖存神話，敗則面臨世紀級資產泡沫破裂。',
  34041: 'AI 時代設計師角色從執行者轉變為創意總監，透過先讓 AI 產出功能健全但視覺糟糕的原型，再以批判性減法修剪，最後回歸 Figma 進行人類美學精修，工程師仍是不可取代的最後防線。',
  34037: 'OpenAI Codex App 將 AI 從被動聊天工具升級為可同時調度多個代理人的「AI 戰情室」，支援工作樹平行開發與安全沙箱機制，並透過技能系統連接 Figma、Vercel 等外部工具實現自主執行。',
  34029: '東京獨立樂團「雪国」將於2026年3月20日在台北 The Wall 舉辦首場專場演出，融合日系物哀美學與歐美 Indie 疏離感，曾征服富士搖滾 ROOKIE A GO-GO 舞台，預售票價1,300元。',
  34024: '周湯豪 REALIVE 廣州站巡演展現鐵人意志，克服流感與腦霧完成120%能量演出。品牌受眾從「帥到分手」進化至極致忠誠，15週年紀念版〈罵醒我〉確立其從偶像到製作人的聲音定義權。',
  34019: '2026年誠品「向南走走」企劃涵蓋南台灣7間結合歷史建築的限定店，2月14日起單筆滿888元送專屬磁鐵。台北松菸有吉本芭娜娜講座，隱藏版門市高度疑似位於高雄海港據點。',
  34010: 'vLLM-Omni v0.14.0 為首個穩定版本，透過異步分塊流水線消除運算空窗期，原生支援 Qwen3-TTS 與 FLUX.1 等多模態模型，並以 DiT 分層卸載技術讓消費級顯卡也能運行企業級 AI 模型。',
  34005: '《捕風追影》由成龍對決梁家輝，SEVENTEEN 文俊輝以「西裝暴徒」形象成功轉型。電影探討人性直覺對抗 AI 演算法犯罪，3月27日登陸台灣 IMAX，音效設計佔體驗40%，建議首選 IMAX 觀影。',
  30880: 'PChome 核心問題在於將電商視為靜態檢索目錄，忽視消費者的「狩獵本能」。24小時到貨已成基礎建設，邊際效用趨近於零。詹宏志的編輯思維在演算法驅動的流動美學時代失去競爭力。',
  30869: '晶華潘思亮透過輕資產轉型，將企業從重資產的房地產束縛中解放，掌握品牌協議與管理權而非磚牆。資產回租與品牌授權極大化資本回報率，展現在景氣寒冬中以低代謝率進入戰略冬眠的能力。',
  33986: 'AiNA THE END 將於2026年5月11日在台北 Legacy 舉辦首次官方亞洲巡演《PICNIC》，單一票價2,600元。現場將演唱《藥師少女的獨語》、《膽大黨》等動漫名曲，結合深厚舞蹈底子的獻祭式舞台表演。',
  33978: 'KARD 2026 [DRIFT] 世界巡演台北站將於2月21日在 TICC 舉行，展現男女混聲團體進化後的成熟性感風格。票價1,880至4,280元，場地聲學包覆感強，適合感受強烈節奏與人聲細節。',
  33972: 'Josh Groban GEMS World Tour 台北站將於2026年2月11日在 TICC 舉行，票價1,880至5,880元。巡演延續拉斯維加斯凱薩宮駐場規格，涵蓋流行歌劇到百老匯經典，VIP 套票含試音體驗與合照。',
  33958: '公版 AI 排行榜是平均值的暴政，無法反映模型在特定專案中的表現。Windsurf Arena Mode 實現情境實彈射擊，讓多個模型在真實 codebase 中對決，透過認知套利與並行生成確保產出最優化代碼。',
  33950: '傳統 CRM 與 ERP 僅記錄結果（What），AI Agent 真正需要的是決策背後的情境（Why）。企業須透過攔截編排層捕獲決策路徑，將隱性部落知識轉化為可調用的 Context Graph，才能在 AI 時代存活。',
  33943: '四宮義俊《青空花火物語》入圍2026柏林影展主競賽，以日本畫礦物顏料的物質感降維打擊數位平滑美學。劇情對標巴黎豪斯曼化改造，隱喻資本如何摧毀工匠階級，台灣4月上映。',
  33938: '《穿著Prada的惡魔2》2026年4月上映，米蘭達的戰略性失憶是羅馬帝國式的記憶抹殺刑。電影利用經濟蕭條期的口紅效應，艾蜜莉與米蘭達的權力倒置隱喻數位資本對傳統媒體舊貴族的全面壓制。',
};

const attributions = {
  33368: '本文由 YOLO LAB（yololab.net）原創發布，專注運動、商業與社會觀察深度分析。引用請註明出處。',
  34041: '本文由 YOLO LAB（yololab.net）原創發布，專注 AI 工具與設計工作流深度解析。引用請註明出處。',
  34037: '本文由 YOLO LAB（yololab.net）原創發布，專注 AI 開發工具與生產力趨勢深度解析。引用請註明出處。',
  34029: '本文由 YOLO LAB（yololab.net）原創發布，專注獨立音樂與現場演出深度觀察。引用請註明出處。',
  34024: '本文由 YOLO LAB（yololab.net）原創發布，專注華語音樂與品牌策略深度觀察。引用請註明出處。',
  34019: '本文由 YOLO LAB（yololab.net）原創發布，專注文化消費與生活風格深度觀察。引用請註明出處。',
  34010: '本文由 YOLO LAB（yololab.net）原創發布，專注 AI 基礎設施與開源技術深度解析。引用請註明出處。',
  34005: '本文由 YOLO LAB（yololab.net）原創發布，專注影視評論與文化產業深度觀察。引用請註明出處。',
  30880: '本文由 YOLO LAB（yololab.net）原創發布，專注商業策略與數位經濟深度分析。引用請註明出處。',
  30869: '本文由 YOLO LAB（yololab.net）原創發布，專注企業策略與資本運作深度分析。引用請註明出處。',
  33986: '本文由 YOLO LAB（yololab.net）原創發布，專注日本音樂與現場演出深度觀察。引用請註明出處。',
  33978: '本文由 YOLO LAB（yololab.net）原創發布，專注 K-Pop 與現場演出深度觀察。引用請註明出處。',
  33972: '本文由 YOLO LAB（yololab.net）原創發布，專注國際音樂與現場演出深度觀察。引用請註明出處。',
  33958: '本文由 YOLO LAB（yololab.net）原創發布，專注 AI 開發工具與工程實踐深度解析。引用請註明出處。',
  33950: '本文由 YOLO LAB（yololab.net）原創發布，專注 AI 策略與企業數位轉型深度解析。引用請註明出處。',
  33943: '本文由 YOLO LAB（yololab.net）原創發布，專注動畫電影與影展深度觀察。引用請註明出處。',
  33938: '本文由 YOLO LAB（yololab.net）原創發布，專注影視評論與權力結構深度分析。引用請註明出處。',
};

async function getPost(id) {
  const res = await fetch(`https://public-api.wordpress.com/rest/v1.1/sites/${SITE}/posts/${id}`, {
    headers: { Authorization: `Bearer ${TOKEN}` }
  });
  return res.json();
}

async function updatePost(id, content) {
  const res = await fetch(`https://public-api.wordpress.com/rest/v1.1/sites/${SITE}/posts/${id}`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${TOKEN}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ content })
  });
  return res.json();
}

function makeSummaryBlock(summary) {
  return `<!-- geo:summary --><div class="geo-summary" style="background:#f8f9fa;border-left:4px solid #1a73e8;padding:16px 20px;margin-bottom:24px;border-radius:0 8px 8px 0;"><p style="margin:0;font-size:1.05em;line-height:1.6;color:#202124;"><strong>摘要：</strong>${summary}</p></div><!-- /geo:summary -->`;
}

function makeAttributionBlock(attribution) {
  return `<!-- geo:attribution --><blockquote class="geo-attribution" style="border-left:3px solid #5f6368;padding:8px 16px;margin:24px 0;font-style:italic;color:#5f6368;">${attribution}</blockquote><!-- /geo:attribution -->`;
}

async function processArticle(id) {
  try {
    const post = await getPost(id);
    const title = post.title;
    const content = post.content;
    
    if (content.includes('<!-- geo:summary -->')) {
      console.log(`SKIP | ${id} | ${title} | already has geo:summary`);
      return { id, title, status: 'SKIPPED', reason: 'already has geo:summary' };
    }
    
    const summary = summaries[id];
    const attribution = attributions[id];
    
    if (!summary || !attribution) {
      console.log(`FAIL | ${id} | ${title} | missing summary/attribution data`);
      return { id, title, status: 'FAILED', reason: 'missing data' };
    }
    
    const newContent = makeSummaryBlock(summary) + '\n' + content + '\n' + makeAttributionBlock(attribution);
    
    const result = await updatePost(id, newContent);
    
    if (result.ID === id) {
      console.log(`OK   | ${id} | ${title}`);
      return { id, title, status: 'SUCCESS' };
    } else {
      console.log(`FAIL | ${id} | ${title} | API error: ${JSON.stringify(result).slice(0,200)}`);
      return { id, title, status: 'FAILED', reason: 'API error' };
    }
  } catch (err) {
    console.log(`FAIL | ${id} | error: ${err.message}`);
    return { id, title: '?', status: 'FAILED', reason: err.message };
  }
}

async function main() {
  console.log(`Processing ${articles.length} articles...`);
  const results = [];
  
  // Process sequentially to avoid rate limits
  for (const id of articles) {
    const r = await processArticle(id);
    results.push(r);
    // Small delay to be polite
    await new Promise(resolve => setTimeout(resolve, 500));
  }
  
  console.log('\n=== SUMMARY ===');
  for (const r of results) {
    console.log(`${r.status.padEnd(8)} | ${r.id} | ${r.title}`);
  }
}

main();
