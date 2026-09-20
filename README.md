# AutoGui

基于 PyAutoGUI 的 GUI 自动化工具，支持鼠标点击和键盘按键的批量执行。

## 环境要求

```bash
pip install -r requirements.txt
```

## 代码结构

- `Library/Base.py` — 三个脚本共享的基础代码：pynput 全局热键监听（停止 `StopControl` / 开始 `StartControl`）、按键名归一化与校验（`CanonKey`/`ToKeyName`/`ToStopKeyName`/`ValidateStopKey`/`ValidateStartKey`）、参数预设加载/保存（`LoadPreset`/`SavePreset`/`GetPresetNumber`）
- `MouseClick.py` / `KeyPress.py` / `Recorder.py` — 脚本主体，从 `Library.Base` 导入公共部分

## Git 提交签名

本仓库要求提交带验证签名（SSH 签名，无需 GPG）。新工作机配置见 [Docs/SETUP_SSH_SIGNING.md](Docs/SETUP_SSH_SIGNING.md)，可一键脚本完成：

```bash
bash Scripts/SetupGitSigning.sh
```

## 鼠标点击 — MouseClick.py

录制鼠标点击位置和操作类型，批量重复执行。

支持两种模式输入点击命令列表，也支持从预设文件加载。

```bash
python MouseClick.py (-n <命令数> | -l <点击列表> | <预设文件>) -r <重复次数> [-m] [-a] [-k1 <开始热键>] [-s <启动延时>] [-d <间隔秒>] [-w <等待秒>] [-k2 <停止键>] [-o <预设文件>]
```

| 参数 | 说明 |
|------|------|
| `file` | 预设文件，从中加载点击命令/坐标/节奏（与 `-n`、`-l` 互斥） |
| `-n`, `--num` | 点击命令数量，交互式逐个输入 |
| `-l`, `--list` | 逗号分隔的点击列表，如 `"1,2,3"`（1=左键，2=双击，3=右键） |
| `-r`, `--repeat` | 重复执行次数，`0` 表示无限循环（必填） |
| `-m`, `--move` | 每次点击前移动到记录的位置 |
| `-a`, `--auto` | 自动执行，跳过开始热键等待直接开始 |
| `-k1`, `--start-key` | 开始热键，按下该键后才开始执行（pynput 全局监听，终端失焦也能触发），默认 `enter`；指定 `-a` 时跳过 |
| `-s`, `--start-delay` | 开始执行前的等待时间（秒），用于切换窗口，默认 0 |
| `-d`, `--delay` | 每条命令之间的等待时间（秒），默认 0.1，未给定时取预设值 |
| `-w`, `--wait` | 每轮结束后的纯轮间间隔（秒），默认 0，未给定时取预设值；不再叠加最后一条命令的 `-d` |
| `-k2`, `--stop-key` | 停止热键（pynput 全局监听，终端失焦也能停止），默认 `esc` |
| `-o`, `--output` | 将当前点击配置保存为预设 JSON 文件，**仅显式指定时保存** |

`-n`、`-l`、`file` 三者互斥，必须指定其中一个；`file` 与 `-m` 也互斥（坐标由预设提供）。

**示例 1：** 直接指定点击命令，重复 3 轮

```bash
python MouseClick.py -l "1,2,3" -r 3
```

**示例 2：** 指定点击命令并启用位置移动，间隔 0.5 秒

```bash
python MouseClick.py -l "1,1,3" -r 5 -m -d 0.5
```

**示例 3：** 交互式逐个输入 2 个点击命令，重复 3 轮

```bash
python MouseClick.py -n 2 -r 3 -m -d 0.1
```

**示例 4：** 三个位置无限循环点击，每轮间隔 1 秒，按 `esc`（或终端聚焦时 `Ctrl+C`）停止

```bash
python MouseClick.py -l "1,2,3" -r 0 -m -w 1
```

**示例 5（保存预设）：** 指定点击列表并采集坐标，保存为预设后继续执行

```bash
python MouseClick.py -l "1,2,3" -m -r 3 -o clicks.json
```

**示例 6（回放预设）：** 从预设加载命令、坐标和节奏，重复 5 轮

```bash
python MouseClick.py clicks.json -r 5
```

**示例 7（开始热键）：** 脚本启动后等待，切到目标窗口按下 `f2` 才开始自动点击

```bash
python MouseClick.py -l "1,2,3" -r 3 -m -k1 f2
```

## 键盘按键 — KeyPress.py

支持两种模式输入按键列表，也支持从预设文件加载，批量重复按下。

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
python KeyPress.py (-n <命令数> | -l <按键列表> | <预设文件>) -r <重复次数> [-a] [-k1 <开始热键>] [-s <启动延时>] [-d <间隔秒>] [-w <等待秒>] [-k2 <停止键>] [-o <预设文件>]
```

| 参数 | 说明 |
|------|------|
| `file` | 预设文件，从中加载按键列表和节奏（与 `-n`、`-l` 互斥） |
| `-n`, `--num` | 按键命令数量，交互式逐个输入 |
| `-l`, `--list` | 逗号分隔的按键列表，如 `"up,down,left,right"` |
| `-r`, `--repeat` | 重复执行次数，`0` 表示无限循环（必填） |
| `-a`, `--auto` | 自动执行，跳过开始热键等待直接开始 |
| `-k1`, `--start-key` | 开始热键，按下该键后才开始执行（pynput 全局监听，终端失焦也能触发），默认 `enter`；指定 `-a` 时跳过 |
| `-s`, `--start-delay` | 执行前等待时间（秒），默认 0 |
| `-d`, `--delay` | 每条命令之间的等待时间（秒），默认 0.1，未给定时取预设值 |
| `-w`, `--wait` | 每轮结束后的纯轮间间隔（秒），默认 0，未给定时取预设值；不再叠加最后一条命令的 `-d` |
| `-k2`, `--stop-key` | 停止热键（pynput 全局监听，终端失焦也能停止），默认 `esc` |
| `-o`, `--output` | 将当前按键配置保存为预设 JSON 文件，**仅显式指定时保存** |

`-n`、`-l`、`file` 三者互斥，必须指定其中一个。

**示例 1：** 直接指定按键，自动执行，启动前等待 3 秒，重复 5 轮，间隔 0.5 秒

```bash
python KeyPress.py -l "up,down,left,right" -r 5 -a -s 3 -d 0.5
```

**示例 2：** 交互式逐个输入 3 个按键，重复 2 轮

```bash
python KeyPress.py -n 3 -r 2
```

**示例 3（保存预设）：** 指定按键列表和节奏，保存为预设后继续执行

```bash
python KeyPress.py -l "up,down,left,right" -r 5 -d 0.5 -o keys.json
```

**示例 4（回放预设）：** 从预设加载按键和节奏，重复 5 轮

```bash
python KeyPress.py keys.json -r 5
```

**示例 5（开始热键）：** 脚本启动后等待，切到目标窗口并按下 `f2` 才开始执行（默认开始热键是 `enter`，只有想换键时才需指定 `-k1`）

```bash
python KeyPress.py -l "up,down,left,right" -r 5 -k1 f2
```

### 参数统一约定

三个脚本通用的参数语义一致：

| 参数 | 统一语义 |
|------|----------|
| `-r`, `--repeat` | 重复轮数，`0` 表示无限循环（三个脚本均必填） |
| `-s`, `--start-delay` | 开始热键按下后的缓冲秒数，默认 0（`-a` 时即启动后缓冲） |
| `-w`, `--wait` | 每轮结束后的纯轮间间隔（秒），默认 0，不再叠加最后一条命令的 `-d` |
| `-k2`, `--stop-key` | 停止热键（pynput 全局监听，终端失焦也能停止），默认 `esc` |
| `-a`, `--auto` | 跳过开始热键等待，直接执行（三个脚本通用，含 Recorder 的 record/replay） |
| `-k1`, `--start-key` | 开始热键，按下后才开始执行（pynput 全局监听，默认 `enter`，`-a` 时跳过）；三个脚本通用 |
| 命令输入 | 统一用 `-l, --list` 直接给命令列表；或用 `-n, --num` 逐个交互输入；或传预设文件 `file` 加载，三者互斥 |

> **窗口焦点：** 脚本不会自动激活目标窗口。`-k1` 开始热键就是焦点闸门——先切换/点击进入目标窗口，再按开始键才开始执行。指定 `-a` 跳过该等待时，须在启动前把目标窗口置于前台：鼠标点击按绝对坐标路由、不受焦点影响，但键盘按键与 Recorder 回放跟随焦点窗口。

> **无限循环停止：** `-r 0` 时后台监听 `-k2` 指定的停止键（默认 `esc`），终端失焦也能生效；终端的 `Ctrl+C` 和鼠标移到屏幕角落（pyautogui 失效保险）仍可作为备用手段。

> **延时精度：** 各脚本启动时会将 `pyautogui.PAUSE` 置 0，消除 pyautogui 每次调用自带的隐性 0.1 秒；`-d` 通过 pyautogui 的 `interval` 参数注入，指定的延时即真实命令间隔，`-w` 为纯轮间间隔。

### 参数预设（KeyPress/MouseClick 的录制与回放）

KeyPress/MouseClick 支持把"用户输入的配置"保存为 JSON 预设文件，下次直接加载复用。这与 Recorder.py 的真实操作录制不同——这里存的是**参数快照**（命令列表 + 位置 + 节奏），无时间轴：

```json
{
  "version": 1,
  "type": "keypress",                // keypress / mouseclick
  "keys": ["up", "down", "left"],    // keypress: 按键列表
  "clicks": [1, 2, 3],               // mouseclick: 点击命令 1/2/3
  "positions": [[100, 200]],         // mouseclick: -m 采集的坐标，可为空
  "delay": 0.5,
  "wait": 1.0
}
```

规则：

- `-o/--output` **显式指定时才保存**，默认不保存；保存时打印完整文件位置提示。
- 回放用位置参数 `file` 加载预设；`-r` **必须**在命令行指定，预设**不保存**重复次数（重复次数随场合给定）。
- CLI 显式给出的 `-d/-w` **覆盖**预设值；未给出时取预设值，无预设则 `-d` 为 0.1、`-w` 为 0。
- `-s`（启动延时）、`-k1`（开始热键）、`-k2`（停止键）、`-a`（自动启动）属执行环境，不入预设，始终走命令行。

## 录制回放 — Recorder.py

真实录制鼠标操作和键盘按键，自动采集每步的真实延时，再按录制节奏重放。与上面两个脚本的区别：操作和延时都从用户实际操作中获取，不需要手动填命令数和统一延时。

### 录制

```bash
python Recorder.py record [-o <输出文件>] [-a] [-k1 <开始热键>] [-s <缓冲秒>] [-k2 <停止键>]
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

**示例：** 切到目标窗口按下 `f2` 开始录制，用 `esc` 停止，保存到 `demo.json`

```bash
python Recorder.py record -k1 f2 -k2 esc -o demo.json
```

> 按 `-k2` 指定的键即停止录制，该操作本身不会被记录。

### 回放

```bash
python Recorder.py replay <录制文件> -r <重复次数> [-a] [-k1 <开始热键>] [-s <缓冲秒>] [-w <轮间等待>] [-k2 <停止键>] [--speed <倍速>]
```

| 参数 | 说明 |
|------|------|
| `-r`, `--repeat` | 重复次数，`0` 表示无限循环（必填） |
| `-a`, `--auto` | 跳过开始热键等待，直接开始回放 |
| `-k1`, `--start-key` | 开始热键，按下后才开始回放（pynput 全局监听，终端失焦也能触发），默认 `enter`；`-a` 时跳过 |
| `-s`, `--start-delay` | 开始热键按下后的缓冲秒数，默认 0 |
| `-w`, `--wait` | 每轮执行完后的等待时间（秒），默认 0 |
| `-k2`, `--stop-key` | 回放停止热键（pynput 全局监听，终端失焦也能停止），默认 `esc` |
| `--speed` | 回放倍速，如 `2` 表示 2 倍速（`0.5` 表示半速），默认 1.0 |

回放按录制时相邻事件的时间差依次执行，跨轮使用同一个累积目标时刻调度（防漂移），轮间 `-w` 等待也并入该调度。启动时 `pyautogui.PAUSE` 已置 0，重放不再被 pyautogui 隐性延时拖慢，事件节拍与录制时间戳精确对齐。

**示例 1：** 回放一次

```bash
python Recorder.py replay demo.json -r 1
```

**示例 2：** 3 倍速循环回放

```bash
python Recorder.py replay demo.json -r 0 --speed 3
```

**示例 3：** 按开始热键（默认 `enter`，`-a` 可跳过）后缓冲 1 秒，循环回放，每轮之间间隔 2 秒

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
