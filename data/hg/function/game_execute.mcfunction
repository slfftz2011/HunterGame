#游戏检测函数

#如果猎物死亡游戏状态为2
execute as @a[tag=prey] if score @s DEATH matches 1 run scoreboard players set $state GAME_STATE 2
#如果猎物击杀末影龙游戏状态为3
execute if entity @a[tag=prey,advancements={end/kill_dragon=true}] run scoreboard players set $state GAME_STATE 3