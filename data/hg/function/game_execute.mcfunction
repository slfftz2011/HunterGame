# 游戏检测函数

# 如果猎物死亡游戏状态为2
execute as @a[tag=prey] if score @s DEATH matches 1 run scoreboard players set $state GAME_STATE 2
# 如果末影龙死亡游戏状态为3
execute if entity @a[dimension=minecraft:the_end] run function hg:check_dragon