import pyautogui

def ArgParseMouseClickInit(parser):
  """参数解析初始化"""
  import argparse

  if parser is None:
    parser = argparse.ArgumentParser(description='Click mouse')

  parser.add_argument('-n', '--num', type=int, required=True, help='Number of click commands')
  parser.add_argument('-r', '--repeat', type=int, required=True, help='Number of repeat times')
  parser.add_argument('-m', '--move', action='store_true', default=False, help='Move mouse to position before clicking')
  parser.add_argument('-w', '--wait', type=int, default=0, help='Time(seconds) to wait after executing the click commands list once')

  return parser

def ArgCheckMouseClick(args):
  """参数校验"""

  if args.num <= 0:
    raise ValueError('Invalid click command number (-n/--num)')
  if args.repeat <= 0:
    raise ValueError('Invalid repeat times (-r/--repeat)')
  if args.wait < 0:
    raise ValueError('Invalid wait time (-w/--wait)')

def GetClickList(num):
  """获取点击命令列表"""

  print('Select your clock command:')
  print('1: click left')
  print('2: click left double')
  print('3: click right')

  clickOption = {
    1: pyautogui.click,
    2: pyautogui.doubleClick,
    3: pyautogui.rightClick
  }
  clickList = []

  for i in range(num):
    while True:
      try:
        print(f'Input your {i+1} click command (1/2/3):')
        click = int(input())
        if click not in clickOption:
          raise ValueError('Invalid click command! Please input 1, 2, or 3.')
        clickList.append(clickOption[click])
        break
      except ValueError as e:
        print(f'Error: {e}')

  return clickList

def GetPositionList(num):
  """获取点击位置列表"""

  positionList = []
  for i in range(num):
    print(f'Get your {i+1} click position: Press Enter to capture the current mouse position.')
    input()
    x, y = pyautogui.position()
    positionList.append((x, y))
    print(f'Captured position: ({x}, {y})')
  return positionList

def RunClick(clickList, positionList, repeat, wait):
  """运行点击命令"""
  import time

  # 移动到目标位置，防止激活时处于窗口外
  if positionList is not None and len(positionList) > 0:
    pyautogui.moveTo(positionList[0][0], positionList[0][1])

  # 激活目标窗口: 部分窗口失焦后需要一次激活
  pyautogui.click()

  for i in range(repeat):
    for j in range(len(clickList)):
      if positionList is not None:
        pyautogui.moveTo(positionList[j][0], positionList[j][1])
      # print(f'Executing click command: {clickList[j]}')
      clickList[j]() # 执行点击命令
    time.sleep(wait)
    print(f'Run {i+1}/{repeat} times')

def main():
  """主函数"""
  try:
    argParse = ArgParseMouseClickInit(None) # 解析参数
    args = argParse.parse_args()
    ArgCheckMouseClick(args)
    clickList = GetClickList(args.num) # 生成鼠标操作列表
    positionList = GetPositionList(args.num) if args.move else None # 生成鼠标点击的位置列表
    RunClick(clickList, positionList, args.repeat, args.wait) # 开始执行点击命令
  except Exception as e:
    print(f'Error: {e}')

if __name__ == '__main__':
  main()
