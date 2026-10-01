# 开始游戏函数阶段1
# 初始化标签并随机选择猎物添加标签
tag @a remove prey
tag @a remove hunter
tag @r add prey
tag @a[tag=!prey] add hunter
# 初始化队伍并加入队伍
team leave @a
team join prey @a[tag=prey]
team join hunter @a[tag=hunter]
# 初始化并显示猎物玩家
title @a title {"text":"猎物是。。。", "color": "yellow", "bold": true}
# 仅为猎物设置个人出生点
execute as @a at @s run spawnpoint @s ~ ~ ~
scoreboard players reset @a DEATH
