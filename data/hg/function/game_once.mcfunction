#游戏体函数

execute as @a[tag=prey,limit=1] at @s run setworldspawn ~ ~ ~
execute as @a[tag=hunter] unless items entity @s container.* minecraft:compass run give @s minecraft:compass
execute as @a as @s run effect give @a[tag=hunter] minecraft:glowing