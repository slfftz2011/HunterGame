#初始化函数

#创建游戏状态计分板并初始化
scoreboard objectives add GAME_STATE dummy
scoreboard players set $state GAME_STATE 0
#创建死亡次数计分板
scoreboard objectives add DEATH deathCount {"text":"狗带榜", "color":"aqua"}
scoreboard objectives setdisplay sidebar DEATH
#创建血量计分板
scoreboard objectives add HP health
scoreboard objectives setdisplay list
scoreboard objectives setdisplay below_name
#创建猎人队伍
team add hunter
team modify hunter color red
team modify hunter seeFriendlyInvisibles true
team modify hunter friendlyFire false
team modify hunter prefix {"text": "[猎人]", "color": "yellow", "bold": true}
#创建猎物队伍
team add prey
team modify prey seeFriendlyInvisibles true
team modify prey friendlyFire false
team modify prey prefix {"text": "[猎物]", "color": "yellow", "bold": true}
team modify prey color green
#说明
loot give @a loot hg:welcome