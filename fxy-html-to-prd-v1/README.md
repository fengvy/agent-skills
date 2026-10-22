# fxy-html-to-prd-v1

从已有的产品原型 HTML **反向推导**项目级结构化 PRD（产品需求文档）的 Agent Skill。

一个项目一份 PRD，多端按端增量追加，跨端关系统一写第六章；不另建跨端台账。

## 安装到新设备

技能是仓库里的纯文件。推荐先把仓库 clone 到固定位置，再把技能目录软链到 Agent 的技能目录 —— 另一台设备 `git pull` 后技能立即更新。

```bash
# 1. clone 仓库（注意：仓库根目录不是技能根目录，不要直接 clone 到技能目录）
git clone https://github.com/fengvy/agent-skills.git ~/agent-skills

# 2. 软链技能目录（目录名必须是 fxy-html-to-prd-v1，SKILL.md 位于该目录根部）
# Qoder：
mkdir -p ~/.qoder-cn/skills
ln -s ~/agent-skills/fxy-html-to-prd-v1 ~/.qoder-cn/skills/fxy-html-to-prd-v1
# WorkBuddy：
# mkdir -p ~/.workbuddy/skills
# ln -s ~/agent-skills/fxy-html-to-prd-v1 ~/.workbuddy/skills/fxy-html-to-prd-v1
```

若技能列表不识别软链，改为复制：`mkdir -p ~/.qoder-cn/skills && cp -R ~/agent-skills/fxy-html-to-prd-v1 ~/.qoder-cn/skills/`（WorkBuddy 换成 `~/.workbuddy/skills/`）。

若要作为项目级技能供团队共用，按所用 Agent 的项目技能目录约定放置（WorkBuddy 为 `.workbuddy/skills/`）。

## 目录结构

```
fxy-html-to-prd-v1/
├── SKILL.md                                   技能定义（触发时加载）
├── references/                                按需加载
│   ├── prd-output-template.md                 项目级 PRD 九章骨架
│   └── example-module.md                      PRD 的 A/B 类模块示例
└── scripts/                                   确定性脚本（Python 3 标准库，无第三方依赖）
    ├── extract_prototype_ui.py                静态文本型原型：提取可见文本与交互元素
    ├── dump_prototype_js.py                   JS 渲染型原型：抽取函数体 / mock 数据
    ├── audit_coverage.py                      正向对账：原型有 → 文档没写（查漏写）
    ├── audit_unimplemented.py                 反向对账：文档称「未实现」的声明是否可信
    └── _prd_end_view.py                       按端切片 PRD（被两个对账脚本调用）
```

**两个对账脚本是一对，缺一向不算完成**：

- **正向**（`audit_coverage.py`）：原型里有、文档没写 → 实施方不知道有这功能，可能漏做
- **反向**（`audit_unimplemented.py`）：文档声称「未实现」但判断有误 → 实施方被明确告知不用做，会**主动跳过**一个真实功能

反向错误更严重（消极错误 vs 积极错误）。反向核验须**按维度**分查（赋值 / 调用 / 使用），只数「引用」会把「有引用但从不赋值」误判成"已实现"。

**多端 PRD 必须逐端跑**：两个脚本都支持 `--section <端名>`，第五章只取该端 `#### 5.X <端名>` 分节（含可选的「共用」分节），第三、六、七、九章表格只留该端行。直接拿全项目 PRD 跑，其他端的同名按钮/标识符会造成假覆盖或假一致。端名对不上时脚本报错并列出既有分节。

## 环境要求

- Python 3（仅标准库）
- 无需联网、无需安装依赖

## 用法

技能由 Agent 按 `SKILL.md` 的描述自动触发；给一份或多份原型（本地路径 / 粘贴代码 / 线上 hosted 链接）+ 一句「撰写 PRD」即可。多端项目先建一份项目级 PRD，之后每端读取现有 PRD 增量追加，不重写已覆盖端。

各脚本的详细用法见 `SKILL.md` 的 Scripts 一节，或直接读脚本内 docstring。

## 产出

- `<项目名>-PRD.md` —— 一个项目一份，供人阅读，覆盖全部端并承载跨端契约
