from django.db import models
from django.utils import timezone
from tinymce.models import HTMLField

class BlogCategory(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Blog Category"
        verbose_name_plural = "Blog Categories"


class Blog(models.Model):
    title = models.CharField(max_length=100)
    category = models.ForeignKey(BlogCategory, on_delete=models.CASCADE, blank=True, null=True)
    description = HTMLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = "Blog"
        verbose_name_plural = "Blogs"

STATUS_CHOICES = [
    ('PENDING', 'Beklemede'),
    ('RUNNING', 'Çalışıyor'),
    ('COMPLETED', 'Tamamlandı'),
    ('FAILED', 'Başarısız'),
    ('CANCELLED', 'İptal Edildi'),
]

RISK_CHOICES = [
    ('HIGH', 'Yüksek'),
    ('MEDIUM', 'Orta'),
    ('LOW', 'Düşük'),
    ('INFO', 'Bilgilendirme'),
]


class Scan(models.Model):
    target_url = models.URLField(
        verbose_name="Hedef URL",
        max_length=500
    )
    status = models.CharField(
        verbose_name="Tarama Durumu",
        max_length=10,
        choices=STATUS_CHOICES,
        default='PENDING'
    )    
    zap_scan_id = models.IntegerField(
        verbose_name="ZAP Aktif Tarama ID",
        null=True, 
        blank=True,
        help_text="ZAP API'den dönen ID. Tarama ilerlemesini izlemek için kullanılır."
    )
    
    scan_type = models.CharField(
        verbose_name="Tarama Tipi",
        max_length=10,
        choices=[('ACTIVE', 'Aktif Tarama'), ('API', 'API Tarama')],
        default='ACTIVE'
    )
    
    start_time = models.DateTimeField(
        verbose_name="Başlangıç Zamanı",
        default=timezone.now
    )
    
    end_time = models.DateTimeField(
        verbose_name="Bitiş Zamanı",
        null=True, 
        blank=True
    )

    class Meta:
        verbose_name = "Tarama İşi"
        verbose_name_plural = "Tarama İşleri"
        ordering = ['-start_time']

    def __str__(self):
        return f"{self.target_url} - {self.status}"

class Alert(models.Model):
    scan_job = models.ForeignKey(
        Scan, 
        on_delete=models.CASCADE, 
        related_name='alerts',
        verbose_name="Tarama İşi"
    )
    risk_level = models.CharField(
        verbose_name="Risk Seviyesi",
        max_length=10,
        choices=RISK_CHOICES
    )
    alert_name = models.CharField(
        verbose_name="Açığın Adı",
        max_length=255
    )
    confidence = models.CharField(
        verbose_name="Güvenilirlik",
        max_length=50,
    )
    
    description = models.TextField(verbose_name="Açıklama", null=True, blank=True)
    solution = models.TextField(verbose_name="Çözüm Önerisi", null=True, blank=True)
    reference = models.TextField(verbose_name="Referanslar", null=True, blank=True)
    url = models.URLField(verbose_name="Bulgu URL'si", max_length=500)
    param = models.CharField(verbose_name="Parametre", max_length=255, null=True, blank=True)
    evidence = models.TextField(verbose_name="Kanıt", null=True, blank=True)
    
    # CWE/WASC bilgileri
    cwe_id = models.IntegerField(verbose_name="CWE ID", null=True, blank=True)
    wasc_id = models.IntegerField(verbose_name="WASC ID", null=True, blank=True)

    class Meta:
        verbose_name = "Güvenlik acigi (Alert)"
        verbose_name_plural = "Güvenlik Açıkları (Alerts)"
        # Yüksek riskli olanları başta sıralamak için
        ordering = ['risk_level', '-id'] 

    def __str__(self):
        return f"{self.alert_name} ({self.get_risk_level_display()})"