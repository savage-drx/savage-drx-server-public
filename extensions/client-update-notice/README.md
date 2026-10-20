# Private client-update reminder

This is integrated into **`bin/game64.so`**, built specifically against the
current public server. It is not a custom #36/#37 module or a reference-only
packet. `bin/silverback.bin`, Python, maps, configuration and gameplay are unchanged.

After successful account authentication, the server asks that connection for
`client_version_local` using the existing `sca`/`ca` protocol. If the reported
positive version is older than the latest stable updater release, that player
receives one private console/chat reminder. There are no kicks or broadcasts.
Unknown, malformed, equal and newer versions receive no reminder. Map reloads
and re-authentication do not repeat the query; a new connection can be reminded.
The automatic reply is consumed before control-proxy routing.

The reported value is **not verified file integrity**: stale or modified client
configuration can report a different version from its installed files. This does
not use account login history and does not require a client/backend update.

## Settings

| CVar | Default | Meaning |
| --- | --- | --- |
| `sv_clientUpdateNotice` | `1` | Set to `0` to disable queries and reminders. |
| `sv_clientUpdateLatest` | `0` | Automatic stable target; a positive integer pins a target for offline operation. |

Example console commands: `sv_clientUpdateNotice 0`, or
`sv_clientUpdateLatest 833`. Use your normal server configuration mechanism if
you want an override to survive restart/map configuration reloads.

Automatic lookup is a credential-free HTTPS GET to
`https://api.savagedrx.com/updater/v2/client/version`. One independent worker
per process has a 1-second connection / 2-second total timeout and a 31-byte
response limit. TLS verification stays on; redirects are not followed. Requests
are join-triggered, coalesced and limited to one attempt per five minutes,
including failures. Successful metadata expires after fifteen minutes. No
per-player web calls, database calls or frame-loop HTTP work are introduced.
An unavailable endpoint never delays account authentication or rejects players.

No new inbound ports or firewall exceptions are needed. Outbound HTTPS/443 and
working CA certificates/DNS are needed only for automatic metadata. The same
libcurl-GnuTLS runtime is already required by the public Engine; dependency
installation is unchanged. Pinning a release avoids this optional lookup.

## Install / rollback

1. Preserve local changes and your current executable/module backups. Do not
   reset configuration, tokens or server content to repository defaults.
2. Update to the reviewed commit/branch containing this change. Stop only your
   own server using its normal supervisor when empty; do not replace a mapped
   `game/game64.so` in place while it is running.
3. Keep the existing public Engine. The supplied start scripts copy
   `bin/game64.so` into `game/game64.so` when starting. If you use a custom
   runtime/seed arrangement, update both through your normal guarded procedure.
4. Restart once, verify the expected module SHA-256 in `manifest.json`, the map,
   settings, listeners and logs. Query both new CVars in the server console.
5. Check with an old client and a current client: only the old client should see
   one private reminder. Verify map changes and reconnects with your normal
   configuration before adopting widely.

To roll back, stop that server, restore the saved **matching public baseline**
Game module in `bin/` and the runtime/seed as applicable, then start normally.
No configuration/database migration needs undoing. `sv_clientUpdateNotice 0`
can disable the feature immediately without restarting.

## Provenance and validation

The public base is `7a44482a720f101d91270552e51834c02bd62b5c`. Both binaries
exactly match builds commit `77e3001c7f5785b7f7f8d74632112e8965a1972e`, whose
CI record identifies core `51870d5d9b06edd73267fc746edc69618f540e17`.
The original Game was reproduced **byte-for-byte** with the recorded toolchain
before applying `public-core.patch`. No CoreAPI layout or Engine changes were
made. The patch preserves the original authentication implementation.

`manifest.json` pins the original/new binaries, source archive, builder image
and normalized patched-source hashes. `evidence/` distinguishes adapter tests
(mocked HTTP), real-engine loopback tests (synthetic auth, no graphical client)
and compilation. A graphical player's visible acceptance is still a separate
gate. Control-proxy placement is source-checked, not live-proxy activation proof.
The native fixture retains the public Python interpreter/stdlib, substitutes
minimal test Python hooks, disables map downloads and uses an uncompressed,
byte-preserving test copy of the stdlib ZIP because its extension modules are
absent. A test-only local-file bridge executes console checks through the
existing Python frame callback: this public Engine has no native TCP admin
responder. Neither native binary is instrumented. This does not establish full
production Python-hook integration or graphical acceptance.

## Rebuild without touching an installed server

For maintainers with access to the matching core repository:

```bash
git -C /path/to/core -c core.autocrlf=false archive --format=tar -o /absolute/input/core-51870d5.tar 51870d5d9b06edd73267fc746edc69618f540e17
mkdir -p /absolute/output/client-notice
docker run --rm --network none --cpus 2 --memory 5g \
  --mount type=bind,source=/absolute/input,target=/input,readonly \
  --mount type=bind,source=/absolute/server/extensions/client-update-notice,target=/extension,readonly \
  --mount type=bind,source=/absolute/output/client-notice,target=/output \
  igorzy/drx-builder@sha256:9b7a51451c540f2b5ea197e5d92abcf42e3b98cf8e09e94f466b8eddeb2b1079 \
  python3 /extension/build.py --source-archive /input/core-51870d5.tar --output /output
```

Pull the pinned image separately if necessary. The build runs offline, extracts
only into a temporary directory, reproduces the baseline, applies the narrow
patch, runs adapter/policy tests and verifies the candidate hash. It never
installs, deploys or restarts anything. `SOURCE_DATE_EPOCH` intentionally retains
the parent timestamp for reproducibility, so the old compiled date is not the
feature release date; use the commit/manifest/hash for identification.
