# 游戏结束函数
# 用 tellraw 显示胜者
execute if score $state GAME_STATE matches 2 run tellraw @a ["", {"text": "游戏结束！\n", "color": "yellow"}, {"text": "猎人 ", "color": "dark_red"}, {"selector": "@a[tag=hunter]"}, {"text": " 获胜！", "color": "dark_red"}]
execute if score $state GAME_STATE matches 3 run tellraw @a ["", {"text": "游戏结束！\n", "color": "yellow"}, {"text": "猎物 ", "color": "dark_green"}, {"selector": "@a[tag=prey]"}, {"text": " 获胜！", "color": "dark_green"}]

# 最后恢复状态
scoreboard players set $state GAME_STATE 0