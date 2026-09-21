# KeyPress.py — 键盘按键

批量重复按下按键。支持 `-l` 列表、`-n` 交互输入、预设文件三种模式输入按键列表。通用约定（三态热键、运行终止、预设文件）见 [Usage.md](Usage.md)。

> **注意：** 输入按键时需输入按键对应的英文名称（如 `enter`、`shift`、`ctrl`），而不是直接按下键盘按键。常见按键名称参考 [PyAutoGUI 按键文档](https://pyautogui.readthedocs.io/en/latest/keyboard.html#the-hotkey-function)。

## 常用按键名称

| 类型 | 按键名称 |
|------|----------|
| 字母 | `a` `b` `c` ... `z` |
| 数字 | `0` `1` `2` ... `9` |
| 方向键 | `up` `down` `left` `right` |
| 功能键 | `f1` `f2` ... `f12` |
| 编辑键 | `enter` `tab` `space` `backspace` `delete` `escape` `insert` |
| 修饰键 | `shift` `ctrl` `alt` `capslock` |
| 符号 | `` ` `` `-` `=` `[` `]` `\` `;` `'` `,` `.` `/` |

## 用法

```bash
python Scripts/KeyPress.py (-n <命令数> | -l <按键列表> | <预设文件>) -r <重复次数> [-a] [-k1 <开始热键>] [-s <启动延时>] [-d <间隔秒>] [-w <等待秒>] [-k2 <结束键>] [-k3 <暂停键>] [-o <预设文件>]
```

也可经统一入口：`python Main.py keypress <上述参数>`（无参数进菜单后按提示填写）。

## 参数

| 参数 | 说明 |
|------|------|
| `file` | 预设文件，从中加载按键列表和节奏（与 `-n`、`-l` 互斥） |
| `-n`, `--num` | 按键命令数量，交互式逐个输入 |
| `-l`, `--list` | 逗号分隔的按键列表，如 `"up,down,left,right"` |
| `-r`, `--repeat` | 重复执行次数，`0` 表示无限循环（必填） |
| `-a`, `--auto` | 自动执行，跳过开始热键等待直接开始 |
| `-k1`, `--start-key` | 开始热键，按下后才开始（pynput 全局监听，终端失焦也能触发），默认 `enter`；`-a` 时跳过 |
| `-s`, `--start-delay` | 执行前等待时间（秒），默认 0 |
| `-d`, `--delay` | 每条命令之间的等待时间（秒），默认 0.1，未给定时取预设值 |
| `-w`, `--wait` | 每轮结束后的纯轮间间隔（秒），默认 0；不再叠加最后一条命令的 `-d` |
| `-k2`, `--stop-key` | 结束热键（按住即真结束，pynput 全局监听），默认 `esc` |
| `-k3`, `--pause-key` | 暂停/继续热键（按一次暂停、再按一次恢复），默认关闭 |
| `-o`, `--output` | 将当前按键配置保存为预设 JSON 文件，**仅显式指定时保存** |

`-n`、`-l`、`file` 三者互斥，必须指定其中一个。

## 示例

```bash
# 直接指定按键，自动执行，启动前等待 3 秒，重复 5 轮，间隔 0.5 秒
python Scripts/KeyPress.py -l "up,down,left,right" -r 5 -a -s 3 -d 0.5

# 交互式逐个输入 3 个按键，重复 2 轮
python Scripts/KeyPress.py -n 3 -r 2

# 无限循环按下 a,d：按 q 开始，space 暂停/恢复，按 p 真正结束
python Scripts/KeyPress.py -l a,d -r 0 -k1 q -k2 p -k3 space

# 保存预设，之后从预设加载回放
python Scripts/KeyPress.py -l "up,down,left,right" -r 5 -d 0.5 -o keys.json
python Scripts/KeyPress.py keys.json -r 5

# 脚本启动后等待，切到目标窗口按下 f2 才开始
python Scripts/KeyPress.py -l "up,down,left,right" -r 5 -k1 f2
```
