# dfx command reference (captured)

Offline snapshot of **dfx 0.31.0** help text and safe command output for this project.

Each command has a folder with `response.txt`:

```
docs/dfx/<command-path>/response.txt
```

Example: `docs/dfx/canister/create/response.txt` → `dfx canister create --help`

## File format

```text
# dfx <command> --help
# Generated: <timestamp>
# dfx: dfx 0.31.0

=== SUPPORT (--help) ===
... full --help output ...

=== RESPONSE (safe run) ===   ← only when a read-only run was possible
... actual command output ...
```

## Top-level commands

| Command | Path |
|---------|------|
| Root / version | [`_root/response.txt`](_root/response.txt) |
| build | [`build/response.txt`](build/response.txt) |
| cache | [`cache/response.txt`](cache/response.txt) |
| canister | [`canister/response.txt`](canister/response.txt) |
| config | [`config/response.txt`](config/response.txt) |
| completion | [`completion/response.txt`](completion/response.txt) |
| cycles | [`cycles/response.txt`](cycles/response.txt) |
| deploy | [`deploy/response.txt`](deploy/response.txt) |
| deps | [`deps/response.txt`](deps/response.txt) |
| diagnose | [`diagnose/response.txt`](diagnose/response.txt) |
| extension | [`extension/response.txt`](extension/response.txt) |
| fix | [`fix/response.txt`](fix/response.txt) |
| generate | [`generate/response.txt`](generate/response.txt) |
| identity | [`identity/response.txt`](identity/response.txt) |
| info | [`info/response.txt`](info/response.txt) |
| killall | [`killall/response.txt`](killall/response.txt) |
| ledger | [`ledger/response.txt`](ledger/response.txt) |
| new | [`new/response.txt`](new/response.txt) |
| ping | [`ping/response.txt`](ping/response.txt) |
| quickstart | [`quickstart/response.txt`](quickstart/response.txt) |
| remote | [`remote/response.txt`](remote/response.txt) |
| schema | [`schema/response.txt`](schema/response.txt) |
| start | [`start/response.txt`](start/response.txt) |
| stop | [`stop/response.txt`](stop/response.txt) |
| wallet | [`wallet/response.txt`](wallet/response.txt) |

**119** command paths captured (including all subcommands).

## Regenerate

From the repo root:

```bash
./docs/dfx/capture-dfx-commands.sh
```

Requires `dfx` on `PATH`. Destructive commands (deploy, delete, etc.) only record `--help`; read-only commands also include a live **RESPONSE** section where safe.
