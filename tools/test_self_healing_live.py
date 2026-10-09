"""
J.A.R.V.I.S. Live Self-Healing Daemon & Process Resilience Verification Harness.
Performs end-to-end live testing across daemon supervision, memory pruning,
port resilience, composite health scoring, and voice directives.
"""

import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from core.self_repair import SelfRepairEngine, self_repair_engine
from core.local_intelligence import local_intelligence


def run_live_self_healing_diagnostic():
    print("=" * 65)
    print("J.A.R.V.I.S. SELF-HEALING DAEMON & PROCESS RESILIENCE LIVE VERIFICATION")
    print("=" * 65)

    # 1. Daemon Supervision & Resuscitation
    print("\n[1/6] Auditing Supervised Daemon Matrix...")
    supervisor_res = self_repair_engine.supervise_daemons()
    statuses = supervisor_res.get("statuses", {})
    revived = supervisor_res.get("revived", [])
    print(f"  -> Total Supervised Daemons: {len(statuses)}")
    for k, d in statuses.items():
        state = "ONLINE" if d["alive"] else "OFFLINE"
        print(f"     * {d['name']:<24}: {state} (Restarts: {d['restarts_total']}, Tripped: {d['circuit_breaker']})")
    if revived:
        print(f"  -> Autonomously Revived      : {', '.join(revived)}")
    assert len(statuses) >= 4, "Must supervise at least 4 core daemons"

    # 2. Memory & Resource Leak Pruning
    print("\n[2/6] Executing Memory Leak Pruning & Working Set Compaction...")
    prune_res = self_repair_engine.prune_memory_and_resources(force=True)
    print(f"  -> RSS Before   : {prune_res['rss_before_mb']} MB")
    print(f"  -> RSS After    : {prune_res['rss_after_mb']} MB")
    print(f"  -> Freed Memory : {prune_res['freed_mb']} MB")
    print(f"  -> System RAM   : {prune_res['system_ram_pct']}%")
    print(f"  -> Files Pruned : {prune_res['files_removed']}")
    assert prune_res["pruned"], "Memory pruning routine must report successful execution"

    # 3. Port & Socket Verification
    print("\n[3/6] Probing Local Service Ports...")
    port_audit = self_repair_engine.verify_and_repair_ports()
    for port, info in port_audit.items():
        print(f"  -> Port {port:<6} Listening: {info['listening']}")
    assert len(port_audit) >= 1, "Must audit local service ports"

    # 4. Composite System Resilience Index
    print("\n[4/6] Computing Composite Resilience & Health Telemetry...")
    telemetry = self_repair_engine.get_system_health_telemetry()
    score = telemetry["health_score"]
    status = telemetry["status"]
    print(f"  -> Composite Health Score : {score}%")
    print(f"  -> Operational Status     : {status}")
    print(f"  -> Active Daemons         : {telemetry['daemons_alive']} / {telemetry['daemons_total']}")
    print(f"  -> Database Intact        : {telemetry['database_intact']}")
    print(f"  -> Internet Connected     : {telemetry['internet_connected']}")
    assert 0 <= score <= 100, "Health score must be between 0 and 100"

    # 5. British Butler Spoken Summary
    print("\n[5/6] Generating Articulate Butler Speech Telemetry...")
    voice_summary = self_repair_engine.get_health_voice_summary()
    print(f"  -> J.A.R.V.I.S.: \"{voice_summary}\"")
    assert "sir" in voice_summary.lower(), "Spoken summary must maintain respectful British Butler persona"
    assert "health score" in voice_summary.lower(), "Spoken summary must report health score"

    # 6. Local Intelligence Directive Dispatch
    print("\n[6/6] Verifying Voice Directive Integration...")
    directives = ["system health", "run self healing"]
    for d in directives:
        handled, resp = local_intelligence.evaluate_and_execute(d)
        assert handled, f"Directive '{d}' was not handled by local intelligence"
        print(f"  [Directive: '{d}'] Handled: {handled}")
        print(f"  -> Response: \"{resp[:90]}...\"")

    print("\n" + "=" * 65)
    print("ALL 6 LIVE SELF-HEALING VERIFICATIONS PASSED WITH 100% SUCCESS")
    print("=" * 65)
    return True


if __name__ == "__main__":
    success = run_live_self_healing_diagnostic()
    sys.exit(0 if success else 1)
