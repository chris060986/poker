import jsonpickle
from jsonpickle.handlers import BaseHandler

from poker import Card, Combo
from poker.handhistory import _BaseStreet, _BaseHandHistory, _Player, _PlayerAction


@jsonpickle.handlers.register(Card, base=True)
class CardHandler(BaseHandler):

    def flatten(self, obj, data):
        data = {'rank': obj.rank.val, 'suit': obj.suit.name}
        return data

    def restore(self, obj):
        raise NotImplementedError


@jsonpickle.handlers.register(Combo, base=True)
class ComboHandler(BaseHandler):

    def flatten(self, obj, data):
        data = {'1': self.context.flatten(obj.first, reset=False), '2': self.context.flatten(obj.second, reset=False)}
        return data

    def restore(self, obj):
        raise NotImplementedError


@jsonpickle.handlers.register(_Player, base=True)
class PlayerHandler(BaseHandler):

    def flatten(self, obj, data):
        data.clear()
        data = {'name': obj.name, 'stack': float(obj.stack), 'seat': obj.seat}
        if obj.combo is not None:
            data['hand'] = self.context.flatten(obj.combo, reset=False)
        return data

    def restore(self, obj):
        raise NotImplementedError


@jsonpickle.handlers.register(_PlayerAction, base=True)
class PlayerActionsHandler(BaseHandler):

    def flatten(self, obj, data):
        data = {}
        data['name'] = obj.name
        data['action'] = obj.action.name
        if obj.amount is not None:
            data['amount'] = float(obj.amount)
        return data

    def restore(self, obj):
        raise NotImplementedError


@jsonpickle.handlers.register(_BaseStreet, base=True)
class StreetHandler(BaseHandler):

    def flatten(self, obj, data):
        data = {}
        if obj.actions is not None:
            data['actions'] = [self.context.flatten(action, reset=False) for action in obj.actions]
        if obj.cards is not None:
            data['cards'] = [self.context.flatten(x, reset=False) for x in obj.cards]
            data['flushdraw'] = obj.has_flushdraw
            data['gutshot'] = obj.has_gutshot
            data['paired'] = obj.has_pair
            data['straightdraw'] = obj.has_straightdraw
            data['monotone'] = obj.is_monotone
            data['triplet'] = obj.is_triplet
        return data

    def restore(self, obj):
        raise NotImplementedError


@jsonpickle.handlers.register(_BaseHandHistory, base=True)
class HandHistoryHandler(BaseHandler):

    def flatten(self, obj, data):
        data = {}
        data['timestamp'] = str(obj.date)
        data['id'] = int(obj.ident)
        data['tablename'] = obj.table_name
        data['bb'] = float(obj.bb)
        data['sb'] = float(obj.sb)
        data['game'] = str(obj.game)
        data['gametype'] = str(obj.game_type)
        data['limit'] = str(obj.limit)
        data['max-players'] = obj.max_players
        data['hero'] = obj.hero.name
        data['button'] = obj.button.name
        if obj.total_pot is not None:
            data['total_pot'] = float(obj.total_pot)
        if obj.rake is not None:
            data['rake'] = float(obj.rake)
        if obj.tournament_ident is not None:
            data['tournament-id'] = int(obj.tournament_ident)
        if obj.tournament_level is not None:
            data['tournament-level'] = str(obj.tournament_level)
        if obj.currency is not None:
            data['currency'] = str(obj.currency)
        if obj.extra is not None and obj.extra.get('money_type') is not None:
            data['moneytype'] = str(obj.extra.get('money_type'))
        data['players'] = [self.context.flatten(player, reset=True) for player in obj.players]

        if obj.preflop is not None:
            preflop_actions = [self.context.flatten(action, reset=False) for action in obj.preflop.actions]
            data['preflop'] = {'actions': preflop_actions}

        if obj.flop is not None:
            data['flop'] = self.context.flatten(obj.flop, reset=True)

        if obj.turn is not None:
            data['turn'] = self.context.flatten(obj.turn, reset=True)

        if obj.river is not None:
            data['river'] = self.context.flatten(obj.river, reset=True)

        if obj.show_down is not None:
            data['show_down'] = self.context.flatten(obj.show_down, reset=True)

        if obj.board is not None:
            board_ = [self.context.flatten(card, reset=True) for card in obj.board]
            data['board'] = board_
        data['winners'] = obj.winners

        if obj.earnings is not None:
            data['earnings'] = float(obj.earnings)
        return data

    def restore(self, obj):
        raise NotImplementedError


class JsonEncoder:

    def encode(self, obj):
        return jsonpickle.encode(obj)
