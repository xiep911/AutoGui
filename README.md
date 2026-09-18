# AutoGui

基于 PyAutoGUI 的 GUI 自动化工具，支持鼠标点击和键盘按键的批量执行。

## 环境要求

```bash
pip install -r requirements.txt
```

## 鼠标点击 — MouseClick.py

录制鼠标点击位置和操作类型，批量重复执行。

支持两种模式输入点击命令列表。

```bash
python MouseClick.py (-n <命令数> | -c <点击列表>) -r <重复次数> [-m] [-s <启动延时>] [-d <间隔秒>] [-w <等待秒>] [-k <停止键>]
```

| 参数 | 说明 |
|------|------|
| `-n`, `--num` | 点击命令数量，交互式逐个输入 |
| `-c`, `--clicks` | 逗号分隔的点击列表，如 `"1,2,3"`（1=左键，2=双击，3=右键） |
| `-r`, `--repeat` | 重复执行次数，`0` 表示无限循环（必填） |
| `-m`, `--move` | 每次点击前移动到记录的位置 |
| `-s`, `--start-delay` | 开始执行前的等待时间（秒），用于切换窗口，默认 0 |
| `-d`, `--delay` | 每条命令之间的等待时间（秒），默认 0 |
| `-w`, `--wait` | 每轮执行后的等待时间（秒），默认 0 |
| `-k`, `--stop-key` | 停止热键（pynput 全局监听，终端失焦也能停止），默认 `esc` |

`-n` 和 `-c` 互斥，必须指定其中一个。

**示例 1：** 直接指定点击命令，重复 3 轮

```bash
python MouseClick.py -c "1,2,3" -r 3
```

**示例 2：** 指定点击命令并启用位置移动，间隔 0.5 秒

```bash
python MouseClick.py -c "1,1,3" -r 5 -m -d 0.5
```

**示例 3：** 交互式逐个输入 2 个点击命令，重复 3 轮

```bash
python MouseClick.py -n 2 -r 3 -m -d 0.1
```

**示例 4：** 三个位置无限循环点击，每轮间隔 1 秒，按 `esc`（或终端聚焦时 `Ctrl+C`）停止

```bash
python MouseClick.py -c "1,2,3" -r 0 -m -w 1
```

## 键盘按键 — KeyPress.py

支持两种模式输入按键列表，批量重复按下。

> **注意：** 输入按键时需输入按键对应的英文名称（如 `enter`、`shift`、`ctrl`），而不是直接按下键盘按键。常见按键名称参考 [PyAutoGUI 按键文档](https://pyautogui.readthedocs.io/en/latest/keyboard.html#the-hotkey-function)。

### 常用按键名称

| 类型 | 按键名称 |
|------|----------|
| 字母 | `a` `b` `c` ... `z` |
| 数字 | `0` `1` `2` ... `9` |
| 方向键 | `up` `down` `left` `right` |
| 功能键 | `f1` `f2` ... `f12` |
| 编辑键 | `enter` `tab` `space` `backspace` `delete` `escape` `insert` |
| 修饰键 | `shift` `ctrl` `alt` `capslock` |
| 符号 | `` ` `` `-` `=` `[` `]` `\` `;` `'` `,` `.` `/` |

```bash
python KeyPress.py (-n <命令数> | -l <按键列表>) -r <重复次数> [-a] [-s <启动延时>] [-d <间隔秒>] [-w <等待秒>] [-k <停止键>]
```

| 参数 | 说明 |
|------|------|
| `-n`, `--num` | 按键命令数量，交互式逐个输入 |
| `-l`, `--list` | 逗号分隔的按键列表，如 `"up,down,left,right"` |
| `-r`, `--repeat` | 重复执行次数，`0` 表示无限循环（必填） |
| `-a`, `--auto` | 自动执行，跳过 Enter 确认 |
| `-s`, `--start-delay` | 执行前等待时间（秒），默认 0 |
| `-d`, `--delay` | 每条命令之间的等待时间（秒），默认 0 |
| `-w`, `--wait` | 每轮执行后的等待时间（秒），默认 0 |
| `-k`, `--stop-key` | 停止热键（pynput 全局监听，终端失焦也能停止），默认 `esc` |

`-n` 和 `-l` 互斥，必须指定其中一个。

**示例 1：** 直接指定按键，自动执行，启动前等待 3 秒，重复 5 轮，间隔 0.5 秒

```bash
python KeyPress.py -l "up,down,left,right" -r 5 -a -s 3 -d 0.5
```

**示例 2：** 交互式逐个输入 3 个按键，重复 2 轮

```bash
python KeyPress.py -n 3 -r 2
```

### 参数统一约定

三个脚本通用的参数语义一致：

| 参数 | 统一语义 |
|------|----------|
| `-r`, `--repeat` | 重复轮数，`0` 表示无限循环（KeyPress/MouseClick 必填；Recorder `replay` 默认 1） |
| `-s`, `--start-delay` | 开始执行前的等待秒数（Recorder `record` 默认 3，其余默认 0） |
| `-w`, `--wait` | 每轮结束后的等待秒数，默认 0 |
| `-k`, `--stop-key` | 停止热键（pynput 全局监听，终端失焦也能停止），默认 `esc` |
| 命令输入 | MouseClick 用 `-c, --clicks`，KeyPress 用 `-l, --list` 直接给列表；或用 `-n, --num` 逐个交互输入，两种互斥 |

> **无限循环停止：** `-r 0` 时后台监听 `-k` 指定的停止键（默认 `esc`），终端失焦也能生效；终端的 `Ctrl+C` 和鼠标移到屏幕角落（pyautogui 失效保险）仍可作为备用手段。

## 录制回放 — Recorder.py

真实录制鼠标操作和键盘按键，自动采集每步的真实延时，再按录制节奏重放。与上面两个脚本的区别：操作和延时都从用户实际操作中获取，不需要手动填命令数和统一延时。

### 录制

```bash
python Recorder.py record [-o <输出文件>] [-s <启动延时秒>] [-k <停止键>]
```

| 参数 | 说明 |
|------|------|
| `-o`, `--output` | 录制结果保存的文件，默认 `recording.json` |
| `-s`, `--start-delay` | 开始录制前等待时间（秒），默认 3 |
| `-k`, `--stop-key` | **停止录制热键**（pyautogui 键名），默认 `esc` |

录制内容以 JSON 保存（每条事件带时间戳，相邻事件时间差即该步真实延时）：

```json
{"t": 0.00, "type": "down",  "button": "left",  "x": 100, "y": 200}
{"t": 0.42, "type": "up",    "button": "left",  "x": 100, "y": 200}
{"t": 1.35, "type": "keydown", "key": "enter"}
{"t": 1.42, "type": "keyup",   "key": "enter"}
```

**示例：** 延迟 2 秒开始，用 `esc` 停止，保存到 `demo.json`

```bash
python Recorder.py record -s 2 -k esc -o demo.json
```

> 按 `-k` 指定的键即停止录制，该操作本身不会被记录。

### 回放

```bash
python Recorder.py replay <录制文件> [-r <重复次数>] [-s <执行前延时>] [-w <轮间等待>] [--speed <倍速>]
```

| 参数 | 说明 |
|------|------|
| `-r`, `--repeat` | 重复次数，`0` 表示无限循环，默认 1 |
| `-s`, `--start-delay` | 开始回放前的等待时间（秒），用于切入目标窗口，默认 0 |
| `-w`, `--wait` | 每轮执行完后的等待时间（秒），默认 0 |
| `--speed` | 回放倍速，如 `2` 表示 2 倍速（`0.5` 表示半速），默认 1.0 |

回放按录制时相邻事件的时间差依次执行，跨轮使用同一个累积目标时刻调度（防漂移），轮间 `-w` 等待也并入该调度。

**示例 1：** 回放一次

```bash
python Recorder.py replay demo.json
```

**示例 2：** 3 倍速循环回放

```bash
python Recorder.py replay demo.json -r 0 --speed 3
```

**示例 3：** 1 秒后开始，循环回放，每轮之间间隔 2 秒

```bash
python Recorder.py replay demo.json -r 0 -s 1 -w 2
```

### 说明与限制

- 支持左/中/右键的按下与抬起（自动包含双击、按键时长）、滚轮滚动、键盘按键（含按住时长）。
- 纯鼠标移动不记录；按下按键（拖拽）期间只记录起止位置，回放为直线拖拽。
- 需要全局输入钩子，仅 Windows/macOS/Linux 桌面环境适用；依赖 `pynput`。
- 录制坐标为屏幕绝对坐标，窗口移动或缩放后需重新录制。

## 许可

MIT License
