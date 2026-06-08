"""Contract testleri üçin her list endpointde azyndan bir setir bolar ýaly fixture maglumat."""
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.core.models import AuditLog, SystemSetting
from apps.scans.models import Scan, ScanSchedule, Vulnerability, ZapConfiguration
from apps.targets.models import Target
from apps.users.models import APIKey

User = get_user_model()

admin = User.objects.get(email="admin@guardly.com")
user = User.objects.get(email="user@guardly.com")

# Target (user-iň)
target, _ = Target.objects.get_or_create(
    url="https://contract-test.example.com",
    defaults={"owner": user, "verification_token": "x" * 32},
)

# Scan
scan, _ = Scan.objects.get_or_create(
    owner=user, target=target, scan_type=Scan.ScanType.PASSIVE,
    defaults={"status": Scan.Status.COMPLETED, "completed_at": timezone.now()},
)

# Vulnerability
Vulnerability.objects.get_or_create(
    scan=scan, target=target, owner=user, name="Reflected XSS",
    defaults={
        "severity": Vulnerability.Severity.HIGH,
        "owasp_category": "A03:2021 - Injection",
        "url": "https://contract-test.example.com/search",
    },
)

# Schedule
ScanSchedule.objects.get_or_create(
    owner=user, target=target,
    defaults={
        "scan_type": Scan.ScanType.PASSIVE,
        "frequency": ScanSchedule.Frequency.DAILY,
        "next_run_at": timezone.now(),
    },
)

# ZAP config
ZapConfiguration.objects.get_or_create(owner=user, defaults={"api_url": "http://localhost:8090"})

# API key (user-iň)
if not APIKey.objects.filter(user=user).exists():
    APIKey.objects.create(user=user, name="contract-test-key")

# System setting
SystemSetting.objects.get_or_create(key="contract_test_flag", defaults={"value": "1", "description": "test"})

# Audit log
AuditLog.objects.get_or_create(
    action="contract_test", entity_type="target", entity_id=target.id,
    defaults={"actor": admin, "metadata": {"seed": True}},
)

print("Fixtures ensured: target/scan/vuln/schedule/zap/apikey/setting/auditlog")
