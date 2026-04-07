#Codex開發文件包：動態疊加物追蹤、替換、遮蔽與局部重建系統

這是一套可直接丟給Codex開始拆專案的文件包，定位為**合法授權素材**的後期處理流程。

適用用途：
-自有品牌影片中的台標、角標、字幕條、下三分之一資訊條替換
-隱私資訊遮蔽
-廣播圖文包改版
-內部審片與後期修補
-對授權素材中的動態疊加物做追蹤、替換、遮蔽與局部重建

不適用用途：
-未授權素材的保護標記移除
-規避版權或所有權保護
-以還原第三方原始內容為目的的流程設計

##文件清單
-`PROJECT_BLUEPRINT.md`：完整技術設計文件
-`AGENTS.md`：放在專案根目錄給Codex讀的長期規則
-`CODEX_TASK_KICKOFF.md`：第一次下任務給Codex時可直接貼上的prompt
-`IMPLEMENTATION_PHASES.md`：Phase 1到Phase 4的開發拆解
-`CONFIG_SCHEMA.md`：設定檔與資料結構設計
-`PROJECT_TREE.md`：專案資料夾結構與每個模組責任

##建議使用方式
1.先把`AGENTS.md`放進專案根目錄
2.把`PROJECT_BLUEPRINT.md`與`CONFIG_SCHEMA.md`一起放進repo
3.開新專案後，先把`PROJECT_TREE.md`建立成實際資料夾
4.把`CODEX_TASK_KICKOFF.md`整段丟給Codex
5.先做CLI MVP，不要一開始就做GUI
6.先用mock patch processor跑通，再接ComfyUI API
7.等MVP穩定，再接SAM2、CoTracker、Temporal Stabilization

##與Codex配合的原則
-Codex先做最小可跑版本
-每一輪只做一個窄範圍變更
-先定義schema，再寫config，再寫module，再補測試
-不要一次重構整個專案
-工作流JSON與Python orchestration必須分離
