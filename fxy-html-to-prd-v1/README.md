# fxy-html-to-prd-v1

从已有的产品原型 HTML **反向推导**结构化 PRD（产品需求文档）与《实现规格》的 Agent Skill。

## 安装到新设备

技能是纯文件，没有云端同步机制，直接 clone 到用户级技能目录即可：

```bash
git clone <本仓库地址> ~/.workbuddy/skills/fxy-html-to-prd-v1
```

**目录名必须是 `fxy-html-to-prd-v1`**，且 `SKILL.md` 位于该目录根部 —— WorkBuddy 靠这个结构识别技能。

若要作为项目级技能供团队共用，改为 clone 到项目的 `.workbuddy/skills/` 下。

## 目录结构

```
fxy-html-to-prd-v1/
├── SKILL.md                                   技能定义（触发时加载）
├── references/                                按需加载
│   ├── prd-output-template.md                 主 PRD 九章骨架
│   ├── example-module.md                      主 PRD 的 A/B 类模块示例
│   ├── implementation-spec-template.md        《实现规格》骨架
│   └── implementation-spec-example.md         《实现规格》填满的样本
└── scripts/                                   确定性脚本（Python 3 标准库，无第三方依赖）
    ├── extract_prototype_ui.py                静态文本型原型：提取可见文本与交互元素
    ├── dump_prototype_js.py                   JS 渲染型原型：抽取函数体 / mock 数据
    ├── audit_coverage.py                      正向对账：原型有 → 文档没写（查漏写）
    └── audit_unimplemented.py                 反向对账：文档称「未实现」的声明是否可信
```

**两个对账脚本是一对，缺一向不算完成**：

- **正向**（`audit_coverage.py`）：原型里有、文档没写 → 实施方不知道有这功能，可能漏做
- **反向**（`audit_unimplemented.py`）：文档声称「未实现」但判断有误 → 实施方被明确告知不用做，会**主动跳过**一个真实功能

反向错误更严重（消极错误 vs 积极错误）。反向核验须**按维度**分查（赋值 / 调用 / 使用），只数「引用」会把「有引用但从不赋值」误判成"已实现"。

## 环境要求

- Python 3（仅标准库）
- 无需联网、无需安装依赖

## 用法

技能由 Agent 按 `SKILL.md` 的描述自动触发；给一份原型（本地路径 / 粘贴代码 / 线上 hosted 链接）+ 一句「撰写 PRD」即可。

各脚本的详细用法见 `SKILL.md` 的 Scripts 一节，或直接读脚本内 docstring。

## 产出

- `<产品名>-PRD.md` —— 供人阅读，用于确认口径
- `<产品名>-实现规格.md` —— 供实施端 AI 阅读，保证实现唯一性
