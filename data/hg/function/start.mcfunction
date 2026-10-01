# 开始游戏函数
# 注：该函数采用随机选择猎物方式且猎物数为1，如已规划好猎物人员请调用hg:handled_start函数

function hg:start_steps/phase1
schedule function hg:start_steps/phase2 1s
schedule function hg:start_steps/phase3 3s
