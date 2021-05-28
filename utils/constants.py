"""implements constants"""

OSRS_RANK_ALIASSES = [["unranked", "none"],
                      ["iron", "smiley", "smile"],
                      ["recruit", "nana", "nanna", "one stripe", "1 nana", "1 nanna", "1 stripe"],
                      ["peon"],
                      ["corporal", "two stripe", "2 nana", "2 nanna", "2 stripe"],
                      ["sergeant", "three stripe", "3 nana", "3 nanna", "3 stripe"],
                      ["cadet", "shovel"],
                      ["pvmer", "sword", "scimmy"],
                      ["skiller", "pickaxe", "hcim"],
                      ["combat expert", "combatexpert", "inferno", "hcim"],
                      ["maxed", "max"],
                      ["gamer"],
                      ["moderator", "silver", "silver star"],
                      ["administrator", "general", "gold", "gold star"]]

OSRS_RANKS = ["unranked", "iron", "recruit", "peon", "corporal", "sergeant", "cadet",
              "pvmer", "skiller", "combat expert", "maxed", "gamer", "moderator", "administrator"]

COMMON_OSRS_RANK_NAMES = ["unranked", "iron", "1 stripe", "peon", "2 stripes", "3 stripes",
                          "cadet", "pvmer", "skiller", "combat expert", "maxed", "gamer",
                          "moderator", "administrator"]

alias_to_rank = {}
for rankaliases in OSRS_RANK_ALIASSES:
    for alias in rankaliases:
        alias_to_rank[alias] = rankaliases[0]
