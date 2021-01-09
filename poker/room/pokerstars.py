import re
from decimal import Decimal
from datetime import datetime
import attr
import pytz
from pathlib import Path
from zope.interface import implementer
from .. import handhistory as hh
from ..card import Card
from ..hand import Combo
from ..constants import Limit, Game, GameType, Currency, Action, MoneyType

__all__ = ["PokerStarsHandHistory", "Notes"]


@implementer(hh.IStreet)
class _Street(hh._BaseStreet):

    _blind_re = re.compile(
            r"""^(?P<name>.+?): posts (?P<blind>\w+\s\w+) [\D]?(?P<amount>(\d+(?:\.\d+)?))""")

    _raise_re = re.compile(
        r"""^(?P<name>.+?): raises \D?(?P<raise>(\d+(?:\.\d+)?)) to \D?(?P<amount>(\d+(?:\.\d+)?))""")

    _cash_out_re = re.compile(
        r"^(?P<name>.+?) (?P<action>cashed out) the hand for [\D](?P<amount>(\d+(?:\.\d+)?))")

    _collected_re = re.compile(
        r"""^(?P<name>.+?) collected \D?(?P<amount>(\d+(?:\.\d+)?))"""
    )

    def _parse_cards(self, boardline):
        if len(boardline) == 10:
            self.cards = (Card(boardline[1:3]), Card(boardline[4:6]), Card(boardline[7:9]))
        if len(boardline) == 15:
            self.cards = (Card(boardline[1:3]), Card(boardline[4:6]), Card(boardline[7:9]), Card(boardline[12:14]))
        if len(boardline) == 18:
            self.cards = (Card(boardline[1:3]), Card(boardline[4:6]), Card(boardline[7:9]),
                          Card(boardline[10:12]), Card(boardline[15:17]))

    def _parse_actions(self, actionlines):
        actions = []
        for line in actionlines:
            if line.startswith("Uncalled bet"):
                action = self._parse_uncalled(line)
            elif "collected" in line:
                action = self._parse_collected(line)
            elif "doesn't show hand" in line:
                action = self._parse_muck(line)
            elif ' said, "' in line:  # skip chat lines
                continue
            elif "posts" in line:
                action = self._parse_blind(line)
            elif "raises" in line:
                action = self._parse_raise(line)
            elif "leaves" in line:
                continue
            elif "connected" in line: # also includes disconnected
                continue
            elif "cashed out" in line:
                action = self._parse_cashed_out(line)
            elif "removed from the table" in line:
                continue
            elif "shows" in line:
                # shows is ignored at the moment
                continue
            elif "mucks" in line:
                # muck is ignored at the moment
                continue
            elif "finished" in line:
                # muck is ignored at the moment
                continue
            elif ":" in line:
                action = self._parse_player_action(line)
            else:
                raise RuntimeError("bad action line: " + line)

            actions.append(hh._PlayerAction(*action))
        self.actions = tuple(actions) if actions else None

    # TODO: all currency symobols should be removed
    def _parse_uncalled(self, line):
        first_paren_index = line.find("(")
        second_paren_index = line.find(")")
        amount = line[first_paren_index + 1: second_paren_index]
        amount = str.replace(amount, "$", "")
        name_start_index = line.find("to ") + 3
        name = line[name_start_index:]
        return name, Action.RETURN, Decimal(amount)

    def _parse_muck(self, line):
        colon_index = line.find(":")
        name = line[:colon_index]
        return name, Action.MUCK, None

    def _parse_player_action(self, line):
        name, _, action = line.partition(": ")
        action, _, amount = action.partition(" ")
        amount, _, _ = amount.partition(" ")

        if amount:
            amount = str.replace(amount, "$", "")
            return name, Action(action), Decimal(amount)
        else:
            return name, Action(action), None

    def _parse_collected(self, line):
        match = self._collected_re.match(line)
        return match.group("name"), Action.WIN, Decimal(match.group("amount"))

    def _parse_raise(self, line):
        match = self._raise_re.match(line)
        return match.group("name"), Action.RAISE, Decimal(match.group("amount"))

    def _parse_blind(self, line):
        match = self._blind_re.match(line)
        return match.group("name"), Action(match.group("blind")), Decimal(match.group("amount"))

    def _parse_cashed_out(self, line):
        match = self._cash_out_re.match(line)
        return match.group("name"), Action(match.group("action")), Decimal(match.group("amount"))


@implementer(hh.IHandHistory)
class PokerStarsHandHistory(hh._SplittableHandHistoryMixin, hh._BaseHandHistory):
    """Parses PokerStars Tournament hands."""

    _DATE_FORMAT = "%Y/%m/%d %H:%M:%S ET"
    _TZ = pytz.timezone("US/Eastern")  # ET
    _split_re = re.compile(r" ?\*\*\* ?\n?|\n")
    _header_re = re.compile(
        r"""
                        ^PokerStars\s+                                # Poker Room
                        Hand\s+\#(?P<ident>\d+):\s+                   # Hand history id
                        (Tournament\s+\#(?P<tournament_ident>\d+),\s+ # Tournament Number
                         ((?P<freeroll>Freeroll)|(                    # buyin is Freeroll
                          \$?(?P<buyin>\d+(\.\d+)?)                   # or buyin
                          (\+\$?(?P<rake>\d+(\.\d+)?))?               # and rake
                          (\s+(?P<currency>[A-Z]+))?                  # and currency
                         ))\s+
                        )?
                        (?P<game>.+?)\s+                              # game
                        (?P<limit>(?:Pot\s+|No\s+|)Limit)\s+          # limit
                        (-\s+Level\s+(?P<tournament_level>\S+)\s+)?   # Level (optional)
                        \(
                         (((?P<sb>\d+)/(?P<bb>\d+))|(                 # tournament blinds
                          \$(?P<cash_sb>\d+(\.\d+)?)/                 # cash small blind
                          \$(?P<cash_bb>\d+(\.\d+)?)                  # cash big blind
                          (\s+(?P<cash_currency>\S+))?                # cash currency
                         ))
                        \)\s+
                        -\s+                                          # no localized dateanymore
                        (?P<date>.+)                                  # ET date
                        """,
        re.VERBOSE,
    )
    _table_re = re.compile(
        r"^Table '(.*)' (\d+)-max Seat #(?P<button>\d+) is the button"
    )
    _seat_re = re.compile(
            r"^Seat (?P<seat>\d+): (?P<name>.+?) \(\$?(?P<stack>\d+(\.\d+)?) in chips\)"
    )  # noqa
    _hero_re = re.compile(r"^Dealt to (?P<hero_name>.+?) \[(..) (..)\]")
    _pot_re = re.compile(r"^Total pot \$?(\d+(?:\.\d+)?) .*\| Rake \$?(\d+(?:\.\d+)?)")
    _winner_re = re.compile(r"^Seat (\d+): (.+?) collected \(\$?(\d+(?:\.\d+)?)\)")
    _showdown_re = re.compile(r"^Seat (\d+): (.+?) showed \[(.+?)\] and won")
    _ante_re = re.compile(r".*posts the ante (\d+(?:\.\d+)?)")
    _board_re = re.compile(r"(?<=[\[ ])(..)(?=[\] ])")


    def parse_header(self):
        # sections[0] is before HOLE CARDS
        # sections[-1] is before SUMMARY
        self._split_raw()

        match = self._header_re.match(self._splitted[0])

        self.extra = dict()
        self.ident = match.group("ident")

        # We cannot use the knowledege of the game type to pick between the blind
        # and cash blind captures because a cash game play money blind looks exactly
        # like a tournament blind

        self.sb = Decimal(match.group("sb") or match.group("cash_sb"))
        self.bb = Decimal(match.group("bb") or match.group("cash_bb"))

        if match.group("tournament_ident"):
            self.game_type = GameType.TOUR
            self.tournament_ident = match.group("tournament_ident")
            self.tournament_level = match.group("tournament_level")

            currency = match.group("currency")
            self.buyin = Decimal(match.group("buyin") or 0)
            self.rake = Decimal(match.group("rake") or 0)
        else:
            self.game_type = GameType.CASH
            self.tournament_ident = None
            self.tournament_level = None
            currency = match.group("cash_currency")
            self.buyin = None
            self.rake = None

        if match.group("freeroll") and not currency:
            currency = "USD"

        if not currency:
            self.extra["money_type"] = MoneyType.PLAY
            self.currency = None
        else:
            self.extra["money_type"] = MoneyType.REAL
            self.currency = Currency(currency)

        self.game = Game(match.group("game"))
        self.limit = Limit(match.group("limit"))

        self._parse_date(match.group("date"))

        self.header_parsed = True

    def parse(self):
        """Parses the body of the hand history, but first parse header if not yet parsed."""
        if not self.header_parsed:
            self.parse_header()

        self._parse_table()
        self._parse_players()
        self._parse_button()
        self._parse_hero()
        self._parse_preflop()
        self._parse_street("FLOP")
        self._parse_street("TURN")
        self._parse_street("RIVER")
        self._parse_showdown()
        self._parse_pot()
        self._parse_board()
        self._parse_winners()
        self._calculate_earnings()

        self._del_split_vars()
        self.parsed = True

    def _calculate_earnings(self):
        earnings = Decimal(0)
        all_actions = []
        if self.preflop is not None and self.preflop.actions is not None:
            all_actions.extend(list(filter(lambda action : action.name == self.hero.name, self.preflop.actions)))
        if self.flop is not None and self.flop.actions is not None:
            all_actions.extend(list(filter(lambda action : action.name == self.hero.name, self.flop.actions)))
        if self.turn is not None and self.turn.actions is not None:
            all_actions.extend(list(filter(lambda action: action.name == self.hero.name, self.turn.actions)))
        if self.river is not None and self.river.actions is not None:
            all_actions.extend(list(filter(lambda action : action.name == self.hero.name, self.river.actions)))
        if self.show_down is not None and self.show_down.actions is not None:
            all_actions.extend(list(filter(lambda action : action.name == self.hero.name, self.show_down.actions)))

        for action in all_actions:
            if action.action in [Action.BET, Action.RAISE, Action.CALL, Action.SB, Action.BB]:
                earnings -= action.amount
            elif action.action in [Action.WIN, Action.CASH_OUT, Action.RETURN]:
                earnings += action.amount
        self.earnings = earnings


    def _parse_table(self):
        self._table_match = self._table_re.match(self._splitted[1])
        self.table_name = self._table_match.group(1)
        self.max_players = int(self._table_match.group(2))

    def _parse_players(self):
        self.players = self._init_seats(self.max_players)
        for line in self._splitted[2:self._sections[0]]:
            match = self._seat_re.match(line)
            if bool(match):
                index = int(match.group("seat")) - 1
                self.players[index] = hh._Player(
                    name=match.group("name"),
                    stack=Decimal(match.group("stack")),
                    seat=int(match.group("seat")),
                    combo=None,
                )
            # we reached the end of the players section
            else:
                if "posts small blind" in line:
                    self._small_blind_line = line
                elif "posts big blind" in line:
                    self._big_blind_line = line
                # else ignore



    def _parse_button(self):
        button_seat = int(self._table_match.group("button"))
        self.button = self.players[button_seat - 1]

    def _parse_hero(self):
        hole_cards_line = self._splitted[self._sections[0] + 2]
        match = self._hero_re.match(hole_cards_line)
        hero, hero_index = self._get_hero_from_players(match.group("hero_name"))
        hero.combo = Combo(match.group(2) + match.group(3))
        self.hero = self.players[hero_index] = hero
        if self.button.name == self.hero.name:
            self.button = hero

    def _parse_preflop(self):
        start = self._sections[0] + 3
        stop = self._sections[1]
        nocards = [""]  # cause no cards are dealt
        if self._small_blind_line is not None:
            nocards.append(self._small_blind_line)
        if self._big_blind_line is not None:
            nocards.append(self._big_blind_line)
        nocards.extend(self._splitted[start:stop])
        preflop = _Street(nocards)
        self.preflop = preflop

    def _parse_street(self, street_name):
        try:
            start = self._splitted.index(street_name) + 1
        except ValueError:
            setattr(
                self,
                f"{street_name.lower()}",
                None,
            )
            return
        stop = self._splitted.index("", start)
        streetlines = self._splitted[start:stop]
        street = _Street(streetlines)
        setattr(
            self,
            f"{street_name.lower()}",
            street,
        )

    def _parse_showdown(self):
        if "SHOW DOWN" in self._splitted:
            showdown_lines = []
            start_showdown = self._splitted.index("SHOW DOWN")
            end_showdown = self._splitted.index("SUMMARY")
            showdown_lines.extend(self._splitted[start_showdown+1:end_showdown-1])
            street = _Street(showdown_lines)
            self.show_down = street
        else:
            self.show_down = None

    def _parse_pot(self):
        potline = self._splitted[self._sections[-1] + 2]
        match = self._pot_re.match(potline)
        self.total_pot = Decimal(match.group(1))

    def _parse_board(self):
        boardline = self._splitted[self._sections[-1] + 3]
        if not boardline.startswith("Board"):
            return
        cardsstr = self._board_re.findall(boardline)
        i = 0
        # value is not needed to set cause board is populated by property in
        # _BaseHandHistory#board
        for card in cardsstr:
            if self.board[i] != Card(card):
                raise RuntimeError("Boardcard not in Board as expected")
            i += 1

    def _parse_winners(self):
        winners = set()
        start = self._sections[-1] + 4
        for line in self._splitted[start:]:
            if not self.show_down and "collected" in line:
                match = self._winner_re.match(line)
                winners.add(self._clean_name(match.group(2)))
            elif self.show_down and "won" in line and "showed" in line:
                match = self._showdown_re.match(line)
                seat = int(match.group(1))
                playername = self._clean_name(match.group(2))
                split = match.group(3).split()
                playerCombo = Combo.from_cards(Card(split[0]), Card(split[1]))
                self.players[seat - 1].combo = playerCombo
                winners.add(playername)

        self.winners = tuple(winners)

    def _clean_name(self, name):
        name = str.replace(name, "(button)", "")
        name = str.replace(name, "(small blind)", "")
        name = str.replace(name, "(big blind)", "")
        return name
