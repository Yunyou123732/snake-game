# 贪吃蛇小游戏

一个使用 Python 和 pygame 编写的桌面贪吃蛇小游戏。项目内已经创建了
`.venv` 虚拟环境，并已安装和验证 `pygame 2.6.1`。

## 环境要求

- Windows
- Python 3.8 或更高版本（当前虚拟环境使用 Python 3.8.9）
- pygame 2.6.1（已安装在项目内的 `.venv` 中）

## 运行游戏

在 PowerShell 中执行：

```powershell
cd D:\snake-game
.\.venv\Scripts\python.exe main.py
```

也可以先激活虚拟环境再运行：

```powershell
cd D:\snake-game
.\.venv\Scripts\Activate.ps1
python main.py
```

如果 PowerShell 不允许执行激活脚本，直接使用第一种命令即可。

## 在 PyCharm 中打开和运行

1. 在 PyCharm 中选择 **Open**，打开 `D:\snake-game` 目录。
2. 如果解释器未自动选中，打开 **Settings > Project: snake-game > Python
   Interpreter**，选择 **Add Interpreter > Add Local Interpreter > Existing**。
3. 将解释器路径设为 `D:\snake-game\.venv\Scripts\python.exe`。
4. 打开 `main.py`，点击运行按钮，或在代码编辑区右键选择 **Run
   'main'**。

## 操作方式

- 方向键或 `W`、`A`、`S`、`D`：控制蛇向上、左、下、右移动。
- 场内会持续补充两颗红色果实；每吃到一个加 10 分，蛇身变长，移动速度逐渐加快。
- 按 `Space`：暂停或继续游戏，暂停时棋盘上会显示醒目的提示。
- 撞到墙壁：游戏结束；穿过自己的身体不会结束游戏。
- 游戏结束后：界面会显示最终分数，按 `Enter`、`Space` 或 `R` 重新开始。
- 按 `Esc`：退出游戏。

## 重新安装依赖

如果需要在其他电脑或新的虚拟环境中安装依赖：

```powershell
cd D:\snake-game
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

安装后可验证 pygame：

```powershell
.\.venv\Scripts\python.exe -c "import pygame; print(pygame.version.ver)"
```
