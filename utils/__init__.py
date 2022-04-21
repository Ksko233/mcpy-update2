"""By bailongyue"""
#mcpyModule basedata
import math
import time

class MinecraftError(Exception):
    pass

TICKS_PER_SEC = 60

SAVED = False

ENABLE_NIGHT = True

SECTOR_SIZE = 32
CHUNK_SIZE = 4

TERRAIN = [True, False, False, False, False] # 生物群系
#[0]树林(测试时使用False), [1]雪地, [2]冰河, [3]沙漠, [4]干旱世界(测试阶段)

INFWORLD = True #无限世界

#print(SEED)
GTIME = 0 # 当前世界时间
GDAY = 0.005
GNIGHT = 0.015

WALKING_SPEED = 5 # 走路速度
RUNNING_SPEED = 8 # 跑步速度
FLYING_SPEED = 16 # 飞行速度

GRAVITY = 35.0 # 重力
MAX_JUMP_HEIGHT = 1.25 # 最大跳跃速度
JUMP_SPEED = math.sqrt(2 * GRAVITY * MAX_JUMP_HEIGHT)
TERMINAL_VELOCITY = 35 # 终端速度

PLAYER_HEIGHT = 2 # 玩家高度

TRANSBLOCKS = ("LEAF", "FLOWER", "TALLGRASS", "WATER")

WORLDLEN = 192 # 世界长度

l1 = WORLDLEN/2-1
l2 = -WORLDLEN/2

def log(txt):
    #print("[MCPY client %d]%s" % (int(time.time()), txt))
    pass

CHKLIM = int(WORLDLEN / 2 / CHUNK_SIZE)
