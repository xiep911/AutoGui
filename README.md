# AutoGui

基于 PyAutoGUI 的 GUI 自动化工具，支持鼠标点击、键盘按键的批量/无限循环执行，以及真实操作的录制回放。统一入口为 `Main.py`，各脚本也保留独立运行能力。

## 快速开始

```bash
pip install -r requirements.txt
```

## 目录结构

- `Main.py` — 统一入口：交互菜单或 CLI 直传，子进程方式调度下面脚本
- `Scripts/` — 三个独立脚本（可单独运行，也可被 Main.py 调度）：
  - `KeyPress.py` — 键盘按键批量/循环执行
  - `MouseClick.py` — 鼠标点击批量/循环执行
  - `Recorder.py` — 录制 / 回放真实鼠标键盘操作
- `Library/Base.py` — 公共代码：pynput 全局热键（开始 / 暂停 / 结束）、按键名归一化与校验、参数预设存取

## 快速示例

```bash
# 统一入口（推荐）：无参数进交互菜单，或带参数直传
python Main.py
python Main.py keypress -l a,d -r 0 -k1 q -k2 p -k3 space

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
