/**
 * Site Optimizer Custom Slash Command Integration
 *
 * 這個文件定義了 /site-optimizer 自定義命令，
 * 讓你可以在 Claude Code 中直接使用：
 *
 *   /site-optimizer --site yololab --type image-alt --phase scan
 *
 * 或通過 Skill 工具：
 *
 *   Skill("site-optimizer", "--site yololab --type image-alt --phase scan")
 */

import { spawn } from "child_process";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

/**
 * 執行 Site Optimizer
 * @param {string} args - 命令行參數
 * @returns {Promise<void>}
 */
export async function executeSiteOptimizer(args) {
  const scriptPath = path.join(__dirname, "../scripts/site-optimizer.js");

  return new Promise((resolve, reject) => {
    const proc = spawn("node", [scriptPath, ...args.split(/\s+/).filter(a => a)], {
      stdio: "inherit",
      cwd: path.join(__dirname, "../.."),
    });

    proc.on("close", (code) => {
      if (code === 0) {
        resolve();
      } else {
        reject(new Error(`Site Optimizer exited with code ${code}`));
      }
    });

    proc.on("error", (error) => {
      reject(error);
    });
  });
}

/**
 * 預定義的快捷命令
 */
export const shortcuts = {
  "quick-scan": {
    description: "快速掃描 YOLO LAB 的前 10 篇文章",
    command: "--site yololab --type image-alt --phase scan --sample 10",
  },
  "full-scan": {
    description: "完整掃描 YOLO LAB 全站",
    command: "--site yololab --type image-alt --phase scan",
  },
  "apply-featured": {
    description: "應用到 YOLO LAB 的 featured_media",
    command: "--site yololab --type image-alt --phase apply-featured",
  },
  "apply-inline": {
    description: "應用到 YOLO LAB 的內嵌圖片",
    command: "--site yololab --type image-alt --phase apply-inline",
  },
  "report": {
    description: "查看 YOLO LAB 的優化報告",
    command: "--site yololab --type image-alt --phase report",
  },
  "rollback": {
    description: "回滾所有更新",
    command: "--site yololab --type image-alt --phase rollback --target all",
  },
};

export default { executeSiteOptimizer, shortcuts };
