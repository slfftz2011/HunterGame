# 游戏循环函数

# 调用游戏体函数
execute if score $state GAME_STATE matches 1 run function hg:game_once
# 调用游戏检测函数
execute if score $state GAME_STATE matches 1 run function hg:game_execute

# 状态跳变时调度 gameover
execute if score $state GAME_STATE matches 2..3 unless score $pre GAME_STATE matches 2..3 run gamemode spectator @a
execute if score $state GAME_STATE matches 2..3 unless score $pre GAME_STATE matches 2..3 run title @a title {"text": "游戏结束！", "color": "yellow"}
execute if score $state GAME_STATE matches 2..3 unless score $pre GAME_STATE matches 2..3 run schedule function hg:gameover 1s
# 记录本刻状态
scoreboard players operation $pre GAME_STATE = $state GAME_STATE