# Hyundai HRS-PRO250 / Reventon-HOLTOP Smart ERV: Tuya Local investigation

## Scope

This is a **work-in-progress** investigation based on an HRS-PRO250 heat-recovery
ventilation unit with Tuya product ID `ddrpa4plk6fsvz9l`, also found in the
existing `reventon_holtop_smart_erv.yaml` device profile. A matching product ID
is evidence that the profile may be suitable; it does not prove that every
measurement is physically available on all variants.

The goal is to expose the maximum **verified** set of Tuya Local status values
while preserving factory controls. Do not assume that points available on the
wired controller or the Modbus interface are transmitted by the Wi-Fi module.

## Observed local status

Tuya Local has successfully connected via Tuya protocol 3.4. The table below
is based on local DPS received in Home Assistant logs on 2026-11-23 and
2026-11-24, not on a complete manufacturer data model.

| DP | Observed payload type | Existing Tuya Local meaning | Caveat |
| --- | --- | --- | --- |
| 101 | boolean | ventilation power | Control point; avoid automatic testing |
| 102 | string (`"0"`–`"9"`) | supply fan *set* speed | Raw level, not measured RPM or airflow |
| 103 | string (`"0"`–`"9"`) | exhaust fan *set* speed | Raw level, not measured RPM or airflow |
| 106 | integer | supply air **target** temperature | Setpoint, not SA measurement |
| 107 | integer | bypass base temperature setting | Not a bypass open/closed sensor |
| 108 | integer | bypass temperature delta setting | Not a bypass open/closed sensor |
| 109 | string | configured filter interval | Distinct from remaining life |
| 111 | integer | CO2 | Repeated 0 ppm; optional hardware unconfirmed |
| 112 | string | air quality level | `"0"` maps to unknown |
| 113 | integer | humidity | Repeated 100%; sensor presence unconfirmed |
| 114 | integer | PM2.5 | Repeated 0; optional hardware unconfirmed |
| 117 | integer | Indoor temperature (profile label) | Physical probe location not validated |
| 118 | integer | Outdoor temperature (profile label) | Observed 4–6°C and one transient 31°C |
| 119 | integer (bitfield) | fault indicator / raw code | 0 indicates no reported fault |
| 122 | boolean | defrost active | Verified reported boolean, not controller-side tested |
| 123 | boolean | filter clean due | Verified reported boolean |
| 125 | boolean | speed mode selector | true selects 9-step mapping in current profile |
| 126 | integer | remaining filter life | Reported in days |

The existing profile additionally defines DPs 104 and 105 for 3-step mode
and DP 110 for a filter reset button. These did **not** appear in the
captured local status payload. Their absence is not proof of lack of support.

### Initial additions on this development branch

The branch adds four **read-only diagnostic entities**, without modifying
the existing fan, setpoint, switch or reset-button behavior:

- Raw supply fan speed level (DP 102).
- Raw exhaust fan speed level (DP 103).
- Nine-step fan speed mode flag (DP 125).
- Raw device fault code (DP 119).

Existing fan entities convert the level to a percentage; raw entities allow
direct comparison with the wired controller. These are intentionally classified
as diagnostic entities rather than additional writable controls.

## Open validation work

1. Compare controller readings RA/OA/SA/EA (or FR) against DP 117 and DP 118
   at the same instant; do not rename either DP without confirmation.
2. Check whether additional status DP keys appear after ordinary mode
   transitions, using **read-only** logging and redacted diagnostics.
3. Verify that the raw fan speed levels and nine-step flag match controller
   settings. Do not conflate commanded level with measured motor RPM.
4. Determine whether the 0 ppm CO2, 0 PM2.5, and 100% humidity represent
   installed sensors, unsupported optional modules or device defaults.
5. Verify filter remaining life and fault code semantics on the controller.
6. Test the integration with the updated YAML and review the GitHub Actions
   validation results. Do not publish an upstream PR before hardware validation.

## Safety and privacy

- **No automatic write tests** against a live ventilation unit.
- Do not press the filter reset button or change bypass/defrost controls while
  validating measurement mappings.
- Redact `local_key`, cloud credentials, login QR codes, IDs and private
  networking details before publishing diagnostics.
- A stock HACS update can overwrite local Python hotfixes. The upstream
  `fan.py` generator-length bug was fixed on the author's `main` branch
  after the `2026.11.0` release (commit `6e78b77`); it is not a new
  Hyundai-specific change in this branch.

## References

- Device profile: `custom_components/tuya_local/devices/reventon_holtop_smart_erv.yaml`
- Vendor and status investigation in the user's Home Assistant instance
  (logs and device UI; no private diagnostic files committed)
- Upstream fix for fan entity construction:
  https://github.com/make-all/tuya-local/commit/6e78b77e2726
- Upstream project: https://github.com/make-all/tuya-local

## Hardware validation — 2026-11-24

A Hyundai HRS-PRO250 running the development branch's updated
`reventon_holtop_smart_erv.yaml` was restarted in Home Assistant and four
new diagnostic entities were confirmed visible with valid current values:

| Diagnostic entity | DP | Observed value | Interpretation |
| --- | --- | --- | --- |
| Supply fan speed level (raw) | 102 | `"9"` | Reported 9-step supply setting |
| Exhaust fan speed level (raw) | 103 | `"9"` | Reported 9-step exhaust setting |
| Nine-step fan speed mode | 125 | `true` | Nine-step mode enabled |
| Fault code (raw) | 119 | `0` | No fault reported |

Other visible values in the same Home Assistant screenshots:
DP 117 = 16°C, DP 118 = 10°C, DP 113 = 99%, DP 111 = 0 ppm,
DP 114 = 0 µg/m³, DP 106 setpoint = 23°C, DP 126 = 28 days.
These are observations only; physical temperature probe mapping and
optional air-quality sensor availability remain unverified.

All four diagnostics were confirmed present and updating after the HA Core
restart. The screenshots do **not** verify the write path or prove that
the reported fan levels represent measured RPM or airflow. They also show
activity history entries for ventilation toggles and target-temperature
changes, which should not be attributed to this read-only profile addition
without separate evidence.

GitHub Actions validation: YAML workflow 45362240735 (3611 passed);
Python workflow 45362824316 (4013 passed, 2 warnings).

## Proposed separate speed sliders (awaiting hardware test)

The Home Assistant device view currently shows the exhaust fan's percentage
slider, but primarily an on/off switch for the ventilation (supply) entity.
Both DPs `102` and `103` are distinct writable speed settings in the existing
fan profile, so the development branch adds two **Number** entities:

- `Supply fan speed (0-9)`: DP 102, Tuya string levels `"0"` through `"9"`
- `Exhaust fan speed (0-9)`: DP 103, Tuya string levels `"0"` through `"9"`

These complement rather than replace the existing fan and power entities.
They expose *discrete settings* rather than approximate percentages, and
accept only integer steps from 0 through 9. A separate DP 125 availability
flag hides them whenever the device is not in nine-step mode.

**IMPORTANT:** The live write behavior, especially setting either fan to
`0`, is **not verified**. A zero setting could stop one airflow independently;
do not test it until device safety is assessed. The changes are committed
to GitHub, not installed in the user's running Home Assistant instance.
The controls write the existing DP directly; their presence does not create
a new safety interlock or guarantee simultaneous fan operation.

Regression tests validate the conversion of HA level `7` to Tuya payload
`"7"` and confirm that both controls are unavailable in three-step mode.

## Live Tuya debug analysis — 2026-11-24, 10:44–10:50 Europe/Warsaw

A six-minute locally exported Tuya Local debug log was analyzed without
committing the raw log, device ID, IP addresses, tokens or encrypted frames.

**Independent supply and exhaust updates were directly observed:**

| Time | DP 102 supply | DP 103 exhaust | Observation |
| --- | --- | --- | --- |
| 10:44:58 | `"9"` | `"9"` | full poll |
| 10:49:25 | `"4"` | `"9"` | supply DP changed |
| 10:49:42 | `"4"` | `"4"` | exhaust DP changed |
| 10:49:51 | `"4"` | `"7"` | exhaust DP changed |
| 10:50:01 | `"4"` | `"9"` | exhaust DP changed |
| 10:50:06 | `"9"` | `"9"` | supply DP changed |

The log shows **incoming** device state and does not by itself attribute
these changes to HA, a Tuya app, or the physical panel. It supports
independent reported setpoints, **not** measured independent airflow.

**DP 118 temperature-like reading:** fell progressively from 30°C
(10:44:58) to 7°C (10:49:56–10:50:15). Interim observations were
29, 28, 26, 24, 22, 21, 19, 17, 15, 14, 13, 12, 11, 10, 9, 8°C.
DP 117 remained 16°C. This is a coherent changing raw value,
not a single GUI rendering glitch. A probe warming during
non-ventilation and cooling during airflow is a *hypothesis only*;
the physical locations of DP 117 and DP 118 are not yet verified.

**Other live updates:** DP 106 23 → 20 → 23°C;
DP 113 humidity repeatedly 99 ↔ 100%;
DP 101 true → false at 10:50:16, then true at 10:50:19.
No new DP IDs appeared: the set of reported DPs remained the 18
previously documented. DP 119 remained 0 in full polls.
No Tuya Local integration exception was observed in this captured
debugging interval. Scanner debug mentioned `devices.json` absence,
which is not evidence of Tuya Local communication failure.

**Next validation:** compare the temperatures at the wired controller
during settled operation; review diagnostic state after speed changes,
avoid setting any individual fan to 0; validate new Number sliders
through GitHub Actions and then, with a backup, in Home Assistant.

## Independent slider CI validation

As of the `43331780` YAML profile revision, the project CI reports:

- YAML tests: success — workflow
  https://github.com/BudrysLP/tuya-local/actions/runs/45368677011
- Lint: success — workflow
  https://github.com/BudrysLP/tuya-local/actions/runs/45368676777
- Python tests (including both slider value-to-string write-path tests):
  **4015 passed, 2 warnings** — workflow
  https://github.com/BudrysLP/tuya-local/actions/runs/45368557000

These CI results validate static mapping and mocked writes, not physical
fan speeds or safety behavior. Do not issue zero-level write tests until
verified safe.

## Confirmed writable exhaust fan setting — 2026-11-24

During testing of the two new 0–9 Home Assistant sliders, the user set
`Exhaust fan speed (0-9)` to **6** while the supply setting remained **9**.
The existing percentage-based `Exhaust fan` slider moved together with
the new exhaust slider because **both control DP 103**; this is expected,
not cross-coupling with the supply fan DP 102.

**Hardware confirmation:** the user checked the physical Hyundai controller
and confirmed it also displayed exhaust level **6** after changing the
Home Assistant slider. This validates the DP 103 write path at level 6.
It does **not** yet prove the DP 102 write path from the new Number entity,
nor safe behavior for level 0.

Recommendation: preserve the existing upstream fan entity for compatibility.
For a simplified user dashboard, hide or disable the redundant legacy
`Exhaust fan` entity in Home Assistant's entity settings, rather than
remove it from the device profile. The user-facing controls should be:
ventilation power (DP 101), supply speed 0–9 (DP 102), and exhaust speed
0–9 (DP 103).
