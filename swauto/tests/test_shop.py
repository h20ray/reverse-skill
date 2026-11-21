"""Shop wire tests — Magic/Guild "black market" port (B5).

The list/buy RPC payloads and the checkShopItem type→flag dispatch were
recovered by driving the real oracle methods offline
(work/autosw/trace/_B5_shop_recovery_outcome.md). These tests pin the
recovered-exact wire shape: a pure predicate + a session mixin that sends
one command per buy/list.
"""

from swauto.game import constants as C
from swauto.game.shop import (
    ShopMixin,
    _monster_natural_stars,
    check_shop_item,
)
from swauto.net.transport import ScriptedTransport
from swauto.game.loops import Loops


# -- check_shop_item predicate -----------------------------------------------

def _row(item_master_type: int, *, available: int = 1, **kw) -> dict:
    row = {
        "item_id": 1, "item_no": 1, "box_type": 8, "master_id": 100,
        "quantity": 1, "amount": 1, "item_master_type": item_master_type,
        "item_master_id": 90001, "cost_type": 1, "cost": 100,
        "available": available, "rune_rank": 6, "rune_class": 6,
    }
    row.update(kw)
    return row


def test_unavailable_row_never_bought():
    """available == 0 short-circuits False before any flag is read."""
    for t in (C.SHOP_TYPE_SCROLL, C.SHOP_TYPE_STONE,
              C.SHOP_TYPE_2STAR, C.SHOP_TYPE_4STAR):
        assert check_shop_item(_row(t, available=0),
                               {"buy_scroll": 1, "buy_stone": 1}) is False


def test_scroll_needs_buy_scroll():
    assert check_shop_item(_row(C.SHOP_TYPE_SCROLL), {"buy_scroll": 1}) is True
    assert check_shop_item(_row(C.SHOP_TYPE_SCROLL), {}) is False
    # an unrelated flag doesn't buy a scroll
    assert check_shop_item(_row(C.SHOP_TYPE_SCROLL),
                           {"buy_stone": 1}) is False


def test_stone_needs_buy_stone():
    assert check_shop_item(_row(C.SHOP_TYPE_STONE), {"buy_stone": 1}) is True
    assert check_shop_item(_row(C.SHOP_TYPE_STONE), {}) is False


def test_two_and_four_star_need_their_flags():
    assert check_shop_item(_row(C.SHOP_TYPE_2STAR), {"buy_2star": 1}) is True
    assert check_shop_item(_row(C.SHOP_TYPE_2STAR), {}) is False
    assert check_shop_item(_row(C.SHOP_TYPE_4STAR), {"buy_4star": 1}) is True
    assert check_shop_item(_row(C.SHOP_TYPE_4STAR), {}) is False


def test_unknown_master_types_never_buy():
    for t in (0, 2, 3, 8, 99):
        assert check_shop_item(_row(t), {
            "buy_rune": 1, "buy_stone": 1, "buy_scroll": 1,
            "buy_2star": 1, "buy_4star": 1}) is False


def test_missing_available_is_not_sold():
    row = _row(C.SHOP_TYPE_SCROLL)
    row.pop("available")
    assert check_shop_item(row, {"buy_scroll": 1}) is True


def test_empty_item_false():
    assert check_shop_item({}, {"buy_scroll": 1}) is False
    assert check_shop_item(None, {"buy_scroll": 1}) is False


# -- _monster_natural_stars (bestiary helper) --------------------------------

def test_bestiary_natural_stars_reads_com2us_shape():
    monsters = {1001: {"com2us_id": 1001, "natural_stars": 2}}
    assert _monster_natural_stars(monsters, 1001) == 2
    # missing entry / missing bestiary -> 0
    assert _monster_natural_stars(monsters, 9999) == 0
    assert _monster_natural_stars(None, 1001) == 0


# -- shop wire methods --------------------------------------------------------

def _shop_bot(responses=None):
    transport = ScriptedTransport(responses or {"*": lambda p: {"ret_code": 0}})
    bot = Loops(transport, sleeper=lambda s: None)
    bot.gid = 4
    return bot, transport


def test_get_shop_list_sends_black_market_list():
    """getShopList -> GetBlackMarketList {cash_used: 0}."""
    bot, transport = _shop_bot({"GetBlackMarketList": {
        "ret_code": 0, "shop_list": [{"item_no": 1}]}})
    rows = bot.get_shop_list()
    assert rows == [{"item_no": 1}]
    cmd, payload = transport.calls[0]
    assert cmd == "GetBlackMarketList"
    assert payload["command"] == "GetBlackMarketList"
    assert payload["cash_used"] == 0


def test_get_guild_shop_list_sends_guild_black_market_list():
    bot, transport = _shop_bot({"GetGuildBlackMarketList": {
        "ret_code": 0, "shop_list": [{"item_no": 2}]}})
    rows = bot.get_guild_shop_list()
    assert rows == [{"item_no": 2}]
    cmd, payload = transport.calls[0]
    assert cmd == "GetGuildBlackMarketList"
    assert payload["command"] == "GetGuildBlackMarketList"
    assert payload["manual_update"] == 0
    assert payload["guild_id"] == 4


def test_buy_shop_item_payload_exact():
    """buyShopItem reads item_master_type/item_no/item_master_id/amount and
    appends the island anchor — recovered-exact BuyBlackMarketItem."""
    bot, transport = _shop_bot({"BuyBlackMarketItem": {"ret_code": 0}})
    row = _row(C.SHOP_TYPE_SCROLL, item_no=7, item_master_id=1011,
               amount=2, cost=75000)
    bot.buy_shop_item(row, pos_x=5, pos_y=6)
    cmd, payload = transport.calls[0]
    assert cmd == "BuyBlackMarketItem"
    assert payload["command"] == "BuyBlackMarketItem"
    assert payload["item_master_type"] == C.SHOP_TYPE_SCROLL
    assert payload["item_no"] == 7
    assert payload["item_master_id"] == 1011
    assert payload["amount"] == 2
    assert payload["island_id"] == 1
    assert payload["pos_x"] == 5 and payload["pos_y"] == 6


def test_buy_shop_item_defaults_amount_one_and_random_anchor():
    """amount defaults to 1; the island anchor is stochastic (B5 §1) but the
    island_id stays 1 and pos are small positive ints."""
    bot, transport = _shop_bot({"BuyBlackMarketItem": {"ret_code": 0}})
    row = _row(C.SHOP_TYPE_SCROLL, item_no=3, item_master_id=1011)
    bot.buy_shop_item(row)
    payload = transport.calls[0][1]
    assert payload["amount"] == 1
    assert payload["island_id"] == 1
    assert 1 <= payload["pos_x"] <= 30
    assert 1 <= payload["pos_y"] <= 30


def test_buy_guild_shop_item_payload_exact():
    """buyGuildShopItem -> BuyGuildBlackMarketItem {guild_id, item_no,
    refresh_ts} — the probe's refresh_ts default was 0."""
    bot, transport = _shop_bot({"BuyGuildBlackMarketItem": {"ret_code": 0}})
    bot.gid = 4
    bot.buy_guild_shop_item({"item_no": 9})
    cmd, payload = transport.calls[0]
    assert cmd == "BuyGuildBlackMarketItem"
    assert payload["command"] == "BuyGuildBlackMarketItem"
    assert payload["guild_id"] == 4
    assert payload["item_no"] == 9
    assert payload["refresh_ts"] == 0


def test_check_and_buy_shop_scans_and_buys_accepted_rows():
    """Driver: fetch GetBlackMarketList, buy every check_shop_item-True row."""
    rows = [
        _row(C.SHOP_TYPE_SCROLL, item_no=1, cost=75000),   # buy_scroll -> buy
        _row(C.SHOP_TYPE_STONE, item_no=2, cost=100000),   # no flag -> skip
        _row(C.SHOP_TYPE_SCROLL, item_no=3, cost=150000),  # buy_scroll -> buy
    ]
    bot, transport = _shop_bot({
        "GetBlackMarketList": {"ret_code": 0, "shop_list": rows},
        "*": {"ret_code": 0}})
    n = bot.check_and_buy_shop({"buy_scroll": 1})
    assert n == 2
    cmds = [c[0] for c in transport.calls]
    assert cmds == ["GetBlackMarketList", "BuyBlackMarketItem", "BuyBlackMarketItem"]
    # the two bought rows are 1 and 3 (row 2 is a stone, not flagged)
    bought_nos = [transport.calls[i][1]["item_no"] for i in (1, 2)]
    assert bought_nos == [1, 3]


def test_check_and_buy_guild_shop():
    rows = [_row(C.SHOP_TYPE_STONE, item_no=5), _row(C.SHOP_TYPE_SCROLL, item_no=6)]
    bot, transport = _shop_bot({
        "GetGuildBlackMarketList": {"ret_code": 0, "shop_list": rows},
        "*": {"ret_code": 0}})
    n = bot.check_and_buy_guild_shop({"buy_stone": 1})
    assert n == 1
    assert transport.calls[0][0] == "GetGuildBlackMarketList"
    cmd, payload = transport.calls[1]
    assert cmd == "BuyGuildBlackMarketItem"
    assert payload["guild_id"] == 4
    assert payload["item_no"] == 5
    assert payload["refresh_ts"] == 0


def test_shop_constants_wire_names():
    assert C.SHOP_LIST == "GetBlackMarketList"
    assert C.SHOP_BUY == "BuyBlackMarketItem"
    assert C.GUILD_SHOP_LIST == "GetGuildBlackMarketList"
    assert C.GUILD_SHOP_BUY == "BuyGuildBlackMarketItem"
