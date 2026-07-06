# 📐 刷题吧 (QuizBank)

多题型题库管理系统，支持 LaTeX 公式渲染、知识点分类导航、云端数据存储。

## ✨ 功能特性

- **📂 知识点树导航** — 模块 → 章节 → 知识点三级分类，快速筛选题目
- **📋 题目列表** — 支持分页（10/20/30/50 题每页可选）
- **👁 答案切换** — 单题显示/隐藏答案，也可一键全局显示/隐藏
- **📐 LaTeX 公式** — 基于 KaTeX 渲染数学公式
- **🖼 嵌入式图片** — 支持解析卷附图、答案附图
- **🔍 筛选与搜索** — 按难度、题型、来源筛选，支持全文搜索
- **✏️ 题目管理** — 通过弹窗添加/编辑题目，批量导入脚本
- **☁️ 云端存储** — 数据存储在 BaaS 云数据库，多设备同步

## 🛠 技术栈

| 层 | 技术 |
|------|------|
| 前端 | 原生 JavaScript + KaTeX |
| 后端 | BaaS 云数据库 |
| 存储 | 华为云 OBS（图片）、CDN（前端静态资源） |
| 部署 | CDN + 云函数 |

## 🚀 部署

### 线上地址

https://zirfzlhr.kuafuai.net

### 本地开发

```bash
cd public
python3 -m http.server 8765
# 浏览器打开 http://localhost:8765
```

### 部署到 CDN

```bash
# 1. 打包 public 目录
cd public && zip -r ../project.zip .

# 2. 上传到 OBS
python3 <skill>/scripts/upload_file.py project.zip

# 3. 执行部署 API
python3 <skill>/scripts/baas.py --x-api-type deploy --content-file-path <payload.json>
```

## 📁 项目结构

```
quizbank/
├── public/                  # 前端静态资源（部署目录）
│   ├── index.html           # 入口页面
│   ├── app.js               # 应用逻辑
│   ├── style.css            # 样式
│   ├── lib/                 # 第三方库（KaTeX, aipexbase 等）
│   └── images/              # 题目附图
├── data/                    # 导入脚本 & 知识点数据
│   ├── knowledge-tree.json  # 知识点树
│   ├── import_*.py          # PDF 批量导入脚本
│   └── parse_pdf_v3.py      # PDF 解析工具
├── backup/                  # 备份文件
│   ├── CDN-snapshot-*/      # CDN 快照
│   ├── questions_v2_backup_*.json  # 数据库备份
│   └── deployed-*.zip       # 部署包
├── README.md
└── .gitignore
```

## 📊 数据库结构

**表名：** `questions_v2`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 主键 |
| topicId | string | 知识点 ID（逗号分隔支持多知识点） |
| type | string | 题型（选择题/填空题/解答题） |
| difficulty | string | 难度（easy/medium/hard） |
| content | string | 题目内容（含 LaTeX 和 `[figN]` 图片标记） |
| options | string | 选项（仅选择题） |
| answer | string | 答案 |
| solution | string | 解析（含 `[figN]` 图片标记） |
| source | string | 来源（如 2024 新课标Ⅰ卷） |
| tags | string | 标签（含 `number:X` 题号） |
| createdAt | datetime | 创建时间 |

## 📝 图片标记规范

题目和解析中的图片用 `[fig1]`、`[fig2]` 标记定位：
- `[fig1]` — 题干附图
- `[fig2]` — 答案附图

标记前后用 `\n` 换行保证独立成行。图片以 base64 存储在 `q.image` 和 `q.answerImage` 字段。

## 🔒 备份纪律

所有操作必须按以下顺序执行：
1. **备份** — 数据库全量备份 + CDN 快照
2. **本地验证** — 本地环境验证效果
3. **部署** — 用户确认后部署
4. **验证** — 部署后验证 CDN 生效
5. **保存部署包** — 保留本轮部署 zip

## 📄 License

MIT
