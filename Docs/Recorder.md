# Recorder.py — 录制 / 回放

真实录制鼠标操作和键盘按键，自动采集每步的真实延时，再按录制节奏重放。与 KeyPress/MouseClick 的区别：操作和延时都从实际操作中获取，不需要手动填命令数和统一延时。通用约定（三态热键、运行终止）见 [Usage.md](Usage.md)。

## 录制

```bash
python Scripts/Recorder.py record [-o <输出文件>] [-a] [-k1 <开始热键>] [-s <缓冲秒>] [-k2 <停止键>]
```

| 参数 | 说明 |
|------|------|
| `-o`, `--output` | 录制结果保存的文件，默认 `recording.json` |
| `-a`, `--auto` | 跳过开始热键等待，直接开始录制 |
| `-k1`, `--start-key` | 开始热键，按下后才开始录制（pynput 全局监听），默认 `enter`；`-a` 时跳过 |
| `-s`, `--start-delay` | 开始热键按下后的缓冲秒数，默认 0 |
| `-k2`, `--stop-key` | **停止录制热键**（pyautogui 键名），默认 `esc` |

录制内容以 JSON 保存（每条事件带时间戳，相邻事件时间差即该步真实延时）：

```json
{"t": 0.00, "type": "down",  "button": "left",  "x": 100, "y": 200}
{"t": 0.42, "type": "up",    "button": "left",  "x": 100, "y": 200}
{"t": 1.35, "type": "keydown", "key": "enter"}
{"t": 1.42, "type": "keyup",   "key": "enter"}
```

> 按 `-k2` 指定的键即停止录制，该操作本身不会被记录。

## 回放

```bash
python Scripts/Recorder.py replay <录制文件> -r <重复次数> [-a] [-k1 <开始热键>] [-s <缓冲秒>] [-w <轮间等待>] [-k2 <结束键>] [-k3 <暂停键>] [--speed <倍速>]
```

| 参数 | 说明 |
|------|------|
| `file` | 录制 JSON 文件 |
| `-r`, `--repeat` | 重复次数，`0` 表示无限循环（必填） |
| `-a`, `--auto` | 跳过开始热键等待，直接开始回放 |
| `-k1`, `--start-key` | 开始热键，按下后才开始回放（pynput 全局监听，终端失焦也能触发），默认 `enter`；`-a` 时跳过 |
| `-s`, `--start-delay` | 开始热键按下后的缓冲秒数，默认 0 |
| `-w`, `--wait` | 每轮执行完后的等待时间（秒），默认 0 |
| `-k2`, `--stop-key` | 结束热键（真结束回放，pynput 全局监听），默认 `esc`；等待开始阶段按它 = 放弃本次回放 |
| `-k3`, `--pause-key` | 暂停/继续热键（按一次暂停、再按一次恢复），默认关闭。暂停会**冻结回放调度时钟**，恢复后事件不会"追帧"快进 |
| `--speed` | 回放倍速，如 `2` 表示 2 倍速（`0.5` 表示半速），默认 1.0 |

回放按录制时相邻事件的时间差依次执行，跨轮使用同一个累积目标时刻调度（防漂移），轮间 `-w` 等待也并入该调度，暂停时段同样冻结在调度时钟外。启动时 `pyautogui.PAUSE` 已置 0，重放不被 pyautogui 隐性延时拖慢，事件节拍与录制时间戳精确对齐。

## 示例

```bash
# 录制：切到目标窗口按下 f2 开始，用 esc 停止，保存到 demo.json
python Scripts/Recorder.py record -k1 f2 -k2 esc -o demo.json

# 回放一次
python Scripts/Recorder.py replay demo.json -r 1

# 3 倍速无限循环回放
python Scripts/Recorder.py replay demo.json -r 0 --speed 3

# 循环回放，每轮间隔 2 秒，space 暂停/恢复、p 真正结束
python Scripts/Recorder.py replay demo.json -r 0 -w 2 -k3 space -k2 p
```

## 说明与限制

- 支持左/中/右键的按下与抬起（自动包含双击、按键时长）、滚轮滚动、键盘按键（含按住时长）。
- 纯鼠标移动不记录；按下按键（拖拽）期间只记录起止位置，回放为直线拖拽。
- 需要全局输入钩子，仅 Windows/macOS/Linux 桌面环境适用；依赖 `pynput`。
- 录制坐标为屏幕绝对坐标，窗口移动或缩放后需重新录制。
