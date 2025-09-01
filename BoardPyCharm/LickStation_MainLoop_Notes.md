# Lick Station — Main Loop Logic

> Short notes so Future Me can remember how this works.

---

## Purpose

Count licks **per cat**, using the RFID reader as a **presence gate** (who’s here + whether to count).

---

## Tunable knobs (top of file)

- `TAG_REQUIRED = True`
  - **Gatekeeper mode**: only count when a cat is present (RFID gate ON).
  - Set `False` for **Logger mode**: always count; attribute to current cat or `"unknown"`.
- `ALLOW_UNKNOWN = False`
  - Unknown tags are ignored in gatekeeper mode. (If logger mode, they can map to `"unknown"`.)
- `HOLD_MS = 3000`
  - Presence stays ON for this long after the **last RFID hit**.
- `LOCK_RELEASE_MS = 2000`
  - Require this much **quiet** before switching from Cat A to Cat B (lock-to-first).

**Presence gate formula**
```py
gate_on = (active_tag is not None) and ((t_ms - last_seen_ms) <= HOLD_MS)
```

---

## Initialization

- Logging → `system.log` (level `INFO`).
- Hardware/objects:
  - `TagReader()` — non-blocking; self-schedules resets internally; `poll()` never sleeps.
  - `HydraPurr()` — lick sensor + small UI helpers.
  - `MyPixel()` — status LED.
- Counters: `lickcounters = { name: LickCounter(name=name) }` for all cats (and `"unknown"` in logger mode).
- Presence state: `active_tag`, `active_name`, `last_seen_ms` (all start empty/zero).
- UI heartbeat: pixel color cycles every **500 ms** (`pixel.cycle()` + `hydrapurr.indicator_toggle()`).

---

## Main loop: high-level flow

1. **Tick time** `t_ms = now_ms()`.
2. **Heartbeat UI** every 500 ms.
3. **RFID poll (non-blocking)**:
   - `pkt = reader.poll()` → `None` or `{ "tag_key": ... }`.
   - If a tag arrives:
     - Map tag → `name = Cats.get_name(tag)`.
     - If unknown and `ALLOW_UNKNOWN` is `False` → ignore.
     - Else update presence with **lock-to-first**:
       - If no `active_tag`: **activate** this tag/name; `last_seen_ms = t_ms`.
       - If same tag: **refresh** `last_seen_ms`.
       - If different tag:
         - If `(t_ms - last_seen_ms) >= LOCK_RELEASE_MS`: **switch** to the new cat.
         - Else: **ignore** (conflict during lock window).
4. **Compute gate**:
   - `gate_on = (active_tag is not None) and ((t_ms - last_seen_ms) <= HOLD_MS)`.
5. **Presence expired?** (`active_tag` exists but `gate_on` is `False`)
   - In gatekeeper mode: send a `0` sample to the last active cat’s counter to **close** any ongoing lick.
   - Log **Deactivating** and update the OLED once (avoid mid-bout screen churn):
     - Line 0 → cat name.
     - Line 1 → bout count (`ctr.bout_count`).
   - Clear `active_tag/active_name`.
6. **Read lick sensor**: `lick_state = 1/0` from `hydrapurr.read_lick(binary=True)`.
7. **Route the sample**:
   - **Gatekeeper (TAG_REQUIRED = True)**:
     - If `gate_on` and `active_name` exists:
       - `lickcounters[active_name].process_sample(lick_state)`
       - If state changed: log `current counter state`.
     - Else: do nothing (keeps per-cat counters quiet).
   - **Logger (TAG_REQUIRED = False)**:
     - Choose `name = active_name if gate_on else "unknown"`.
     - Ensure a counter exists for `name`, then `process_sample(lick_state)`.
     - If state changed: log it.

---

## Data flow (one pass)

RFID packet → update `{active_tag, active_name, last_seen_ms}`  
↓  
Compute `gate_on` from `HOLD_MS` and last seen time  
↓  
Lick sample (`0/1`) → **if** gatekeeper & `gate_on`: route to `lickcounters[active_name]`  
↓  
Log counter state changes; on presence end, flush (send `0`) and update OLED.

---

## Behavior details

- **Lock-to-first** prevents flapping if two cats crowd the antenna; switching requires `LOCK_RELEASE_MS` of quiet.
- **Hold window** bridges the RFID’s ~2–3 Hz cadence; licks between RFID hits still count.
- **OLED update on deactivation** avoids frequent screen writes during active licking.
- **Status LED** pulses every 500 ms so we know the loop is alive.

---

## Pseudocode snapshot

```py
loop:
  t_ms = now()

  # heartbeat (500 ms)
  if t_ms - last_toggle > 500:
      pixel.cycle()
      hydrapurr.indicator_toggle()
      last_toggle = t_ms

  # RFID
  pkt = reader.poll()
  if pkt:
      tag = pkt["tag_key"]
      name = Cats.get_name(tag)
      if name or ALLOW_UNKNOWN:
          if active_tag is None:
              active_tag, active_name = tag, name
              last_seen_ms = t_ms
          elif tag == active_tag:
              last_seen_ms = t_ms
          elif t_ms - last_seen_ms >= LOCK_RELEASE_MS:
              active_tag, active_name = tag, name
              last_seen_ms = t_ms

  gate_on = (active_tag is not None) and (t_ms - last_seen_ms <= HOLD_MS)

  if active_tag and not gate_on:
      if TAG_REQUIRED and active_name:
          lickcounters[active_name].process_sample(0)  # close bout
      # update OLED at end of session
      ctr = lickcounters.get(active_name) if active_name else None
      if ctr:
          hydrapurr.write_line(0, f"{active_name}")
          hydrapurr.write_line(1, f"B:{ctr.bout_count}")
      active_tag = active_name = None

  # licks
  lick = 1 if hydrapurr.read_lick(binary=True) else 0

  if TAG_REQUIRED:
      if gate_on and active_name:
          ctr = lickcounters.get(active_name)
          if ctr:
              ctr.process_sample(lick)
              st = ctr.get_state()
              if st != previous_ctr_state:
                  info(f"state {st}")
                  previous_ctr_state = st
  else:
      name = active_name if gate_on and active_name else "unknown"
      ctr = lickcounters.setdefault(name, LickCounter(name=name))
      ctr.process_sample(lick)
      st = ctr.get_state()
      if st != previous_ctr_state:
          info(f"state {st}")
          previous_ctr_state = st
```

---

## Notes & gotchas

- In the deactivation block, make sure `ctr` is fetched before using `ctr.bout_count`:
  ```py
  ctr = lickcounters.get(active_name) if active_name else None
  if ctr:
      hydrapurr.write_line(0, f"{active_name}")
      hydrapurr.write_line(1, f"B:{ctr.bout_count}")
  ```
- If you switch to **Logger mode**, ensure the `"unknown"` counter exists (the main code does this with `setdefault` when routing).
- `TagReader.poll()` is non-blocking and includes its own reset cadence; calling it each loop won’t stall lick sampling.
