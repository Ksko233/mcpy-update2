"""by Bailongyue
latest version Alpha 0.4.0
Keep going!"""
import sys
import random
import time
import pickle
from threading import Thread
from multiprocessing import Process

from collections import deque
from pyglet import image
from pyglet.gl import *
from pyglet.graphics import TextureGroup
from pyglet.window import key, mouse

from easygui import exceptionbox


version = 'Alpha 0.4.0'

from utils import *
from utils.sysdata import *

if  not SAVED:
    SEED = random.randrange(10, 1000000)# 世界种子
else:
    SEED = 0


from language import *


selimg = pyglet.resource.image(INV_PATH)
invimg = pyglet.resource.image(FULL_INV_PATH)
continue_button = pyglet.resource.image(CONTINUE_WIDGET_PATH)
loadingIMG = pyglet.resource.image("resources/loading.png")

def cube_vertices(x, y, z, n):
    """返回立方体的顶点, 大小为2n"""
    return [
        x-n,y+n,z-n, x-n,y+n,z+n, x+n,y+n,z+n, x+n,y+n,z-n,  # top
        x-n,y-n,z-n, x+n,y-n,z-n, x+n,y-n,z+n, x-n,y-n,z+n,  # bottom
        x-n,y-n,z-n, x-n,y-n,z+n, x-n,y+n,z+n, x-n,y+n,z-n,  # left
        x+n,y-n,z+n, x+n,y-n,z-n, x+n,y+n,z-n, x+n,y+n,z+n,  # right
        x-n,y-n,z+n, x+n,y-n,z+n, x+n,y+n,z+n, x-n,y+n,z+n,  # front
        x+n,y-n,z-n, x-n,y-n,z-n, x-n,y+n,z-n, x+n,y+n,z-n,  # back
    ]



# 立方体的6个面
FACES = [
    ( 0, 1, 0),
    ( 0,-1, 0),
    (-1, 0, 0),
    ( 1, 0, 0),
    ( 0, 0, 1),
    ( 0, 0,-1),
]

random.seed(SEED)


def normalize(position):
    # 将三维坐标'position'的x、y、z取近似值
    x, y, z = position
    x, y, z = (round(x), round(y), round(z))
    return (x, y, z)


def sectorize(position):
    x, y, z = normalize(position)
    x, y, z = x // SECTOR_SIZE, y // SECTOR_SIZE, z // SECTOR_SIZE
    return (x, 0, z)


persistence = random.uniform(0.01,0.15)
Number_Of_Octaves = random.randint(3,5)

def Noise(x, y):
    n = x + y * 57
    n = (n * 8192) ^ n
    return ( 1.0 - ( (n * (n * n * 15731 + 789221) + 1376312589) & 0x7fffffff) / 1073741824.0)

def SmoothedNoise(x, y):
    corners = ( Noise(x-1, y-1)+Noise(x+1, y-1)+Noise(x-1, y+1)+Noise(x+1, y+1) ) / 16
    sides = ( Noise(x-1, y) +Noise(x+1, y) +Noise(x, y-1) +Noise(x, y+1) ) / 8
    center = Noise(x, y) / 4
    return corners + sides + center

def Cosine_Interpolate(a, b, x):
    ft = x * 3.1415927
    f = (1 - math.cos(ft)) * 0.5
    return a*(1-f) + b*f

def Linear_Interpolate(a, b, x):
    return a*(1-x) + b*x

def InterpolatedNoise(x, y):
    integer_X = int(x)
    fractional_X = x - integer_X
    integer_Y = int(y)
    fractional_Y = y - integer_Y
    v1 = SmoothedNoise(integer_X, integer_Y)
    v2 = SmoothedNoise(integer_X + 1, integer_Y)
    v3 = SmoothedNoise(integer_X, integer_Y + 1)
    v4 = SmoothedNoise(integer_X + 1, integer_Y + 1)
    i1 = Cosine_Interpolate(v1, v2, fractional_X)
    i2 = Cosine_Interpolate(v3, v4, fractional_X)
    return Cosine_Interpolate(i1, i2, fractional_Y)

def PerlinNoise(x, y):
    noise = 0
    p = persistence
    n = Number_Of_Octaves
    for i in range(n):
        frequency = pow(2,i)
        amplitude = pow(p,i)
        noise = noise + InterpolatedNoise(x * frequency, y * frequency) * amplitude
    return noise


def tex_coord(x, y, n=8):
    """返回纹理的边界顶点"""
    m = 1.0 / n
    dx = x * m
    dy = y * m
    return dx, dy, dx + m, dy, dx + m, dy + m, dx, dy + m

def tex_coords(top, bottom, sides):
    """返回顶部、底部和侧面的纹理列表"""
    top = tex_coord(*top)
    bottom = tex_coord(*bottom)
    result = []
    result.extend(top)
    result.extend(bottom)
    if len(sides) == 2:
        side = sides
        side = tex_coord(*side)
        result.extend(side * 4)
    elif len(sides) == 4:
        for side in sides:
            side = tex_coord(*side)
            result.extend(side)
    return result

blocks = []

class Block:
    """方块, 用于物品栏和存档"""
    def __init__(self, name, basename, *tex):
        self.name = name
        try:
            self.img = pyglet.image.load(ICONS_PATH+name+".png")
        except:
            self.img = None
        self.tex = tex_coords(*tex)
        self.basename = basename
        self.collide = True
        self.transparent = (basename in TRANSBLOCKS)
        blocks.append(self)
        self.identifier = blocks.index(self)
        #print(self.basename, self.transparent)

    def get_tex(self):
        return self.tex

    def get_name(self):
        return self.name

    def get_args(self):
        return self.identifier

class EntityBlock:
    """实体"""
    def __init__(self, name, *tex):
        self.name = name
        self.tex = tex_coords(*tex)
        self.default_tex = self.tex

    def get_tex(self):
        return self.tex

    def get_name(self):
        return self.name


class Inventory(list):
    """物品栏, 可以生成图标序列"""
    def __init__(self, iterable=(), selected=0):
        list.__init__(self, iterable)
        if type(selected) != int or selected not in list(range(0,9)):
            raise MinecraftError("Selection index must be int between 0 and 9")
        for block in self: ###检查是否为方块, 防止后续游戏崩溃
            if type(block) not in [Block, tuple, list, Item] and block != None:
                raise MinecraftError("%s is not a block." % str(block))
        self.selected = selected

    def get_names(self):
        names = []
        for block in self:
            try:
                names.append(block.get_name())
            except:
                names.append("empty")
        return names

    def get_icons(self):
        icons = []
        for block in self:
            icons.append(block.img)
        return icons

class Item:
    def __init__(self, clasS, name, tex):
        self.name = name
        self.tex = pyglet.resource.image(tex)
    def get_name(self):
        return self.name

#各种各样的方块
#多种草方块

SNOWGRASS = Block('grass', "SNOWGRASS", (4, 0), (0, 1), (1, 3))
GRASS = Block('grass',"GRASS",(1, 0), (0, 1), (0, 0))
SAND = Block('sand',"SAND", (1, 1), (1, 1), (1, 1))
SNOWSAND = Block('sand',"SNOWSAND", (4, 0), (1, 1), (1, 1))
DIRT = Block('dirt',"DIRT", (0, 1), (0, 1), (0, 1))
STONE = Block('stone',"STONE", (2, 0), (2, 0), (2, 0))
STONEBRICK = Block('stone-brick', 'STONEBRICK', (5, 4), (5, 4), (5, 4))
BEDROCK = Block('bedrock',"BEDROCK",(2, 1), (2, 1), (2, 1))
ICE = Block('ice',"ICE", (3, 1), (3, 1), (3, 1))
WOOD = Block('oak',"WOOD", (0, 2), (0, 2), (3, 0))
LEAF = Block('leaf',"LEAF", (0, 3), (0, 3), (0, 3))
SNOWLEAF = Block('leaf',"SNOWLEAF", (1, 5), (1, 5), (1, 5))
BRICK = Block('brick',"BRICK", (1, 2), (1, 2), (1, 2))
PUMPKIN = Block('pumpkin',"PUMPKIN",(2, 2), (3, 3), [(2, 3), (3, 3), (3, 3), (3, 3)])
MELON = Block('watermelon',"MELON",(2, 4), (2, 4), (1, 4))
CLOUD = Block('cloud',"CLOUD",(5, 1), (5, 1), (5, 1))
TNT = Block('TNT',"TNT",(4, 2), (4, 3), (4, 1))
ORE = Block('diamond-ore',"ORE",(3, 4), (3, 4), (3, 4))
WATER = Block('water',"WATER",(0, 4), (0, 4), (0, 4))
WATER.collide = False
DIAMOND = Block("diamond-block", "DIAMOND", (5, 6), (5, 6), (5, 6))
GOLD = Block("gold-block", "GOLD", (7, 7), (7, 7), (7, 7))
GREEN = Block("emerald-block", "GREEN", (5, 7), (5, 7), (5, 7))

_tex_highlight = tex_coords((5, 1), (5, 1), (5, 1))


#"各种各样"的实体
class ExplodingTNT(EntityBlock):
    def __init__(self, pos, host):
        temptex = random.choice([((4, 2), (4, 3), (4, 1)), ((5, 0), (5, 0), (5, 0))])
        EntityBlock.__init__(self, "exploding-TNT", *temptex)
        self.life = 120
        self.exist = True
        self.pos = list(pos)
        self.host = host

    def update(self):
        self.host.model.hide_entity(self.pos)
        pos = self.pos
        if not ((pos[0], int(pos[1]), pos[2]) in self.host.model.world):
            pos[1] -= 0.1
        self.pos = pos
        self.host.model.show_entity(self)
        self.life -= 1
        #print(self.life) # for debug
        if (self.life // 30) % 2 == 1:
            self.tex = _tex_highlight
        else:
            self.tex = self.default_tex
        if self.life <= 0:
            self.host.TNTboom(pos[0], int(round(pos[1])), pos[2])
            self.host.model.hide_entity(pos)
            try:
                self.host.model.entities.remove(self)
            except:
                pass


class Model(object):
    """游戏存档的模型, 不可直接存储"""
    def __init__(self, process=False):
        self.starting = True
        self._shown = {}
        self._shown_entity = {}
        self.setup_world()
        self.group = TextureGroup(image.load(TEXTURE_PATH).get_texture()) # 纹理列表
        if not process:
            self.dfy = self._initialize(immediate=False)
            self.dfy = 22
        else:
            self.dfy=22

    def setup_world(self):
        self.batch = pyglet.graphics.Batch()
        self.starting = True
        self.world = {} # 地图
        self.entities = [] # 实体
        self.shown = {}
        blocks = tuple(self._shown.items())
        for key, block in blocks:
            self._shown.pop(key)
            block.delete()
        blocks = tuple(self._shown_entity.items())
        for key, block in blocks:
            self._shown_entity.pop(key)
            block.delete()
        del blocks # 删除变量节省内存空间
        self.sectors = {}
        self.queue = deque()
        self.water_blocks = []
        self.existing_chunks = []

    def fix_render(self):
        self.batch = pyglet.graphics.Batch()
        self.shown = {}
        self._shown = {}
        self._shown_entities = {}
        self.process_entire_queue()

    def tree(self, y, x, z, immediate=True):
        """生成树"""
        if TERRAIN[0]:
            th = random.randint(4, 6)
            ts = random.randint(th // 2, 4)
            for i in range(y, y + th):
                self.add_block((x, i, z), WOOD, immediate)
            if TERRAIN[1]:
                temp_block = SNOWLEAF
            else:
                temp_block = LEAF
            if TERRAIN[3]:
                self.add_block((x, i+1, z), temp_block, immediate)
            else:
                for dy in range(y + th, y + th + 2):
                    for dx in range(x - ts, x + ts + 1):
                        for dz in range(z - ts, z + ts + 1):
                            self.add_block((dx, dy, dz), temp_block, immediate)
                for dy in range(y + th + 2, y + th + ts + 2):
                    ts -= 1
                    for dx in range(x - ts, x + ts + 1):
                        for dz in range(z - ts, z + ts + 1):
                            self.add_block((dx, dy, dz), temp_block, immediate)

    def _tree(self, y, x, z):
        """生成树"""
        if TERRAIN[0]:
            th = random.randint(4, 6)
            ts = random.randint(th // 2, 4)
            for i in range(y, y + th):
                self._add_block((x, i, z), WOOD, immediate=False)
            if TERRAIN[3]:
                self._add_block((x, i+1, z), LEAF, immediate=False)
            else:
                for dy in range(y + th, y + th + 2):
                    for dx in range(x - ts, x + ts + 1):
                        for dz in range(z - ts, z + ts + 1):
                            self._add_block((dx, dy, dz), LEAF, immediate=True)
                for dy in range(y + th + 2, y + th + ts + 2):
                    ts -= 1
                    for dx in range(x - ts, x + ts + 1):
                        for dz in range(z - ts, z + ts + 1):
                            self._add_block((dx, dy, dz), LEAF, immediate=True)

    def _initialize(self, scale=WORLDLEN-4, position=(0,0), immediate=True):
        """初始化世界"""
        hl = scale // 2
        mn = 0
        quality = 4
        px, pz=position
        gmap = [[0 for x in range(px, scale+px)]for z in range(pz, scale+pz)]
        for x in range(px, scale+px):
            rx = x-px
            for z in range(pz, scale+pz):
                rz = z-pz
                gmap[rx - hl][rz - hl] += round(PerlinNoise(x / quality, z / quality) * quality)
                mn = min(mn, gmap[rx - hl][rz - hl])
        for x in range(-hl+px, hl+px):
            rx = x-px
            for z in range(-hl+pz, hl+pz):
                rz = z-pz
                gmap[rx][rz] += abs(mn)
                if gmap[rx][rz] < 2:
                    self.add_block((x, 4, z), random.choice([SAND, STONE]), immediate)
                    self.add_block((x, 3, z), random.choice([SAND, STONE]), immediate)
                    self.add_block((x, 2, z), STONE, immediate)
                    self.add_block((x, 1, z), random.choice([STONE]*14+[ORE]), immediate)
                    if not TERRAIN[4]:
                        if TERRAIN[2]:
                            self.add_block((x, 5, z), ICE, immediate)
                            self.add_block((x, 6, z), ICE, immediate)
                        else:
                            self.add_block((x, 5, z), WATER)
                            self.add_block((x, 6, z), WATER)
                    else:
                        if TERRAIN[1]:
                            self.add_block((x, 6, z), SNOWSAND, immediate)
                        else:
                            self.add_block((x, 6, z), SAND, immediate)
                        self.add_block((x, 5, z), SAND, immediate)
                else:
                    for y in range(7, gmap[rx][rz]+5):
                        self.add_block((x, y, z), DIRT, immediate)
                    self.add_block((x, 6, z), random.choice((DIRT, STONE)), immediate)
                    self.add_block((x, 5, z), STONE, immediate)
                    self.add_block((x, 4, z), random.choice([STONE]*16+[ORE]), immediate)
                    self.add_block((x, 3, z), random.choice([STONE]*13+[ORE]), immediate)
                    self.add_block((x, 2, z), random.choice([STONE]*10+[ORE]), immediate)
                    self.add_block((x, 1, z), random.choice([STONE]*7+[ORE]), immediate)
                    if TERRAIN[3]:
                        if TERRAIN[1]:
                            self.add_block((x, gmap[rx][rz]+5, z), SNOWSAND, immediate)
                        else:
                            self.add_block((x, gmap[rx][rz]+5, z), SAND, immediate)
                    else:
                        y = gmap[rx][rz] + 5
                        if self.starting:
                            if y > 7:
                                if (x+1, y, z) in self.world:
                                    if self.world[(x+1, y, z)] in (GRASS, SAND, SNOWSAND):
                                        temp_block = self.world[(x+1, y, z)]
                                elif (x-1, y, z) in self.world:
                                    if self.world[(x-1, y, z)] in (GRASS, SAND, SNOWSAND):
                                        temp_block = self.world[(x-1, y, z)]
                                elif (x, y, z+1) in self.world:
                                    if self.world[(x, y, z+1)] in (GRASS, SAND, SNOWSAND):
                                        temp_block = self.world[(x, y, z+1)]
                                elif (x, y, z-1) in self.world:
                                    if self.world[(x, y, z-1)] in (GRASS, SAND, SNOWSAND):
                                        temp_block = self.world[(x, y, z-1)]
                                elif (x-1, y, z-1) in self.world:
                                    if self.world[(x-1, y, z-1)] in (GRASS, SAND, SNOWSAND):
                                        temp_block = self.world[(x-1, y, z-1)]
                                elif (x-1, y, z+1) in self.world:
                                    if self.world[(x-1, y, z+1)] in (GRASS, SAND, SNOWSAND):
                                        temp_block = self.world[(x-1, y, z+1)]
                                elif (x+1, y, z+1) in self.world:
                                    if self.world[(x+1, y, z+1)] in (GRASS, SAND, SNOWSAND):
                                        temp_block = self.world[(x+1, y, z+1)]
                                elif (x+1, y, z-1) in self.world:
                                    if self.world[(x+1, y, z-1)] in (GRASS, SAND, SNOWSAND):
                                        temp_block = self.world[(x+1, y, z-1)]
                                else:
                                    temp_block = random.choice([GRASS, GRASS, SNOWGRASS, SAND, SAND])
                                self.add_block((x, y, z), temp_block, immediate)
                            elif y > 8:
                                if (x+1, gmap[x][z] + 5, z) in self.world:
                                    if self.world[(x+1, gmap[x][z] + 5, z)] in (GRASS, SAND, SNOWSAND):
                                        temp_block = self.world[(x+1, gmap[x][z] + 5, z)]
                                elif (x-1, gmap[x][z] + 5, z) in self.world:
                                    if self.world[(x-1, gmap[x][z] + 5, z)] in (GRASS, SAND, SNOWSAND):
                                        temp_block = self.world[(x-1, gmap[x][z] + 5, z)]
                                elif (x, gmap[x][z] + 5, z+1) in self.world:
                                    if self.world[(x, gmap[x][z] + 5, z+1)] in (GRASS, SAND, SNOWSAND):
                                        temp_block = self.world[(x, gmap[x][z] + 5, z+1)]
                                elif (x, gmap[x][z] + 5, z-1) in self.world:
                                    if self.world[(x, gmap[x][z] + 5, z-1)] in (GRASS, SAND, SNOWSAND):
                                        temp_block = self.world[(x, gmap[x][z] + 5, z-1)]
                                elif (x-1, gmap[x][z] + 5, z-1) in self.world:
                                    if self.world[(x-1, gmap[x][z] + 5, z-1)] in (GRASS, SAND, SNOWSAND):
                                        temp_block = self.world[(x-1, gmap[x][z] + 5, z-1)]
                                elif (x-1, gmap[x][z] + 5, z+1) in self.world:
                                    if self.world[(x-1, gmap[x][z] + 5, z+1)] in (GRASS, SAND, SNOWSAND):
                                        temp_block = self.world[(x-1, gmap[x][z] + 5, z+1)]
                                elif (x+1, gmap[x][z] + 5, z+1) in self.world:
                                    if self.world[(x+1, gmap[x][z] + 5, z+1)] in (GRASS, SAND, SNOWSAND):
                                        temp_block = self.world[(x+1, gmap[x][z] + 5, z+1)]
                                elif (x+1, gmap[x][z] + 5, z-1) in self.world:
                                    if self.world[(x+1, gmap[x][z] + 5, z-1)] in (GRASS, SAND, SNOWSAND):
                                        temp_block = self.world[(x+1, gmap[x][z] + 5, z-1)]
                                else:
                                    temp_block = random.choice([GRASS, SNOWGRASS, SAND])
                                self.add_block((x, y, z), temp_block, immediate)
                            else:
                                if TERRAIN[1]:
                                    self.add_block((x, y, z), SNOWGRASS, immediate)
                                else:
                                    self.add_block((x, y, z), GRASS, immediate)
                        else:
                            if TERRAIN[1]:
                                self.add_block((x, y, z), SNOWGRASS, immediate)
                            else:
                                self.add_block((x, y, z), GRASS, immediate)

                self.add_block((x, 0, z), BEDROCK, immediate)

        for x in range(-hl+px, hl+px, 4):
            rx = x-px
            for z in range(-hl+pz, hl+pz, 4):
                rz = z-pz
                if x == 0 and z == 0:
                    continue
                if random.randint(0, 5) == 1 and gmap[rx][rz] > 1:
                    self.tree(gmap[rx][rz] + 6, x, z, immediate)
                elif random.randint(0, 4) == 2 and gmap[rx][rz] > 2 and not TERRAIN[1] and not TERRAIN[3]:
                    self.add_block((x, gmap[rx][rz] + 6, z), random.choice([PUMPKIN, MELON]), immediate)
        for x in range(-1, 2):
            for z in range(-1, 2):
                self.add_block((x, 20, z), DIAMOND)
        return 22

    def hit_test(self, position, vector, max_distance=8):
        m = 8
        x, y, z = position
        dx, dy, dz = vector
        previous = None
        for _ in range(max_distance * m):
            key = normalize((x, y, z))
            if key != previous and key in self.world:
                return key, previous
            previous = key
            x, y, z = x + dx / m, y + dy / m, z + dz / m
        return None, None

    def exposed(self, position):
        """检查一个方块有没有被暴露"""
        x, y, z = position
        for dx, dy, dz in FACES:
            if (x + dx, y + dy, z + dz) not in self.world:
                return True
            elif self.world[(x + dx, y + dy, z + dz)].transparent == True:
                return True
        return False

    def add_block(self, position, block=None, immediate=True):
        if type(block) == int:
            block = blocks[block]
        if position in self.world:
            self.remove_block(position, immediate)
        if block != None:
            self._add_block(position, block)
            self.sectors.setdefault(sectorize(position), []).append(position)
            if immediate:
                if self.exposed(position):
                    self.show_block(position)
                self.check_neighbors(position)

    def _add_block(self, position, block=None, immediate=None):
        """在存档中添加一个方块, 但是不渲染"""
        if position in self.world:
            self.remove_block(position, immediate)
        if block != None:
            self.world[position] = block

    def remove_block(self, position, immediate=True):
        self._remove_block(position, immediate)
        try:
            self.sectors[sectorize(position)].remove(position)
        except:
            pass
        if immediate:
            if position in self.shown:
                self.hide_block(position)
            self.check_neighbors(position)

    def _remove_block(self, position, immediate=True):
        try:
            del self.world[position]
        except:
            pass

    def check_neighbors(self, position):
        x, y, z = position
        for dx, dy, dz in FACES:
            key = (x + dx, y + dy, z + dz)
            if key not in self.world:
                continue
            if self.exposed(key):
                if key not in self.shown:
                    self.show_block(key)
            else:
                if key in self.shown:
                    self.hide_block(key)

    def show_block(self, position, immediate=True):
        block = self.world[position]
        self.shown[position] = block
        if immediate:
            self._show_block(position, block)
        else:
            self._enqueue(self._show_block, position, block)

    def _show_block(self, position, block):
        x, y, z = position
        vertex_data = cube_vertices(x, y, z, 0.5)
        texture_data = list(block.tex)
        self._shown[position] = self.batch.add(24, GL_QUADS, self.group,
            ('v3f/static', vertex_data),
            ('t2f/static', texture_data))
        if block.name=='water':
            self.water_blocks.append(position)

    def show_entity(self, entity):
        x, y, z = entity.pos
        if (x, y, z) in self._shown_entity:
            return
        vertex_data = cube_vertices(x, y, z, 0.5)
        texture_data = list(entity.tex)
        self._shown_entity[(x, y, z)] = self.batch.add(24, GL_QUADS, self.group,
            ('v3f/static', vertex_data),
            ('t2f/static', texture_data))
        

    def hide_block(self, position, immediate=True):
        self.shown.pop(position)
        if immediate:
            self._hide_block(position)
        else:
            self._enqueue(self._hide_block, position)

    def _hide_block(self, position):
        try:
            self._shown.pop(position).delete()
        except(KeyError):
            pass

    def hide_entity(self, var):
        try:
            if type(var) == tuple:
                self._shown_entity.pop(var).delete()
            elif type(var) == list:
                var = tuple(var)
                self._shown_entity.pop(var).delete()
        except(KeyError):
            pass

    def show_sector(self, sector):
        for position in self.sectors.get(sector, []):
            if position not in self.shown and self.exposed(position):
                self.show_block(position, False)

    def hide_sector(self, sector):
        for position in self.sectors.get(sector, []):
            if position in self.shown:
                self.hide_block(position, False)

    def change_sectors(self, before, after):
        before_set = set()
        after_set = set()
        pad = 4
        for dx in range(-pad, pad + 1):
            for dy in [0]:
                for dz in range(-pad, pad + 1):
                    if dx ** 2 + dy ** 2 + dz ** 2 > (pad + 1) ** 2:
                        continue
                    if before:
                        x, y, z = before
                        before_set.add((x + dx, y + dy, z + dz))
                    if after:
                        x, y, z = after
                        after_set.add((x + dx, y + dy, z + dz))
        show = after_set - before_set
        hide = before_set - after_set
        for sector in show:
            self.show_sector(sector)
        for sector in hide:
            self.hide_sector(sector)

    def _enqueue(self, func, *args):
        self.queue.append((func, args))

    def _dequeue(self):
        func, args = self.queue.popleft()
        func(*args)

    def process_queue(self):
        start = time.perf_counter()
        while self.queue and time.perf_counter() - start < 1.0 / TICKS_PER_SEC:
            self._dequeue()

    def process_entire_queue(self):
        while self.queue:
            self._dequeue()
        self.starting = False

class ButtonWidget(object):
    """Button widget"""
    def __init__(self, x, y, text="Continue", img=None):
        """Button widget"""
        self.img = img
        self.label = pyglet.text.Label(text, font_name='Arial',
                                       font_size=28, x=x, y=y, anchor_x='center',
                                       anchor_y='center', color=(255, 255, 255, 255))

    def blit(self, *args, **kw):
        self.img.blit(*args, **kw)
        self.label.draw()

class Window(pyglet.window.Window):
    def __init__(self, *args, **kw):
        super(Window, self).__init__(*args, **kw)
        self.exclusive = False
        self.flying = False # 是否在飞行
        self.running = False # 是否在奔跑
        self.jumping = False # 是否在跳
        self.swimming = False ###是否在游泳(Beta版再更新:))
        self.selecting = False # 是否打开背包
        self.show_gui = True
        self.gamepause = True
        self.gamemenu = False
        self.continue_button = ButtonWidget(self.width/2, self.height-160,
                                            text=textContinue,
                                            img=continue_button)
        self.mainmenu_button = ButtonWidget(self.width/2, self.height-200,
                                            text=textMainmenu,
                                            img=continue_button)
        self.model = Model(SAVED)
        if SAVED:
            try:
                self.process_world(TMP_WORLD_PATH)
            except:
                self.model._initialize(immediate=False)
                self.position = (0, 22, 0)
                self.rotation = (0, 0)
        else:   
            self.position = (0, self.model.dfy, 0)
            self.rotation = (0, 0)
        self.strafe = [0, 0]
        self.current_chunk = [0, 0]
        self.sector = None
        self.reticle = None
        self.removing_block = None
        self.update_removing_block = False
        self.dy = 0
        self.inventory = inventory = Inventory([GRASS, DIRT, STONEBRICK,
                                                SAND, WOOD, BRICK,
                                                PUMPKIN, MELON, TNT], 0)
        self.item_names = inventory.get_names()
        self.icons = inventory.get_icons()
        self.block = inventory[inventory.selected]
        self._game_threads = []
        self.num_keys = [
            key._1, key._2, key._3, key._4, key._5,
            key._6, key._7, key._8, key._9, key._0]
        self.label = pyglet.text.Label('', font_name='Arial', font_size=16,
            x=10, y=self.height - 10, anchor_x='left', anchor_y='top',
            color=(255, 255, 255, 255))
        self.clear()
        pyglet.clock.schedule_interval(self.update, 1.0 / TICKS_PER_SEC)

    def set_exclusive_mouse(self, exclusive, dark=False):
        super(Window, self).set_exclusive_mouse(exclusive)
        self.exclusive = exclusive
        self.show_gui = exclusive
        if exclusive:
            GTIME = 0
        else:
            GTIME = 50
        if dark:
            glClearColor((0.5 - GTIME * 0.02)*1.2, (0.69 - GTIME * 0.02)*1.2, (1.0 - GTIME * 0.02)*1.2, 1)
            setup_fog()

    def get_sight_vector(self):
        x, y = self.rotation
        m = math.cos(math.radians(y))
        dy = math.sin(math.radians(y))
        dx = math.cos(math.radians(x - 90)) * m
        dz = math.sin(math.radians(x - 90)) * m
        return (dx, dy, dz)

    def get_motion_vector(self):
        if any(self.strafe):
            x, y = self.rotation
            strafe = math.degrees(math.atan2(*self.strafe))
            y_angle = math.radians(y)
            x_angle = math.radians(x + strafe)
            if self.flying:
                m = math.cos(y_angle)
                dy = math.sin(y_angle)
                if self.strafe[1]:
                    dy = 0.0
                    m = 1
                if self.strafe[0] > 0:
                    dy *= -1
                dx = math.cos(x_angle) * m
                dz = math.sin(x_angle) * m
            else:
                dy = 0.0
                dx = math.cos(x_angle)
                dz = math.sin(x_angle)
        else:
            dy = 0.0
            dx = 0.0
            dz = 0.0
        return (dx, dy, dz)

    def update(self, dt):
        # 刷新
        global GTIME
        global GNIGHT
        global GDAY
        if ENABLE_NIGHT:
            glClearColor((0.5 - GTIME * 0.02)*1.2, (0.69 - GTIME * 0.02)*1.2, (1.0 - GTIME * 0.02)*1.2, 1)
            setup_fog()
            GTIME += GDAY if GTIME < 23 else GNIGHT
            if GTIME > 50:
                GTIME = 50
                GNIGHT = -GNIGHT
                GDAY = -GDAY
            elif GTIME < 0:
                GTIME = 0
                GNIGHT = -GNIGHT
                GDAY = -GDAY
        self.model.process_queue()
        sector = sectorize(self.position)
        if sector != self.sector:
            self.model.change_sectors(self.sector, sector)
            if self.sector is None:
                self.model.process_entire_queue()
            self.sector = sector
        m = 8
        dt = min(dt, 0.2)
        if self.jumping:
            if self.dy == 0:
                self.dy = JUMP_SPEED
        try:
            for eobj in self.model.entities:
                eobj.update()
        except:
            pass
        for _ in range(m):
            self.__update(dt / m)
        if INFWORLD:
            x, y, z = self.position
            cx = int(round(x / CHUNK_SIZE))
            cz = int(round(z / CHUNK_SIZE))
            self.current_chunk = [cx, cz]
            self.setupChunk(cx, cz)
            self.setupChunk(cx+1, cz)
            self.setupChunk(cx-1, cz)
            self.setupChunk(cx, cz+1)
            self.setupChunk(cx, cz-1)
            self.setupChunk(cx+1, cz+1)
            self.setupChunk(cx-1, cz-1)
            self.setupChunk(cx-1, cz+1)
            self.setupChunk(cx+1, cz-1)
        if self.update_removing_block:
            if self.removing_block:
                self.bbp -= 1
                if self.bbp <= 0:
                    self.bbp = 10
                    if self.removing_block in self.model.world:
                        if not self.model.world[self.removing_block].basename == "BEDROCK":
                            if self.model.world[self.removing_block].basename == "TNT":
                                self.explode(*self.removing_block)
                            self.model.remove_block(self.removing_block)
                    vector = self.get_sight_vector()
                    block, previous = self.model.hit_test(self.position, vector)
                    if block:
                        self.removing_block = block
                    else:
                        self.removing_block = None

    def setupChunk(self, cx, cz):
        if abs(cx) < CHKLIM and abs(cz) < CHKLIM:
            return
        if not (cx, cz) in self.model.existing_chunks:
            self.model.existing_chunks.append((cx, cz))
            self.model._initialize(CHUNK_SIZE, (cx*CHUNK_SIZE, cz*CHUNK_SIZE))

    def __update(self, dt):
        self.set_speed(dt)
        d = self.d
        dx, dy, dz = self.get_motion_vector()
        dx, dy, dz = dx * d, dy * d, dz * d
        if not self.flying:
            self.dy -= dt * GRAVITY
            self.dy = max(self.dy, -TERMINAL_VELOCITY)
            dy += self.dy * dt
        x, y, z = self.position
        x, y, z = self.collide((x + dx, y + dy, z + dz), PLAYER_HEIGHT)
        self.position = (x, y, z)
        if (round(x), round(y), round(z)) in self.model.water_blocks:
            if not self.swimming:
                self.swimming = True
        else:
            self.swimming = False

    def set_speed(self, dt):
        speed = FLYING_SPEED if self.flying else RUNNING_SPEED if self.running or self.swimming else WALKING_SPEED
        self.d = dt * speed

    def collide(self, position, height):
        pad = 0.25
        p = list(position)
        np = normalize(position)
        for face in FACES:
            for i in range(3):
                if not face[i]:
                    continue
                d = (p[i] - np[i]) * face[i]
                if d < pad:
                    continue
                for dy in range(height):
                    op = list(np)
                    op[1] -= dy
                    op[i] += face[i]
                    if tuple(op) not in self.model.world:
                        continue
                    elif not self.model.world[tuple(op)].collide:
                        continue
                    p[i] -= (d - pad) * face[i]
                    if face == (0, -1, 0) or face == (0, 1, 0):
                        self.dy = 0
                    break
        return tuple(p)

    def explode(self, x, y, z):
        boom = ExplodingTNT((x, y, z), self)
        self.model.entities.append(boom)
        self.model.show_entity(boom)

    def TNTboom(self, x, y, z, immediate=True):
        # TNT爆炸
        self.model.remove_block((x, y, z))
        bf = 4
        s = 0
        for dy in range(y - bf, y):
            for i in range(x - s, x + s):
                for j in range(z - s, z + s):
                    if (i, dy, j) in self.model.world:
                        if j == z-s or j == z+s-1 or i == x-s or i == x+s-1:
                            if random.randint(0, 1):
                                if self.model.world[(i, dy, j)].name == 'TNT':
                                    self.TNTboom(i, dy, j)
                                elif self.model.world[(i, dy, j)].name != 'bedrock':
                                    self.model.remove_block((i, dy, j), immediate)
                        else:
                            if self.model.world[(i, dy, j)].name == 'TNT':
                                self.TNTboom(i, dy, j)
                            elif self.model.world[(i, dy, j)].name != 'bedrock':
                                self.model.remove_block((i, dy, j), immediate)
            s += 1
        s = bf
        for i in range(x - s, x + s):
            for j in range(z - s, z + s):
                if (i, y, j) in self.model.world:
                    if j == z-s or j == z+s-1 or i == x-s or i == x+s-1:
                        if random.randint(0, 1):
                            if self.model.world[(i, y, j)].name == 'TNT':
                                self.TNTboom(i, y, j)
                            else:
                                self.model.remove_block((i, y, j), immediate)
                    else:
                        if self.model.world[(i, y, j)].name == 'TNT':
                            self.TNTboom(i, y, j)
                        else:
                            self.model.remove_block((i, y, j), immediate)
        for dy in range(y + 1, y + s + 1):
            for i in range(x - s, x + s):
                for j in range(z - s, z + s):
                    if (i, dy, j) in self.model.world:
                        if j == z-s or j == z+s-1 or i == x-s or i == x+s-1:
                            if random.randint(0, 1):
                                if self.model.world[(i, dy, j)].name == 'TNT':
                                    self.TNTboom(i, dy, j)
                                elif self.model.world[(i, dy, j)].name != 'bedrock':
                                    self.model.remove_block((i, dy, j), immediate)
                        else:
                            if self.model.world[(i, dy, j)].name == 'TNT':
                                self.TNTboom(i, dy, j)
                            elif self.model.world[(i, dy, j)].name != 'bedrock':
                                self.model.remove_block((i, dy, j), immediate)
            s -= 1

    def on_mouse_release(self, x, y, button, modifiers):
        self.update_removing_block = False
        self.bbp = 10

    def on_mouse_press(self, x, y, button, modifiers):
        if self.exclusive:
            self.bbp = 2
            vector = self.get_sight_vector()
            block, previous = self.model.hit_test(self.position, vector)
            if (button == mouse.RIGHT) or \
                    ((button == mouse.LEFT) and (modifiers & key.MOD_CTRL)):
                if previous:
                    # 鼠标右击
                    x, y, z = self.position
                    flag = True
                    for i in range(0, PLAYER_HEIGHT):
                        if previous == normalize((x, y - i, z)):
                            flag = False
                            break
                    if flag:
                        self.model.add_block(previous, self.block)
            elif button == pyglet.window.mouse.LEFT and block:
                # 鼠标左击
                dblock = self.model.world[block]
                try:
                    dblock.name
                except:
                    dblock.name = 'None'
                if dblock.name == 'TNT':
                    self.explode(*block)
                if dblock.name != 'bedrock':
                    vector = self.get_sight_vector()
                    block, previous = self.model.hit_test(self.position, vector)
                    if block:
                        self.removing_block = block
                    else:
                        self.removing_block = None
                    self.update_removing_block = True
        else:
            if not self.selecting:
                if self.width/2-200 < x < self.width/2+200 and self.height-180 < y < self.height-140:
                    self.set_exclusive_mouse(True)
                    self.gamepause = False
                    self.gamemenu = False
                    self.mainmenu_button.label.text = textMainmenu
                if self.width/2-200 < x < self.width/2+200 and self.height-220 < y < self.height-180:
                    #self.reset_model()
                    self.gamemenu = not self.gamemenu
                    self.mainmenu_button.label.text = textBack if self.gamemenu else textMainmenu

    def on_mouse_motion(self, x, y, dx, dy):
        if self.exclusive:
            if self.update_removing_block:
                vector = self.get_sight_vector()
                block, previous = self.model.hit_test(self.position, vector)
                if block:
                    self.removing_block = block
                else:
                    self.removing_block = None
            m = 0.15
            x, y = self.rotation
            x, y = x + dx * m, y + dy * m
            y = max(-90, min(90, y))
            self.rotation = (x, y)

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        self.set_selected_block((self.inventory.selected + scroll_y) % 9)

    def on_key_press(self, symbol, modifiers):
        # 键盘按键
        if symbol == key.W:
            self.strafe[0] -= 1
        elif symbol == key.S:
            self.strafe[0] += 1
        elif symbol == key.A:
            self.strafe[1] -= 1
        elif symbol == key.D:
            self.strafe[1] += 1
        elif symbol == key.SPACE:
            self.jumping = True
        elif symbol == key.R:
            self.running = not self.running
        elif symbol == key.TAB:
            self.flying = not self.flying
            self.update_removing_blocks = False
        elif symbol == key.ESCAPE:
            self.update_removing_blocks = False
            if not self.selecting:
                self.set_exclusive_mouse(False)
                if self.gamemenu:
                    self.gamemenu = False
                else:
                    self.gamepause = True
                self.strafe = [0, 0]
        elif symbol in self.num_keys:
            index = (symbol - self.num_keys[0]) % 9
            self.set_selected_block(index)
        elif symbol == key.E:
            self.update_removing_blocks = False
            if not self.gamepause:
                self.selecting = not self.selecting
                self.set_exclusive_mouse(not self.selecting)
        elif symbol == key.Q:
            self.block = None
        elif symbol == key.F1:
            self.show_gui = not self.show_gui

    def set_selected_block(self, index):
        index = int(round(index)) % 9
        self.block = self.inventory[index]
        self.inventory.selected = index

    def on_key_release(self, symbol, modifiers):
        # 键盘松键
        if symbol == key.W:
            self.strafe[0] += 1
        elif symbol == key.S:
            self.strafe[0] -= 1
        elif symbol == key.A:
            self.strafe[1] += 1
        elif symbol == key.D:
            self.strafe[1] -= 1
        elif symbol == key.SPACE:
            self.jumping = False

    def on_resize(self, width, height):
        # label
        self.label.y = height - 10
        self.continue_button.label.y = height - 160
        self.continue_button.label.x = width // 2
        self.mainmenu_button.label.y = height - 200
        self.mainmenu_button.label.x = width // 2
        # reticle
        if self.reticle:
            self.reticle.delete()
        x, y = self.width // 2, self.height // 2
        n = 10
        self.reticle = pyglet.graphics.vertex_list(4,
            ('v2i', (x - n, y, x + n, y, x, y - n, x, y + n))
        )

    def set_2d(self):
        # 3d模式
        width, height = self.get_size()
        glDisable(GL_DEPTH_TEST)
        viewport = self.get_viewport_size()
        glViewport(0, 0, max(1, viewport[0]), max(1, viewport[1]))
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, max(1, width), 0, max(1, height), -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def set_3d(self):
        # 3d模式
        width, height = self.get_size()
        glEnable(GL_DEPTH_TEST)
        viewport = self.get_viewport_size()
        glViewport(0, 0, max(1, viewport[0]), max(1, viewport[1]))
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(65.0, width / float(height), 0.1, 60.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        x, y = self.rotation
        glRotatef(x, 0, 1, 0)
        glRotatef(-y, math.cos(math.radians(x)), 0, math.sin(math.radians(x)))
        x, y, z = self.position
        glTranslatef(-x, -y, -z)

    def on_draw(self):
        # 绘制
        self.clear()
        self.set_3d()
        glColor3d(1, 1, 1)
        self.model.batch.draw()
        self.draw_focused_block()
        self.set_2d()
        self.draw_label()
        self.draw_reticle()
        if self.show_gui:
            self.draw_selection(self.inventory.selected)
        if self.selecting:
            self.draw_full_inv()
        if self.gamepause:
            self.draw_continue_button()
        if self.model.starting:
            loadingIMG.blit(0, 0)

    def draw_focused_block(self):
        vector = self.get_sight_vector()
        block = self.model.hit_test(self.position, vector)[0]
        if block:
            x, y, z = block
            vertex_data = cube_vertices(x, y, z, 0.51)
            glColor3d(0, 0, 0)
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
            pyglet.graphics.draw(24, GL_QUADS, ('v3f/static', vertex_data))
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

    def draw_selection(self, index=0):
        selimg.blit(self.width/2-288+64*index,16)
        for index, item in zip(list(range(0,9)), self.icons):
            if self.block or self.inventory.selected != index:
                try:
                    item.blit(self.width/2-272+index*64, 32)
                except:
                    pass

    def draw_full_inv(self):
        invimg.blit(self.width/2-176, self.height/2-320)

    def draw_label(self):
        x, y, z = self.position
        self.label.text = '%s:(%.2f, %.2f, %.2f)' % (textPos,\
            x, y, z)
        self.label.draw()

    def draw_continue_button(self):
        self.continue_button.blit(self.width/2-200, self.height-180)
        self.mainmenu_button.blit(self.width/2-200, self.height-220)

    def draw_reticle(self):
        glColor3d(255, 255, 255)
        self.reticle.draw(GL_LINES)

    def save(self, file=TMP_WORLD_PATH):
        poss = list(self.model.world)
        saving_blocks={}
        for pos in poss:
            saving_blocks[pos] = self.model.world[pos].get_args()
        if file==None:
            return self.position, saving_blocks, self.rotation
        else:
            f = open(file, 'wb')
            f.seek(0)
            f.truncate()
            pickle.dump((self.position, saving_blocks, self.rotation,\
                         GTIME, TERRAIN, self.model.existing_chunks,\
                         self.current_chunk), f)
            f.close()

    def process_world(self, file=TMP_WORLD_PATH, immediate=False):
        f = open(file, 'rb')
        data = pickle.load(f)
        f.close()
        self.position = data[0]
        self.rotation = data[2]
        GTIME = data[3]
        TERRAIN = data[4]
        self.model.existing_chunks = data[5]
        self.current_chunk = data[6]
        for position in list(data[1]):
            self.model.add_block(position, data[1][position], immediate)

    def execmd(self, command=""):
        commands = command.split(" ")
        if commands[0] == "add_block":
            exec("self.model.add_block(%s, %s)" % (commands[1], commands[2]))
        elif commands[0] == "remove_block":
            exec("self.model.remove_block(%s)" % commands[1])

    def reset_model(self):
        self.model.setup_world()
        if SAVED:
            try:
                self.process_world(TMP_WORLD_PATH, immediate=True)
            except:
                self.model._initialize(immediate=True)
                self.position = (0, 22, 0)
                self.rotation = (0, 0)
        else:
            self.model._initialize(immediate=True)
            self.position = (0, self.model.dfy, 0)
            self.rotation = (0, 0)
        self.model.process_entire_queue()
        self.model.starting = False

def setup_fog():
    # 初始化迷雾和光照
    glEnable(GL_FOG)
    glFogfv(GL_FOG_COLOR, (GLfloat * 4)((0.5 - GTIME * 0.02)*1.2, (0.69 - GTIME * 0.02)*1.2, (1.0 - GTIME * 0.02)*1.2, 1))
    glHint(GL_FOG_HINT, GL_DONT_CARE)
    glFogi(GL_FOG_MODE, GL_LINEAR)
    glFogf(GL_FOG_START, 12.0)
    glFogf(GL_FOG_END, 32.0)
    glLightfv(GL_LIGHT0, GL_POSITION, (GLfloat * 4)(0.0, 0.0, 0.0, 0.0))
    setup_light()



def setup_first_fog():
    # 初始化迷雾和光照
    glEnable(GL_FOG)
    glFogfv(GL_FOG_COLOR, (GLfloat * 4)(0.5 - GTIME * 0.01, 0.69 - GTIME * 0.01, 1.0 - GTIME * 0.01, 1))
    glHint(GL_FOG_HINT, GL_DONT_CARE)
    glFogi(GL_FOG_MODE, GL_LINEAR)
    glFogf(GL_FOG_START, 12.0)
    glFogf(GL_FOG_END, 32.0)
    glLightfv(GL_LIGHT0, GL_POSITION, (GLfloat * 4)(0.0, 0.0, 0.0, 0.0))
    setup_light()

def setup_light():
    # 初始化光照
    gamelight = 5.0 - GTIME / 10
    glLightfv(GL_LIGHT0, GL_AMBIENT, (GLfloat * 4)(gamelight, gamelight, gamelight, 1.0))
    glLightfv(GL_LIGHT0, GL_DIFFUSE, (GLfloat * 4)(gamelight, gamelight, gamelight, 1.0))
    glLightfv(GL_LIGHT0, GL_SPECULAR, (GLfloat * 4)(1.0, 1.0, 1.0, 1.0))
    glEnable(GL_LIGHT0)

def setup():
    # 初始化
    glClearColor(0.5 - GTIME * 0.01, 0.69 - GTIME * 0.01, 1.0 - GTIME * 0.01, 1)
    glEnable(GL_CULL_FACE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    setup_fog()
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)


def main():
    window = Window(width=1024, height=768,
                    caption='Minecraft %s Python Edition' % version,
                    resizable=True)
    window.set_exclusive_mouse(False)
    setup()
    setup_first_fog()
    pyglet.app.run()
    window.save(TMP_WORLD_PATH)
    #exit()

def reset():
    window = Window(width=1024, height=768,
                    caption='Minecraft %s Python Edition' % version,
                    resizable=True)
    window.set_exclusive_mouse(False)
    window.save(TMP_WORLD_PATH)


if __name__ == '__main__':
    try:
        main()
    except:
        exceptionbox()
