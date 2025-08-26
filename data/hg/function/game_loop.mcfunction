#游戏循环函数

#调用游戏体函数
execute if score $state GAME_STATE matches 1 run function hg:game_once
#调用游戏检测函数
execute if score $state GAME_STATE matches 1 run function hg:game_execute
#判定游戏结果
execute if score $state GAME_STATE matches 2..3 run gamemode spectator @a
execute if score $state GAME_STATE matches 2..3 run title @a title {"text": "游戏结束！", "color": "yellow"}
execute if score $state GAME_STATE matches 2..3 run function hg:wait
execute if score $state GAME_STATE matches 2 run title @a subtitle {"text": "猎人胜！", "color": "dark_red"}
execute if score $state GAME_STATE matches 3 run title @a subtitle {"text": "猎物胜！", "color": "dark_green"}
#结束游戏
execute if score $state GAME_STATE matches 2..3 run scoreboard players set $state GAME_STATE 0