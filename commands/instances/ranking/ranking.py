"""implements checks for ranking users"""

import os
import json

from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

from commands.command import Command
from utils.constants import alias_to_rank, OSRS_RANKS
from utils.discord_utils import id_or_mention_to_id

class Ranking(Command):
    """implements the commands needed for rankup checks"""

    load_dotenv()
    RANK_REQ_FILE = os.getenv('RANK_REQ_FILE')
    USER_DB_FILE = os.getenv('USER_DB_FILE')

    def __init__(self, cr):
        super().__init__(cr)
        self.add_to_router("setrank", self.set_rank_com)
        self.add_to_router("setrankdate", self.set_rank_date_com)

        #load rank requirements from file
        with open(self.RANK_REQ_FILE) as rankfp:
            self.rank_req = json.load(rankfp)

        #load users to dict
        with open(self.USER_DB_FILE) as rankfp:
            self.users = json.load(rankfp)

    async def set_rank_com(self, ctx, user, rank):
        """sets the rank of a user in the db"""
        user = id_or_mention_to_id(user)
        if not user:
            message = "{} member doesn't exist".format(user)
            await self._send_error_msg(ctx.channel, message)
            return

        if not rank in alias_to_rank:
            message = "{} rank doesn't exist try {}help setrank".format(rank, self.router.prefix)
            await self._send_error_msg(ctx.channel, message)
            return

        rank = alias_to_rank[rank]
        user_obj = self._getuserentry(user)
        user_obj["ranks"][rank] = datetime.now(timezone.utc).timestamp()
        user_obj["current_rank"] = rank
        self.users[str(user)] = user_obj
        member = ctx.guild.get_member(user)
        message = "{} - {}".format(member.mention, alias_to_rank[rank])

        await self._save()
        await ctx.channel.send(message)

    async def set_rank_date_com(self, ctx, user, date, rank=OSRS_RANKS[0]):
        """change the date when someone was ranked"""
        user = id_or_mention_to_id(user)
        if not user:
            message = "{} member doesn't exist".format(user)
            await self._send_error_msg(ctx.channel, message)
            return

        if rank not in alias_to_rank:
            message = "{} rank doesn't exist try {}help setrank".format(rank, self.router.prefix)
            await self._send_error_msg(ctx.channel, message)
            return
        rank = alias_to_rank[rank]

        try:
            joindate = datetime.strptime(date, "%Y/%m/%d")
            timestamp = joindate.timestamp()
        except ValueError:
            message = "the time: {} is formatted incorrectly try {}help setrank"
            message = message.format(date, self.router.prefix)
            await self._send_error_msg(ctx.channel, message)
            return
        except(OverflowError, OSError):
            message = "the time: {} is too far in the past or future"
            message = message.format(date)
            await self._send_error_msg(ctx.channel, message)
            return

        entry = self._getuserentry(user)

        if(rank not in entry["ranks"] and
           not OSRS_RANKS.index(entry["current_rank"]) >= OSRS_RANKS.index(rank)):
            message = "{} rank is lower than the rank you're trying to assign!".format(user)
            await self._send_error_msg(ctx.channel, message)
            return

        entry["ranks"][rank] = timestamp

        await self._save()
        await ctx.channel.send(content="succes!")

    def _getrankinginfo(self, user):
        """returns latest rank, timestamp of latest rank change, timestamp of earliest rank"""
        if self._userexists(user):
            entry = self._getuserentry(str(user))
            ranks_sorted_by_date = sorted(entry["ranks"].items(), key=lambda item: item[1])
            return (ranks_sorted_by_date[-1][0], ranks_sorted_by_date[-1][1],
                    ranks_sorted_by_date[0][0])
        now = datetime.timestamp(datetime.now(timezone.utc))
        return OSRS_RANKS[0], now, now

    # async def _sanitizersn(self, rsn):
    #     #replace all whitespace with _
    #     rsn = re.sub(r"\s", '_', rsn)
    #     #replace any non-ascii characters with _
    #     rsn = re.sub(r'[^\x00-\x7F]+', '_', rsn)
    #     return rsn

    # async def _validatersn(self, rsn):
    #     rsnpattern = "^[A-Za-z0-9 _-]{1,12}"
    #     regex = re.compile(rsnpattern, re.ASCII)
    #     return regex.match(rsn)

    # async def _check_total_lvl(self, rsn, rank):
    #     """This should be changed to be non blocking before it's ever used"""
    #     rsn = self._sanitizersn(rsn)
    #     if not self._validatersn(rsn):
    #         return False, None

    #     url = "https://secure.runescape.com/m=hiscore_oldschool_ironman/index_lite.ws?player={}"
    #     url.format(rsn)
    #     try:
    #         with urllib.request.urlopen(url) as response:
    #             res = response.read()
    #     except urllib.error.URLError as error:
    #         msg = "Couldn't check total level because something is wrong with the osrs highscores."
    #         print(error.reason())
    #         return False, msg

    #     #split by metric
    #     res = res.split(' ')
    #     #split by rank/lvl/xp
    #     res = [metric.split(',') for metric in res] 

    #     # check if somethign was added/removed from the highscores
    #     # which makes the metric below not correct
    #     # example response: 1250,2273,462189436 2984,99,18896015 1784,99,19452485 672,99,40690534 819,99,55183577 477,99,60005227 926,99,13141725 1166,99,26420638 3619,99,13576744 2743,99,13253503 2510,99,13066255 6724,99,13034599 7414,99,14097842 423,99,16561539 1226,99,13067820 3225,98,12260913 366,99,17549564 2064,99,13058338 11073,99,13139726 1381,99,19186991 1933,99,19970319 2457,96,10228839 2701,99,13081092 677,99,13265151 -1,-1 4504,14 -1,-1 1051,1372 133739,1 1973,285 2725,400 1356,422 560,170 434,94 -1,-1 7646,251 3453,928 16176,532 2273,12 -1,-1 1874,1235 695,901 355,56 -1,-1 4721,58 1630,523 2029,50 -1,-1 471,926 397,1107 213,1333 168,119 6150,112 942,1003 440,381 7311,75 1574,368 -1,-1 2818,2467 608,741 5737,180 189,9 400,103 -1,-1 -1,-1 -1,-1 997,64 -1,-1 -1,-1 484,490 3888,537 -1,-1 973,19 -1,-1 -1,-1 1776,481 36838,515 1722,321 1107,2395

    #     metrics = ["overall", "attack", "defence", "strength", "hitpoints", "ranged", "prayer",
    #                "magic", "cooking", "woodcutting", "fletching", "fishing", "firemaking",
    #                "crafting", "smithing", "mining", "herblore", "agility", "thieving", "slayer",
    #                "farming", "runecrafting", "hunter", "construction", "league_points",
    #                "bounty_hunter_hunter", "bounty_hunter_rogue", "clue_scrolls_all",
    #                "clue_scrolls_beginner", "clue_scrolls_easy", "clue_scrolls_medium",
    #                "clue_scrolls_hard", "clue_scrolls_elite", "clue_scrolls_master",
    #                "last_man_standing", "abyssal_sire", "alchemical_hydra", "barrows_chests",
    #                "bryophyta", "callisto", "cerberus", "chambers_of_xeric",
    #                "chambers_of_xeric_challenge_mode", "chaos_elemental", "chaos_fanatic",
    #                "commander_zilyana", "corporeal_beast", "crazy_archaeologist", "dagannoth_prime",
    #                "dagannoth_rex", "dagannoth_supreme", "deranged_archaeologist",
    #                "general_graardor", "giant_mole", "grotesque_guardians", "hespori",
    #                "kalphite_queen", "king_black_dragon", "kraken", "kreearra", "kril_tsutsaroth",
    #                "mimic", "nightmare", "obor", "sarachnis", "scorpia", "skotizo", "the_gauntlet",
    #                "the_corrupted_gauntlet", "theatre_of_blood", "thermonuclear_smoke_devil",
    #                "tzkal_zuk", "tztok_jad", "venenatis", "vetion", "vorkath", "wintertodt",
    #                "zalcano", "zulrah"]

    #     if len(res) != len(metrics):
    #         return

    #     lvl_index = 1
    #     total_lvl = res[metrics.index("overall")][lvl_index]

    #     return total_lvl >= self.rank_req[rank]["total"]

    async def _eligableforrankup(self, user):
        rank, lastranktime, firstranktime = self._getrankinginfo(user)
        index = OSRS_RANKS.index(rank)

        #if unranked you can always get a smiley
        if index == 0:
            return True, OSRS_RANKS[index+1], None

        #if you have the latest rank you can't rank up
        if index + 1 == len(OSRS_RANKS):
            return False, None, None

        #if the rank is manual chosen
        if self.rank_req[OSRS_RANKS[index+1]]["handpicked"]:
            msg = "{} are manually chosen by staff, contact one of them"
            msg.format(OSRS_RANKS[index+1])
            return False, None, msg

        #otherwise check time spend in cc if known
        #firstranktime should always exist if someone has a rank
        time_req = self.rank_req[OSRS_RANKS[index+1]]["time"]

        #refuse rankup because not enough time in cc
        if firstranktime + timedelta(days=7*time_req) > datetime.now(timezone.utc):
            rankuptime = firstranktime + timedelta(days=7*time_req + 1)
            msg = "You haven't been in the cc for long enough. You can rank up at {} "
            msg.format(rankuptime.strftime("%Y-%m-%d"))
            return False, None, msg

        #refuse rankup because to short since last rankup
        if lastranktime + timedelta(days=31) > datetime.now(timezone.utc):
            rankuptime = firstranktime + timedelta(days=32)
            msg = "It hasn't been long enough since your last rankup. You can rank up at {} "
            msg.format(rankuptime.strftime("%Y-%m-%d"))
            return False, None, msg

        return True, OSRS_RANKS[index+1], None

    def _userexists(self, user):
        return str(user) in self.users

    def _getuserentry(self, user):
        if not self._userexists(user):
            entry = {
                "current_rank":OSRS_RANKS[0],
                "ranks":
                {
                }
            }
        else:
            entry = self.users[str(user)]
        return entry

    async def _setrank(self, user, rank):
        timestamp = datetime.timestamp(datetime.now(timezone.utc))
        entry = self._getuserentry(user)
        entry["current_rank"] = rank
        entry["ranks"][rank] = {timestamp:rank}
        self.users[str(user)] = entry
        await self._save()

    async def _save(self):
        await self._save_dict(self.USER_DB_FILE, self.users)
