import re
from decimal import Decimal

import pytest

from poker.card import Card
from poker.hand import Combo
from poker.handhistory import _Player
from poker.jsonencoding import JsonEncoder
from poker.room.pokerstars import _Street, PokerStarsHandHistory
from tests.handhistory import stars_hands


@pytest.fixture(scope='function')
def json_encoder():
    return JsonEncoder()


class TestCardEncoding:

    def tests_simple_card(self, json_encoder):
        card = Card("Ad")
        assert json_encoder.encode(card) == "{\"rank\": \"A\", \"suit\": \"DIAMONDS\"}"

    def test_combo_encoding(self, json_encoder):
        combo = Combo.from_cards(Card("Ad"), Card("Kc"))
        expected = "{\"1\": {\"rank\": \"A\", \"suit\": \"DIAMONDS\"}, \"2\": {\"rank\": \"K\", \"suit\": \"CLUBS\"}}"
        assert json_encoder.encode(combo) == expected


class TestStreetEncoding:

    def test_street_flop_encoding(self, json_encoder):
        street = _Street(["[Ad Ks Qc]", ],)
        expected = """{"cards": [{"rank": "A", "suit": "DIAMONDS"}, {"rank": "K", "suit": "SPADES"}, {"rank": "Q", "suit": "CLUBS"}]"""
        assert expected in json_encoder.encode(street)

    def test_board_tuple_encoding(self, json_encoder):
        board = tuple([Card("Ad"), Card("Ks"), Card("Qc"), Card("Jh"), Card("Ts")])
        data= {'board': list(board)}
        expected = "{\"board\": [{\"rank\": \"A\", \"suit\": \"DIAMONDS\"}, {\"rank\": \"K\", \"suit\": \"SPADES\"}, " \
                   "{\"rank\": \"Q\", \"suit\": \"CLUBS\"}, {\"rank\": \"J\", \"suit\": \"HEARTS\"}, " \
                   "{\"rank\": \"T\", \"suit\": \"SPADES\"}]}"
        assert json_encoder.encode(data) == expected

    def test_actions_encoding(self, json_encoder):
        street = _Street(["[8s 5h Jh]", "pokerhero: checks", "ROMPAL76: bets $0.07", "heureka3: calls $0.07", "pokerhero: folds"])
        json = json_encoder.encode(street)
        expected = "{\"actions\": [{\"name\": \"pokerhero\", \"action\": \"CHECK\"}, " \
                   "{\"name\": \"ROMPAL76\", \"action\": \"BET\", \"amount\": 0.07}, " \
                   "{\"name\": \"heureka3\", \"action\": \"CALL\", \"amount\": 0.07}, " \
                   "{\"name\": \"pokerhero\", \"action\": \"FOLD\"}]"
        assert expected in json


class TestPlayer:

    def test_player_encoding_with_combo(self, json_encoder):
        hero_combo = Combo.from_cards(Card("Ad"), Card("Kc"))
        hero = _Player(name="pokerHero", stack=Decimal('1.86'), seat=3, combo=hero_combo)
        expected = "{\"name\": \"pokerHero\", \"stack\": 1.86, \"seat\": 3, \"hand\": " \
                   "{\"1\": {\"rank\": \"A\", \"suit\": \"DIAMONDS\"}, \"2\": {\"rank\": \"K\", \"suit\": \"CLUBS\"}}}"
        assert json_encoder.encode(hero) == expected

    def test_player_encoding_without_combo(self, json_encoder):
        hero = _Player(name="pokerHero", stack=Decimal('1.86'), seat=3, combo=None)
        assert json_encoder.encode(hero) == "{\"name\": \"pokerHero\", \"stack\": 1.86, \"seat\": 3}"


def get_parsed_hand():
    hand_text = stars_hands.HAND12
    hh = PokerStarsHandHistory(hand_text)
    hh.parse()
    return hh


def get_parsed_flop_hand13():
    hand_text = stars_hands.HAND13
    hh = PokerStarsHandHistory(hand_text)
    hh.parse()
    return hh


def get_parsed_flop_hand14():
    hand_text = stars_hands.HAND14
    hh = PokerStarsHandHistory(hand_text)
    hh.parse()
    return hh


class TestFullPokerstarsHand:

    def test_board(self, json_encoder):
        hand_history = get_parsed_hand()
        json = json_encoder.encode(hand_history)
        expected = "\"board\": [{\"rank\": \"3\", \"suit\": \"CLUBS\"}, {\"rank\": \"3\", \"suit\": \"HEARTS\"}, " \
                   "{\"rank\": \"3\", \"suit\": \"SPADES\"}, {\"rank\": \"7\", \"suit\": \"CLUBS\"}, " \
                   "{\"rank\": \"K\", \"suit\": \"SPADES\"}]"
        assert expected in json

    def test_bb(self, json_encoder):
        json = json_encoder.encode(get_parsed_hand())
        assert "\"bb\": 0.02" in json

    def test_sb(self, json_encoder):
        json = json_encoder.encode(get_parsed_hand())
        assert "\"sb\": 0.01" in json

    def test_button(self, json_encoder):
        json = json_encoder.encode(get_parsed_hand())
        expected_button = "\"button\": \"sindyeichelbaum\""
        assert expected_button in json

    def test_currency(self, json_encoder):
        json = json_encoder.encode(get_parsed_hand())
        assert "\"currency\": \"USD\"" in json

    def test_date(self, json_encoder):
        json = json_encoder.encode(get_parsed_hand())
        assert "\"timestamp\": \"2020-04-25 17:29:31+00:00\"" in json

    def test_money_type(self, json_encoder):
        json = json_encoder.encode(get_parsed_hand())
        assert "\"moneytype\": \"Real money\"" in json

    def test_ident(self, json_encoder):
        json = json_encoder.encode(get_parsed_hand())
        assert "\"id\": 212700439098" in json

    def test_game(self, json_encoder):
        json = json_encoder.encode(get_parsed_hand())
        assert "\"game\": \"Hold\'em\"" in json

    def test_game_type(self, json_encoder):
        json = json_encoder.encode(get_parsed_hand())
        assert "\"gametype\": \"Cash game\"" in json

    def test_limit_type(self, json_encoder):
        json = json_encoder.encode(get_parsed_hand())
        assert "\"limit\": \"NL\"" in json

    def test_table_name(self, json_encoder):
        json = json_encoder.encode(get_parsed_hand())
        assert "\"tablename\": \"Heike II\"" in json

    def test_max_players(self, json_encoder):
        json = json_encoder.encode(get_parsed_hand())
        assert "\"max-players\": 9" in json

    def test_hero(self, json_encoder):
        json = json_encoder.encode(get_parsed_hand())
        assert "\"hero\": \"pokerhero\"" in json

    def test_rake(self, json_encoder):
        handhistory = get_parsed_hand()
        handhistory.rake = Decimal('0.10')
        json = json_encoder.encode(handhistory)
        assert "\"rake\": 0.1" in json

    def test_tournament_id(self, json_encoder):
        handhistory = get_parsed_hand()
        handhistory.tournament_ident = 123456789
        json = json_encoder.encode(handhistory)
        assert "\"tournament-id\": 123456789" in json

    def test_tournament_level(self, json_encoder):
        handhistory = get_parsed_hand()
        handhistory.tournament_level = "XI"
        json = json_encoder.encode(handhistory)
        assert "\"tournament-level\": \"XI\"" in json

    def test_players(self, json_encoder):
        json = json_encoder.encode(get_parsed_hand())
        assert "\"players\": [{\"name\": \"Empty Seat 1\", \"stack\": 0.0, \"seat\": 1}, " \
               "{\"name\": \"pokerhero\", \"stack\": 2.0, \"seat\": 2, " \
                    "\"hand\": {\"1\": {\"rank\": \"T\", \"suit\": \"HEARTS\"}, \"2\": {\"rank\": \"5\", \"suit\": \"SPADES\"}}}, " \
               "{\"name\": \"oeggel\", \"stack\": 2.05, \"seat\": 3}, " \
               "{\"name\": \"3_Socks420\", \"stack\": 0.96, \"seat\": 4}, " \
               "{\"name\": \"Laandris09\", \"stack\": 3.55, \"seat\": 5}, " \
               "{\"name\": \"Ammageddon\", \"stack\": 3.48, \"seat\": 6}, " \
               "{\"name\": \"BigSiddyB\", \"stack\": 2.93, \"seat\": 7, " \
                    "\"hand\": {\"1\": {\"rank\": \"A\", \"suit\": \"SPADES\"}, \"2\": {\"rank\": \"Q\", \"suit\": \"HEARTS\"}}}, " \
               "{\"name\": \"sindyeichelbaum\", \"stack\": 0.63, \"seat\": 8, " \
                    "\"hand\": {\"1\": {\"rank\": \"A\", \"suit\": \"DIAMONDS\"}, \"2\": {\"rank\": \"9\", \"suit\": \"HEARTS\"}}}, " \
               "{\"name\": \"masterhodge\", \"stack\": 1.8, \"seat\": 9}]" in json

    def test_has_showdown(self, json_encoder):
        json = json_encoder.encode(get_parsed_hand())
        assert "\"showdown\": \"True\"" in json

    def test_preflop(self, json_encoder):
        json = json_encoder.encode(get_parsed_hand())
        expected = "\"preflop\": {\"actions\": [{\"name\": \"masterhodge\", \"action\": \"SB\", \"amount\": 0.01}, " \
                        "{\"name\": \"pokerhero\", \"action\": \"BB\", \"amount\": 0.02}, " \
                        "{\"name\": \"oeggel\", \"action\": \"FOLD\"}, " \
                        "{\"name\": \"3_Socks420\", \"action\": \"FOLD\"}, " \
                        "{\"name\": \"Laandris09\", \"action\": \"FOLD\"}, " \
                        "{\"name\": \"Ammageddon\", \"action\": \"FOLD\"}, " \
                        "{\"name\": \"BigSiddyB\", \"action\": \"RAISE\", \"amount\": 0.04}, " \
                        "{\"name\": \"sindyeichelbaum\", \"action\": \"RAISE\", \"amount\": 0.63}, " \
                        "{\"name\": \"masterhodge\", \"action\": \"FOLD\"}, "\
                        "{\"name\": \"pokerhero\", \"action\": \"FOLD\"}, " \
                        "{\"name\": \"BigSiddyB\", \"action\": \"CALL\", \"amount\": 0.59}]}"
        assert expected in json

    def test_flop_actions(self, json_encoder):
        json = json_encoder.encode(get_parsed_flop_hand13())
        expected = "\"flop\": {\"actions\": [{\"name\": \"pokerhero\", \"action\": \"CHECK\"}, " \
                   "{\"name\": \"ROMPAL76\", \"action\": \"BET\", \"amount\": 0.07}, " \
                   "{\"name\": \"heureka3\", \"action\": \"CALL\", \"amount\": 0.07}, " \
                   "{\"name\": \"pokerhero\", \"action\": \"FOLD\"}]"
        assert expected in json

    def test_flop_cards(self, json_encoder):
        json = json_encoder.encode(get_parsed_flop_hand13())
        # 8s 5h Jh
        expected = ": [{\"rank\": \"8\", \"suit\": \"SPADES\"}, {\"rank\": \"5\", \"suit\": \"HEARTS\"}, " \
                   "{\"rank\": \"J\", \"suit\": \"HEARTS\"}]"
        assert expected in json

    def test_flop_attribute_flushdraw(self, json_encoder):
        json = json_encoder.encode(get_parsed_flop_hand13())
        expected = "\"flushdraw\": true"
        assert expected in json

    def test_flop_attribute_gutshot(self, json_encoder):
        json = json_encoder.encode(get_parsed_flop_hand13())
        expected = "\"gutshot\": false"
        assert expected in json

    def test_flop_attribute_paired(self, json_encoder):
        json = json_encoder.encode(get_parsed_flop_hand13())
        expected = "\"paired\": false"
        assert expected in json

    def test_flop_attribute_straightdraw(self, json_encoder):
        json = json_encoder.encode(get_parsed_flop_hand13())
        expected = "\"straightdraw\": false"
        assert expected in json

    def test_flop_attribute_monotone(self, json_encoder):
        json = json_encoder.encode(get_parsed_flop_hand13())
        expected = "\"flushdraw\": true"
        assert expected in json

    def test_flop_attribute_triplet(self, json_encoder):
        json = json_encoder.encode(get_parsed_flop_hand13())
        expected = "\"triplet\": true"
        assert expected in json

    def test_turn_card(self, json_encoder):
        json = json_encoder.encode(get_parsed_flop_hand13())
        expected = "{\"rank\": \"2\", \"suit\": \"HEARTS\"}"
        assert expected in json

    def test_turn_actions(self, json_encoder):
        json = json_encoder.encode(get_parsed_flop_hand13())
        expected = "\"actions\": [{\"name\": \"ROMPAL76\", \"action\": \"CHECK\"}, " \
                   "{\"name\": \"heureka3\", \"action\": \"CHECK\"}]"
        assert expected in json

    def test_river_card(self, json_encoder):
        json = json_encoder.encode(get_parsed_flop_hand13())
        expected = "{\"rank\": \"2\", \"suit\": \"CLUBS\"}"
        assert expected in json

    def test_river_actions(self, json_encoder):
        json = json_encoder.encode(get_parsed_flop_hand13())
        expected = "\"actions\": [{\"name\": \"ROMPAL76\", \"action\": \"BET\", \"amount\": 0.1}, " \
                   "{\"name\": \"heureka3\", \"action\": \"CALL\", \"amount\": 0.1}]"
        assert expected in json

    def test_winners(self, json_encoder):
        json = json_encoder.encode(get_parsed_hand())
        winners = re.search("\"winners\": \[(.*)\]", json).group(1)
        assert "BigSiddyB" in winners
        assert "sindyeichelbaum (button)" in winners

    def test_total_pot(self, json_encoder):
        json = json_encoder.encode(get_parsed_flop_hand13())
        assert "\"total_pot\": 0.49" in json

    def test_earnings(self, json_encoder):
        json = json_encoder.encode(get_parsed_flop_hand13())
        assert "\"earnings\": -0.05" in json

    def test_cash_out(self, json_encoder):
        json = json_encoder.encode(get_parsed_flop_hand14())
        print(json)
        assert "\"earnings\": -2.34" in json
