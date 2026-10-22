# agent-skills

自建 Agent Skills 集合。每个技能一个子目录，目录名即技能名（与 `SKILL.md` 的 `name` 一致）。

## 技能清单

| 技能 | 用途 | 产出 |
| --- | --- | --- |
| [`fxy-html-to-prd-v1`](./fxy-html-to-prd-v1/) | 从已有产品原型 HTML **反向推导**项目级结构化 PRD（多端按端增量追加，跨端关系入第六章） | 项目级 PRD |

## 安装到本机

技能是纯文件，从用户级技能目录加载（WorkBuddy 为 `~/.workbuddy/skills/`，Qoder 为 `~/.qoder-cn/skills/`）。**把这个仓库克隆到临时位置，再把需要的技能目录放进技能目录**：

```bash
# 1) 克隆
git clone https://github.com/fengvy/agent-skills.git ~/agent-skills

# 2) 安装某个技能（示例：fxy-html-to-prd-v1）
mkdir -p ~/.workbuddy/skills
cp -R ~/agent-skills/fxy-html-to-prd-v1 ~/.workbuddy/skills/

# 3) 验证：SKILL.md 必须在该目录根部
ls ~/.workbuddy/skills/fxy-html-to-prd-v1/SKILL.md
# Qoder 环境：把上面的 ~/.workbuddy/skills 换成 ~/.qoder-cn/skills
```

> ⚠️ **目录名必须与技能名一致**（`fxy-html-to-prd-v1`），且 `SKILL.md` 位于该目录根部 —— Agent 靠这个结构识别技能。

**更省事的做法（推荐给「本机开发 + 多设备使用」）**：用软链接代替拷贝，这样 `git pull` 后本机技能立即更新，不必反复复制：

```bash
# WorkBuddy：
mkdir -p ~/.workbuddy/skills
ln -s ~/agent-skills/fxy-html-to-prd-v1 ~/.workbuddy/skills/fxy-html-to-prd-v1
# Qoder：
mkdir -p ~/.qoder-cn/skills
ln -s ~/agent-skills/fxy-html-to-prd-v1 ~/.qoder-cn/skills/fxy-html-to-prd-v1
```

## 更新本机已装技能

```bash
cd ~/agent-skills && git pull
# 若用软链接，已自动生效；若用拷贝，需重新 cp -R
```

## 目录约定

```
agent-skills/
├── README.md              ← 本文件（技能索引）
├── .gitignore
└── <skill-name>/
    ├── SKILL.md           ← 必需：YAML frontmatter（name / description）+ 正文
    ├── references/        ← 可选：按需加载的模板与示例
    └── scripts/           ← 可选：确定性脚本
```

## 提交约定

- 每个技能**独立提交**，消息格式 `feat(<skill-name>): 说明` 或 `fix(<skill-name>): 说明`
- 不要把技能运行产生的临时文件提交进来（`.gitignore` 已排除常见类型）
- `SKILL.md` 正文建议控制在 500 行以内（官方最佳实践），超出部分拆到 `references/`
