#开始游戏函数
#注：该函数采用随机选择猎物方式且猎物数为1，如已规划好猎物人员请调用hg:handled_start函数

#初始化标签并随机选择猎物添加标签
tag @a remove prey
tag @a remove hunter
tag @r add prey
tag @a[tag=!prey] add hunter
#初始化队伍并加入队伍
team leave @a
team join prey @a[tag=prey]
team join hunter @a[tag=hunter]
#初始化并显示猎物玩家
title @a title {"text":"猎物是。。。", "color": "yellow", "bold": true}
execute as @a[tag=prey] run spawnpoint @a ~ ~ ~
scoreboard players reset @a DEATH
function hg:wait
title @a subtitle {"type": "selector", "selector": "@a[tag=prey]", "color": "dark_purple"}
clear @a
advancement revoke @a everything
function hg:wait
tellraw @a {"text":"游戏...开始！", "color": "gold"}
scoreboard players set $state GAME_STATE 1