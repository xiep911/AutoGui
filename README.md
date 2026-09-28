# AutoGui

基于 PyAutoGUI 的 GUI 自动化工具，支持鼠标点击、键盘按键的批量/无限循环执行，以及真实操作的录制回放。统一入口为 `Main.py`，各脚本也保留独立运行能力。

## 快速开始

```bash
pip install -r requirements.txt
```

## 目录结构

- `Main.py` — 统一入口：交互菜单或 CLI 直传，子进程方式调度下面脚本；功能列表与参数引导模板动态发现自各脚本的 `ArgParseInit` argparse 定义（加参数零同步）
- `Scripts/` — 三个独立脚本（可单独运行，也可被 Main.py 调度，仅含 argparse 与组装）：
  - `KeyPress.py` — 键盘按键批量/循环执行
  - `MouseClick.py` — 鼠标点击批量/循环执行
  - `Recorder.py` — 录制 / 回放真实鼠标键盘操作
- `Include/Base.py` — 数据定义层（零依赖）：退出码、版本号、热键/间隔默认值、按键名归一表
- `Library/` — 公共实现层，`__all__` 白名单仅导出脚本直接使用的公开 API，内部实现以 `_` 前缀私有（脚本与 Main 用 `import *` 取用）：
  - `Base.py` — 共享 API：按键名归一（`CanonKey`）、参数预设存取（`LoadPreset` / `SavePreset` / `GetPresetNumber`）
  - `Runner.py` — 执行层：`RunConfig` 参数打包、公共 argparse 与 `GuardMain`、统一循环调度、`RunPress` / `RunClick` / `Record` / `Replay`；全局热键控制、校验、分片睡眠、键转换等内部实现内聚于此（`_` 前缀私有）

## 快速示例

```bash
# 统一入口（推荐）：无参数进交互菜单，或带参数直传
python Main.py
python Main.py keypress -l a,d -r 0 -k1 q -k2 p -k3 space
python Main.py --version  # 打印版本号

# 各脚本独立运行
python Scripts/KeyPress.py -l up,down,left,right -r 5
python Scripts/MouseClick.py -l 1,2,3 -r 0 -m
python Scripts/Recorder.py replay demo.json -r 0 --speed 2
```

## 文档

| 文档 | 内容 |
|------|------|
| [Docs/Usage.md](Docs/Usage.md) | Main.py 用法、三态热键（开始/暂停/结束）、运行终止机制、参数统一约定、预设文件 |
| [Docs/KeyPress.md](Docs/KeyPress.md) | KeyPress 完整参数表与示例 |
| [Docs/MouseClick.md](Docs/MouseClick.md) | MouseClick 完整参数表与示例 |
| [Docs/Recorder.md](Docs/Recorder.md) | Recorder 录制/回放完整参数表与示例 |

## 许可

MIT License
