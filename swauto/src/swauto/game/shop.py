"""Magic / Guild "black market" shop — clean-room port of the recovered shop
wire (docs/07 §3.5, docs/04 Category-10; work/autosw/trace/_B5_shop_recovery_outcome.md).

The oracle probe drove the real ``getShopList`` / ``buyShopItem`` /
``checkShopItem`` / ``checkAndBuyShop`` / ``getGuildShopList`` /
``buyGuildShopItem`` to real sends under the scripted harness and recovered:

- the list/buy RPCs (both the Magic Shop and the Guild Magic Shop are
  **"black markets"** — same ``BlackMarket`` command family):
    ``GetBlackMarketList {cash_used: 0}``
    ``BuyBlackMarketItem {item_master_type, item_no, item_master_id, amount,
                          island_id, pos_x, pos_y}``
    ``GetGuildBlackMarketList {manual_update: 0, guild_id}``
    ``BuyGuildBlackMarketItem {guild_id, item_no, refresh_ts}``
- the buy payload's ``island_id/pos_x/pos_y`` are a *stochastic* cosmetic
  drop-location the client randomizes per buy (re-running the same row varied
  pos 10..29 with island_id fixed 1) — any plausible ints keep the wire shape
  exact.
- ``checkShopItem(item, flags)`` high-value predicate (see :func:`check_shop_item`).

Two layers live here:

- :func:`check_shop_item` — the **pure** keep/buy predicate (offline
  unit-testable; no session required).
- :class:`ShopMixin` — session-bound wire methods (list/buy), attached to
  :class:`~swauto.game.client.BattleClient` so a bot inherits them.
"""

from __future__ import annotations

import logging

from . import constants as C

log = logging.getLogger("swauto.game")

# Whether a bought item may occupy the same island slot coordinate twice is a
# server-side rule; the client always emits a fresh random anchor (B5 §1), so
# the port defaults island_id to 1 and lets the caller pass coordinates.
DEFAULT_ISLAND_ID = 1


def _monster_natural_stars(monsters, item_master_id: int) -> int:
    """Bestiary natural-stars for a star-monster shop row.

    The oracle rates a 2★/4★ offer against its live ``self.monsters`` unit
    dict (2967 entries) — an internal layout that is **not** the clean-room
    ``monsters.data`` bestiary (schema ``com2us_id/natural_stars``). Both key
    by the monster's com2us id, so this helper reads either shape defensively
    and returns 0 when the bestiary is absent/unknown (the caller then treats
    the row as not-rateable). Returns 0 when ``monsters`` is None/empty.
    """
    if not monsters:
        return 0
    entry = monsters.get(item_master_id)
    if not entry:
        return 0
    for key in ("natural_stars", "natural_star", "stars", "grade"):
        v = entry.get(key)
        if v is not None:
            try:
                return int(v)
            except (TypeError, ValueError):
                continue
    return 0


def check_shop_item(item: dict, flags: dict) -> bool:
    """The recovered ``checkShopItem`` high-value predicate (B5 §2).

    Returns whether a Magic/Guild-shop ``item`` row is worth buying given the
    ``flags`` buy-config (docs/05 shop checkboxes — ``buy_rune``,
    ``buy_stone``, ``buy_scroll``, ``buy_unknow``, ``buy_2star``,
    ``buy_4star``).

    Recovered semantics (driven on the oracle):

    - an unavailable row (``available == 0``) is never bought — short-circuits
      ``False`` before any flag is read;
    - dispatch on ``item_master_type``:
        ``1``  → ``flags['buy_2star']``  (2★-monster offer),
        ``12`` → ``flags['buy_4star']``  (4★-monster offer),
        ``9``  → ``flags['buy_scroll']`` (mystic/scroll offer),
        ``27`` → ``flags['buy_stone']``  (rune-stone offer),
        ``_``  → ``False``.
    - a True-eligible row must carry ``item_master_id`` (the branch reads it).

    Live-gated leg: the oracle rates the 2★/4★ *star* of the offered unit
    against its live bestiary before honouring ``buy_2star``/``buy_4star``.
    This port honours the type→flag dispatch exactly and, when the bestiary is
    not supplied, treats a 2★/4★ row as buyable iff its flag is set — the star
    validation itself is marked live-gated (documented, not invented).

    The row may be a dict or a Mapping; missing flag keys read as False.
    """
    if not item:
        return False
    available = item.get("available", 1)
    if available == 0:
        return False
    itype = item.get("item_master_type")
    if itype == C.SHOP_TYPE_SCROLL:      # scrolls
        return bool(flags.get("buy_scroll"))
    if itype == C.SHOP_TYPE_STONE:       # rune stones
        return bool(flags.get("buy_stone"))
    if itype == C.SHOP_TYPE_2STAR:       # 2★ monster
        return bool(flags.get("buy_2star"))
    if itype == C.SHOP_TYPE_4STAR:       # 4★ monster
        return bool(flags.get("buy_4star"))
    # rune slots (item_master_type 8) are evaluated by the rune scorer, not a
    # flat shop flag — never auto-buy here.
    return False


class ShopMixin:
    """Session-bound shop wire methods (one command per call).

    Mixed into :class:`~swauto.game.client.BattleClient` so a live/offline bot
    inherits ``get_shop_list``/``buy_shop_item``/``check_and_buy_shop`` and the
    guild variants. Each method is a thin, recovered-exact ``send``; nothing is
    inferred.

    Guild methods read the account's guild id from ``self.gid`` (set by the
    caller; a profile's ``guild`` section carries it). The Magic-shop buy
    payload carries the stochastic island anchor (B5 §1).
    """

    # -- list -----------------------------------------------------------------
    def get_shop_list(self) -> list:
        """Fetch the Magic-shop inventory (``GetBlackMarketList {cash_used: 0}``)."""
        resp = self.send(C.SHOP_LIST, cash_used=0)
        return resp.get("shop_list") or []

    def get_guild_shop_list(self) -> list:
        """Fetch the Guild-shop inventory (``GetGuildBlackMarketList``)."""
        resp = self.send(C.GUILD_SHOP_LIST, manual_update=0, guild_id=self.gid)
        return resp.get("shop_list") or resp.get("guild_magic_shop") or []

    # -- buy ------------------------------------------------------------------
    def buy_shop_item(self, item: dict, *, island_id: int = DEFAULT_ISLAND_ID,
                      pos_x: int | None = None, pos_y: int | None = None) -> dict:
        """Buy one Magic-shop row (``BuyBlackMarketItem``).

        Reads exactly the recovered payload fields off ``item``:
        ``item_master_type``, ``item_no``, ``item_master_id``, ``amount``. The
        island anchor is stochastic in the oracle; ``pos_x``/``pos_y`` default
        to small random ints and ``island_id`` to 1 unless the caller passes
        them.
        """
        import random
        payload = {
            "item_master_type": item["item_master_type"],
            "item_no": item["item_no"],
            "item_master_id": item["item_master_id"],
            "amount": int(item.get("amount", 1) or 1),
            "island_id": island_id,
            "pos_x": pos_x if pos_x is not None else random.randint(1, 30),
            "pos_y": pos_y if pos_y is not None else random.randint(1, 30),
        }
        return self.send(C.SHOP_BUY, **payload)

    def buy_guild_shop_item(self, item: dict, *, refresh_ts: int = 0) -> dict:
        """Buy one Guild-shop row (``BuyGuildBlackMarketItem``).

        Reads ``item_no`` off the row; the payload is just ``guild_id`` +
        ``item_no`` + ``refresh_ts`` (defaulted 0, the probe value).
        """
        return self.send(C.GUILD_SHOP_BUY, guild_id=self.gid,
                         item_no=item["item_no"], refresh_ts=refresh_ts)

    # -- orchestration ---------------------------------------------------------
    def check_and_buy_shop(self, flags: dict) -> int:
        """Scan the Magic shop and buy every row the buy-flags accept.

        Recovered driver contract (B5 §3): fetch ``GetBlackMarketList``, then
        evaluate each row with :func:`check_shop_item` and buy the True rows.
        Returns the number bought. The original's *auto-refresh cadence*
        (spending crystals to re-roll the list) needs live shop state and is a
        documented live boundary — this method never re-rolls on its own.
        """
        bought = 0
        for row in self.get_shop_list():
            if check_shop_item(row, flags):
                log.info("Buying shop row %s (type %s)", row.get("item_no"),
                         row.get("item_master_type"))
                self.buy_shop_item(row)
                bought += 1
        return bought

    def check_and_buy_guild_shop(self, flags: dict) -> int:
        """Scan the Guild shop and buy every accepted row (guild analogue)."""
        bought = 0
        for row in self.get_guild_shop_list():
            if check_shop_item(row, flags):
                log.info("Buying guild-shop row %s (type %s)", row.get("item_no"),
                         row.get("item_master_type"))
                self.buy_guild_shop_item(row)
                bought += 1
        return bought
