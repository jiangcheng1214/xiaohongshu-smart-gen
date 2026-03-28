# 小红书内容生成 - Python 重构版本

纯 Python 实现的小红书内容生成 7 步流水线，替代原有的 shell 脚本实现。

## 目录结构

```
lib_new/
├── __init__.py       # 包初始化
├── session.py        # Session 管理类
├── steps.py          # 所有 7 个步骤的实现
├── pipeline.py       # 流水线协调类
└── validate.py       # 内容验证模块
```

## 快速开始

### 基本用法

```bash
# 从技能目录运行
cd ~/.openclaw/skills/xiaohongshu-smart-gen

# 完整流水线（7步）
python3 xhs_gen.py stock "NVDA stock analysis"

# 只生成内容（步骤 1-3）
python3 xhs_gen.py finance "美联储利率决议" --action content

# 只生成封面（步骤 4-6）
python3 xhs_gen.py tech "AI芯片市场" --action cover

# 查看 session 信息
python3 xhs_gen.py stock "AAPL" --action info
```

### 支持的垂类

- `stock` - 股票分析
- `finance` - 金融资讯
- `tech` - 科技动态
- `beauty` - 美妆护肤

### Actions

| Action | 说明 |
|--------|------|
| `all` | 执行全部 7 个步骤（默认） |
| `content` | 只执行步骤 1-3（搜索、生成、验证） |
| `cover` | 只执行步骤 4-6（封面变量、生成图片、添加 Logo） |
| `info` | 显示 session 信息 |
| `init` | 创建新 session |

## 编程接口

### 直接使用 Pipeline 类

```python
import sys
sys.path.insert(0, 'lib_new')

from pipeline import Pipeline

# 初始化流水线
pipeline = Pipeline()

# 创建或获取 session
session = pipeline.get_or_create_session('stock', 'NVDA analysis')

# 运行完整流水线
pipeline.run_all(session)

# 或分步运行
pipeline.run_content_pipeline(session)  # 步骤 1-3
pipeline.run_cover_pipeline(session)     # 步骤 4-6
pipeline.run_delivery(session)          # 步骤 7
```

### 使用单个步骤

```python
import sys
sys.path.insert(0, 'lib_new')

from session import XhsSession
from steps import Step1Research, Step2Generate, Step3Validate

# 创建 session
session = XhsSession()
session.create('stock', 'NVDA analysis')

# 运行单个步骤
step1 = Step1Research()
step1.run(session)

step2 = Step2Generate()
success, error = step2.run(session)

step3 = Step3Validate()
passed, feedback = step3.run(session)
```

## 与原 Shell 脚本的对比

| 特性 | Shell 版本 | Python 版本 |
|------|-----------|-------------|
| 入口文件 | `scripts/xhs_generate.sh` | `xhs_gen.py` |
| 代码行数 | ~600 行 (shell + 嵌入 python) | ~1200 行 (纯 Python) |
| 错误处理 | 基础 | 完善 |
| 类型提示 | 无 | 有 |
| 可测试性 | 困难 | 容易 |
| 跨平台 | 依赖 bash | 纯 Python |

## 迁移指南

如果你之前使用 shell 脚本：

```bash
# 旧方式 (Shell)
./scripts/xhs_generate.sh stock "NVDA" --all

# 新方式 (Python)
python3 xhs_gen.py stock "NVDA" --action all
# 或简写
python3 xhs_gen.py stock "NVDA"
```

## Session 目录结构

```
xhs_session_<timestamp>_<topic>/
├── session.json          # Session 状态数据
├── research_raw.md       # 搜索结果
├── content.md            # 生成的内容
├── cover_bg.png          # 背景图
├── cover.png             # 带 Logo 的封面
├── debug.log             # 调试日志
└── search_*.json         # 各个搜索的详细结果
```

## 配置文件

垂类配置位于 `verticals/` 目录：

```json
{
  "content_research": {
    "queries": [...]
  },
  "content_structure": {
    "min_length": 300,
    "max_length": 800
  },
  "content_validation": {
    "max_retries": 3,
    "min_score": 5
  },
  "cover_config": {
    "prompt_variables": {...},
    "background_prompt_template": "...",
    "aspect_ratio": "3:4",
    "logo_file": "stock.png"
  }
}
```

## 开发

### 运行测试

```bash
python3 -c "import sys; sys.path.insert(0, 'lib_new'); from steps import Step1Research; print('OK')"
```

### 添加新步骤

1. 在 `steps.py` 中创建新类，继承 `BaseStep`
2. 实现 `run(self, session, **kwargs) -> bool` 方法
3. 在 `Pipeline` 类中添加调用
