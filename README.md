# AutoGui

基于 PyAutoGUI 的 GUI 自动化工具，支持鼠标点击和键盘按键的批量执行。

## 环境要求

```bash
pip install -r requirements.txt
```

## 鼠标点击 — MouseClick.py

录制鼠标点击位置和操作类型，批量重复执行。

```bash
python MouseClick.py -n <命令数> -r <重复次数> [-m] [-d <间隔秒>] [-w <等待秒>]
```

| 参数 | 说明 |
|------|------|
| `-n`, `--num` | 点击命令数量（必填） |
| `-r`, `--repeat` | 重复执行次数（必填） |
| `-m`, `--move` | 每次点击前移动到记录的位置 |
| `-d`, `--delay` | 每条命令之间的等待时间（秒），默认 0 |
| `-w`, `--wait` | 每轮执行后的等待时间（秒），默认 0 |

**示例：** 录制 2 个点击位置，重复 3 轮，启用位置移动，间隔 0.1 秒

```bash
python MouseClick.py -n 2 -r 3 -m -d 0.1
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
python KeyPress.py (-n <命令数> | -k <按键列表>) -r <重复次数> [-a] [-s <启动延时>] [-d <间隔秒>] [-w <等待秒>]
```

| 参数 | 说明 |
|------|------|
| `-n`, `--num` | 按键命令数量，交互式逐个输入 |
| `-k`, `--keys` | 逗号分隔的按键列表，如 `"up,down,left,right"` |
| `-r`, `--repeat` | 重复执行次数（必填） |
| `-a`, `--auto` | 自动执行，跳过 Enter 确认 |
| `-s`, `--start-delay` | 执行前等待时间（秒），默认 0 |
| `-d`, `--delay` | 每条命令之间的等待时间（秒），默认 0 |
| `-w`, `--wait` | 每轮执行后的等待时间（秒），默认 0 |

`-n` 和 `-k` 互斥，必须指定其中一个。

**示例 1：** 直接指定按键，自动执行，启动前等待 3 秒，重复 5 轮，间隔 0.5 秒

```bash
python KeyPress.py -k "up,down,left,right" -r 5 -a -s 3 -d 0.5
```

**示例 2：** 交互式逐个输入 3 个按键，重复 2 轮

```bash
python KeyPress.py -n 3 -r 2
```

## 许可

MIT License
