# 末影龙检测函数
execute if entity @e[type=minecraft:ender_dragon] run scoreboard players set $now DRAGON_STATE 1
execute unless entity @e[type=minecraft:ender_dragon] run scoreboard players set $now DRAGON_STATE 0

execute if score $pre DRAGON_STATE matches 1 if score $now DRAGON_STATE matches 0 run scoreboard players set $state GAME_STATE 3

execute if score $pre DRAGON_STATE matches 0 if score $now DRAGON_STATE matches 0 run summon minecraft:ender_dragon 0 64 0
execute if score $pre DRAGON_STATE matches 0 if score $now DRAGON_STATE matches 0 run scoreboard players set $now DRAGON_STATE 1

scoreboard players operation $pre DRAGON_STATE = $now DRAGON_STATE