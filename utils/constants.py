"""implements constants"""

OSRS_RANK_ALIASSES = [["unranked", "none"],
                      ["smiley", "smiley", "smile"],
                      ["recruit", "nana", "nanna", "one stripe", "1 nana", "1 nanna", "1 stripe"],
                      ["corporal", "two stripe", "2 nana", "2 nanna", "2 stripe"],
                      ["sergeant", "three stripe", "3 nana", "3 nanna", "3 stripe"],
                      ["lieutenant", "bronze", "bonze star"],
                      ["captain", "silver", "silver star"],
                      ["general", "gold", "gold star"]]

OSRS_RANKS = ["unranked", "smiley", "recruit", "corporal", "sergeant",
              "lieutenant", "captain", "general"]

alias_to_rank = {}
for rankaliases in OSRS_RANK_ALIASSES:
    for alias in rankaliases:
        alias_to_rank[alias] = rankaliases[0]
