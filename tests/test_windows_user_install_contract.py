from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_user_installer_keeps_runtime_state_and_authority_separate() -> None:
    source = (ROOT / "scripts" / "install-windows-user.ps1").read_text(
        encoding="utf-8"
    )

    assert '"Programs\\GreyTheory"' in source
    assert '"GreyTheory"' in source
    assert '$venvRoot = Join-Path $installPath "runtime"' in source
    assert '$dataPath = Resolve-AbsolutePath $DataRoot' in source
    assert 'posture = "LOCAL_FIXTURE"' in source
    assert 'live_target_available = $false' in source
    assert "WScript.Shell" in source
    assert "runas" not in source.lower()


def test_user_launcher_opens_only_after_local_only_health() -> None:
    source = (ROOT / "scripts" / "install-windows-user.ps1").read_text(
        encoding="utf-8"
    )

    health_check = source.index('$health.posture -eq "LOCAL_FIXTURE"')
    browser_open = source.index("Start-Process `$WorkbenchUrl")
    assert health_check < browser_open
    assert '$health.live_target_available -eq `$false' in source
    assert '"http://127.0.0.1:$Port/healthz"' in source


def test_lifecycle_harness_proves_persistence_without_overclaiming_user_scope() -> None:
    source = (ROOT / "acceptance" / "run-windows-user-install.ps1").read_text(
        encoding="utf-8"
    )

    assert 'kind = "start_learning_journey"' in source
    assert 'persisted_journey_restart = $true' in source
    assert 'persisted_journey_upgrade = $true' in source
    assert 'persisted_journey_recovery = $true' in source
    assert 'separate_user_accepted = $false' in source
    assert 'signed_installer = $false' in source
    assert "Stop-AcceptanceWorkbench" in source
