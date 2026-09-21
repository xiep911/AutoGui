# MouseClick.py — 鼠标点击

录制鼠标点击位置和操作类型，批量重复执行。支持 `-l` 列表、`-n` 交互输入、预设文件三种模式。通用约定（三态热键、运行终止、预设文件）见 [Usage.md](Usage.md)。

## 用法

```bash
python Scripts/MouseClick.py (-n <命令数> | -l <点击列表> | <预设文件>) -r <重复次数> [-m] [-a] [-k1 <开始热键>] [-s <启动延时>] [-d <间隔秒>] [-w <等待秒>] [-k2 <结束键>] [-k3 <暂停键>] [-o <预设文件>]
```

也可经统一入口：`python Main.py mouseclick <上述参数>`（无参数进菜单后按提示填写）。

## 参数

| 参数 | 说明 |
|------|------|
| `file` | 预设文件，从中加载点击命令/坐标/节奏（与 `-n`、`-l` 互斥） |
| `-n`, `--num` | 点击命令数量，交互式逐个输入 |
| `-l`, `--list` | 逗号分隔的点击列表，如 `"1,2,3"`（1=左键，2=双击，3=右键） |
| `-r`, `--repeat` | 重复执行次数，`0` 表示无限循环（必填） |
| `-m`, `--move` | 每次点击前移动到记录的位置（坐标在交互输入时采集，预设回放时从预设读取） |
| `-a`, `--auto` | 自动执行，跳过开始热键等待直接开始 |
| `-k1`, `--start-key` | 开始热键，按下后才开始（pynput 全局监听，终端失焦也能触发），默认 `enter`；`-a` 时跳过 |
| `-s`, `--start-delay` | 开始执行前的等待时间（秒），默认 0 |
| `-d`, `--delay` | 每条命令之间的等待时间（秒），默认 0.1，未给定时取预设值 |
| `-w`, `--wait` | 每轮结束后的纯轮间间隔（秒），默认 0；不再叠加最后一条命令的 `-d` |
| `-k2`, `--stop-key` | 结束热键（真结束，pynput 全局监听），默认 `esc` |
| `-k3`, `--pause-key` | 暂停/继续热键（按一次暂停、再按一次恢复），默认关闭 |
| `-o`, `--output` | 将当前点击配置保存为预设 JSON 文件，**仅显式指定时保存** |

`-n`、`-l`、`file` 三者互斥，必须指定其中一个；`file` 与 `-m` 也互斥（坐标由预设提供）。

## 示例

```bash
# 直接指定点击命令，重复 3 轮
python Scripts/MouseClick.py -l "1,2,3" -r 3

# 指定点击命令并启用位置移动，间隔 0.5 秒
python Scripts/MouseClick.py -l "1,1,3" -r 5 -m -d 0.5

# 交互式逐个输入 2 个点击命令，重复 3 轮
python Scripts/MouseClick.py -n 2 -r 3 -m -d 0.1

# 三个位置无限循环点击，每轮间隔 1 秒；按 esc（或 Ctrl+C）停止
python Scripts/MouseClick.py -l "1,2,3" -r 0 -m -w 1

# 保存预设后继续执行，之后从预设回放
python Scripts/MouseClick.py -l "1,2,3" -m -r 3 -o clicks.json
python Scripts/MouseClick.py clicks.json -r 5

# 脚本启动后等待，切到目标窗口按下 f2 才开始
python Scripts/MouseClick.py -l "1,2,3" -r 3 -m -k1 f2
```
