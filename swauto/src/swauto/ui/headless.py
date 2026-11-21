"""Headless CLI — run tasks offline against a scripted transport, or
(list/timing/rule utilities) without any network use. ``live-login`` performs a
real authenticated POST against the operator's own gateway (live-only leg)."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from ..config.profile import AccountSnapshot
from ..game.timing import dungeon_time, tower_time
from ..net.transport import (GatewayTransport, SMON_CHECKER_PLACEHOLDER,
                             USER_AGENT, ScriptedTransport, gateway_url,
                             gateway_version_url)
from ..net.login import (DEFAULT_GAME_INDEX, DEFAULT_INFOCSV, DEFAULT_PROTO_VER,
                         LiveVersionFetcher, LoginClient)
from ..game.loops import Loops


def _offline_session() -> Loops:
    """A session wired to a demo scripted server (no real network)."""
    def handler(payload):
        cmd = payload.get("command")
        if cmd == "GetWizardInfo":
            return {"wizard_info": {"wizard_energy": 999, "wizard_crystal": 1000}}
        if cmd == "GetDungeonBestCommunityRanking":
            return {"my_ranking": {"clear_time": 32000, "my_unit_deck_list": []}}
        if cmd == "GetDungeonList":
            return {
                "ret_code": 0,
                "dungeon_list": [
                    {"dungeon_id": 8001, "group_id": 1, "stage_list": [{"stage_id": i + 1, "cleared": 1} for i in range(10)]},
                    {"dungeon_id": 9001, "group_id": 1, "stage_list": [{"stage_id": i + 1, "cleared": 1} for i in range(10)]},
                    {
                        "dungeon_id": 10065,
                        "group_id": 10,
                        "unit_master_id": 18212,
                        "stage_list": [
                            {"stage_id": 1, "cleared": 1},
                            {"stage_id": 2, "cleared": 1},
                            {"stage_id": 3, "cleared": 0},
                            {"stage_id": 4, "cleared": 0},
                            {"stage_id": 5, "cleared": 0},
                            {"stage_id": 6, "cleared": 0},
                            {"stage_id": 7, "cleared": 0},
                            {"stage_id": 8, "cleared": 0},
                            {"stage_id": 9, "cleared": 0},
                            {"stage_id": 10, "cleared": 0},
                        ],
                    },
                ],
            }
        if cmd == "BattleDungeonStart":
            return {"battle_key": 1, "drop_list": []}
        return {"ret_code": 0, "drop_list": []}
    return Loops(ScriptedTransport({"*": handler}), sleeper=lambda s: None)


def cmd_dungeon_list(args) -> int:
    session = _offline_session()
    dungeons = session.get_dungeon_list()
    print(json.dumps(dungeons, indent=2))
    return 0


def cmd_run(args) -> int:
    import logging
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    async def _run():
        session = _offline_session()
        session.rng.seed(args.seed)
        from ..scheduler.engine import TaskManager
        mgr = TaskManager(session)
        params = json.loads(args.params) if args.params else {}
        params.setdefault("times", 2)  # demo default; a real profile supplies its own
        if args.task == "dungeon":
            params.setdefault("dungeon_id", 8001)   # Giant
        elif args.task == "hoh":
            params.setdefault("dungeon_id", 10065)  # Sample HoH
        if args.profile:
            snap = AccountSnapshot.load(args.profile)
            params.setdefault("units", snap.best_units(7))
        tid = mgr.create_task(args.task, params)
        await mgr.wait_all()
        print(json.dumps({"task_id": tid, "status": mgr.status(tid),
                          "runs": mgr.tasks[tid].runs}))
    return asyncio.run(_run())


def cmd_time(args) -> int:
    if args.kind == "tower":
        print(tower_time(args.level, args.difficulty))
    else:
        record = args.record / 1000 if args.record else None
        print(dungeon_time(record))
    return 0


def cmd_score(args) -> int:
    from ..game.score import flatten_rune, rune_score
    rune = json.loads(sys.stdin.read())
    print(rune_score(flatten_rune(rune)))
    return 0


def cmd_live_login(args) -> int:
    """Perform a real version_info_c2 + HubUserLogin against the operator's
    own gateway, and save the fresh session to a profile snapshot.

    This is the live-only leg: it POSTs to the real Com2uS gateway for the
    operator's own account (scope: authorized_target_only). The saved profile
    carries live session keys — it is written to ``profiles/`` (gitignored) and
    never committed; ``AccountSnapshot.sanitize()`` is the only shareable path.
    """
    import logging

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    profile = args.profile
    if not profile:
        raise SystemExit("live-login requires --profile <account snapshot .json>")

    snap = AccountSnapshot.load(profile)
    server_id = snap.server_id  # this_server_id
    if not server_id:
        raise SystemExit("profile has no this_server_id; cannot route the gateway")
    wizard_id = snap.wizard_id
    if not wizard_id:
        raise SystemExit("profile has no wizard_id")

    if args.allow_placeholder_checker and args.smon_checker == SMON_CHECKER_PLACEHOLDER:
        # The operator explicitly opted into the placeholder SmonChecker.
        pass
    elif args.smon_checker == SMON_CHECKER_PLACEHOLDER:
        raise SystemExit(
            "Refusing to send the placeholder SmonChecker (0*40) on a live "
            "request — the real checksum algorithm is live-only. Pass "
            "--smon-checker <40hex> to supply the real value, or "
            "--allow-placeholder-checker to proceed with the placeholder.")

    gate_url = gateway_url(server_id)
    ver_url = gateway_version_url(server_id)
    transport = GatewayTransport(
        gate_url,
        smon_checker=args.smon_checker,
        user_agent=args.user_agent or USER_AGENT)

    ver_fetcher = LiveVersionFetcher(transport, ver_url, game_index=DEFAULT_GAME_INDEX)
    client = LoginClient(transport,
                         proto_ver=DEFAULT_PROTO_VER, infocsv=DEFAULT_INFOCSV,
                         fetch_version=ver_fetcher)

    # 1. version_info_c2 (4-field request) — refreshes proto_ver/infocsv.
    ver = client.fetch_version()
    print("[version_info_c2] proto_ver=%s infocsv=%s" %
          (client.proto_ver, client.infocsv))
    ret = ver.get("ret_code", 0)
    if ret not in (0, None):
        raise SystemExit("version_info_c2 returned ret_code=%s" % ret)

    # 2. HubUserLogin (8-field envelope) — the account session.
    resp, state = client.login_response(wizard_id)
    if state is None:
        raise SystemExit("HubUserLogin refused (block/ret_code != 0)")

    # Save the fresh session to a profile snapshot (never committed).
    # The raw login RESPONSE is the authoritative account snapshot (docs/07
    # §1.4), so it is what gets persisted — fresh session keys and all. It is
    # written under profiles/ (gitignored) and never committed.
    out_dir = Path(args.out or "profiles")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"fresh_{wizard_id}.json"
    out_path.write_text(json.dumps(resp, indent=2), encoding="utf-8")
    print("[HubUserLogin] wizard=%s server=%s session saved -> %s"
          % (wizard_id, server_id, out_path))
    print("[session] session_key=%s.. session_key_node=%s.."
          % (str(state.session_key)[:8], str(state.session_key_node)[:8]))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="swauto")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("run", help="run a task against the offline demo server")
    p.add_argument("--task", default="dungeon")
    p.add_argument("--profile", help="account snapshot JSON (units for decks)")
    p.add_argument("--params", help="task params JSON string")
    p.add_argument("--seed", type=int, default=0)
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("dungeon-list", help="list all available dungeons including HoH")
    p.set_defaults(func=cmd_dungeon_list)

    p = sub.add_parser(
        "live-login",
        help="real version_info_c2 + HubUserLogin against the operator's own "
             "gateway; save the fresh session to a profile")
    p.add_argument("--profile", required=True,
                   help="account snapshot JSON (wizard_id, this_server_id)")
    p.add_argument("--smon-checker", default=SMON_CHECKER_PLACEHOLDER,
                   help="real 40-hex SmonChecker header (algorithm is live-only)")
    p.add_argument("--allow-placeholder-checker", action="store_true",
                   help="proceed with the placeholder SmonChecker (operator opt-in)")
    p.add_argument("--user-agent", default="", help="override the captured User-Agent")
    p.add_argument("--out", default="",
                   help="output dir for the fresh profile (default: profiles/)")
    p.set_defaults(func=cmd_live_login)

    p = sub.add_parser("time", help="print simulated clear time")
    p.add_argument("kind", choices=["dungeon", "tower"])
    p.add_argument("--record", type=int, help="best record in ms (dungeon)")
    p.add_argument("--level", type=int, default=1)
    p.add_argument("--difficulty", type=int, default=1)
    p.set_defaults(func=cmd_time)

    p = sub.add_parser("score", help="score a rune from stdin JSON")
    p.set_defaults(func=cmd_score)

    # ``proxy capture`` — own-account login MITM (optional mitmproxy extra).
    # runner.py has no heavy top-level imports, so this is safe even without
    # mitmproxy installed; mitmproxy is imported lazily inside cmd_capture.
    from ..proxy.runner import add_capture_subcommand
    add_capture_subcommand(sub)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
