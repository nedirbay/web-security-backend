from django.utils import timezone
from .models import Blog, BlogCategory, Scan, Alert
from .filtrs import BlogFilter
from rest_framework.views import APIView
from .serializer import BlogSerializer, BlogCategorySerializer
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from zapv2 import ZAPv2
import time
from googletrans import Translator
from django.contrib.auth import authenticate, login
from rest_framework.pagination import PageNumberPagination

# get all blogcategories
@api_view(['GET'])
def blogcategory_list(request): 
    blogcategories = BlogCategory.objects.all()
    serializer = BlogCategorySerializer(blogcategories, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def blog_list(request): 
    blogs = Blog.objects.all()
    filter_set = BlogFilter(request.GET, queryset=blogs)
    filtered_qs = filter_set.qs
    paginator = PageNumberPagination()
    paginator.page_size = 10
    page = paginator.paginate_queryset(filtered_qs, request) 
    serializer = BlogSerializer(page, many=True)
    return paginator.get_paginated_response(serializer.data)

# get blog detail
@api_view(['GET'])
def blog_detail(request, pk):
    blog = Blog.objects.get(pk=pk)
    serializer = BlogSerializer(blog)
    return Response(serializer.data)


ZAP_API_KEY = 'u3a642dp7nchdoi6vqotikufs'  
ZAP_PROXY_HOST = '127.0.0.1'
ZAP_PROXY_PORT = '8080'

# check is admin user
@api_view(['POST'])
def adminLogin(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(username=username, password=password)
    if user is not None:
        if user.is_superuser:
            login(request, user)
            return Response({'message': 'Login successful', 'user': user.username}, status=status.HTTP_200_OK)
        else:
            return Response({'message': 'You are not authorized to login'}, status=status.HTTP_401_UNAUTHORIZED)
    else:
        return Response({'message': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

class OWASPScanView(APIView):
    """
    URL-i kabul edýär, diňe Spider işleýär (Active Scan wagtlaýyn öçürilen).
    Netijede Passive Scan (Passiw howpsuzlyk barlagy) netijelerini gaýtarýar.
    """
    
    def post(self, request):
        target_url = request.data.get('url')

        if not target_url:
            return Response({"error": "URL hökman girizilmeli"}, status=status.HTTP_400_BAD_REQUEST)

        # Scan kaydı oluştur
        scan_obj = Scan.objects.create(
            target_url=target_url,
            status='RUNNING'
        )

        # 1. ZAP-a baglanmak
        zap = ZAPv2(apikey=ZAP_API_KEY, proxies={
            'http': f'http://{ZAP_PROXY_HOST}:{ZAP_PROXY_PORT}',
            'https': f'http://{ZAP_PROXY_HOST}:{ZAP_PROXY_PORT}'
        })

        try:
            # 2. Skanirlemezden öň URL-e bir gezek ýüzlenmek (Access target)
            zap.urlopen(target_url)
            
            # ----------------------------------------------------
            # 3. SPIDER (Örümçi) - Sahypalary tapmak
            # ----------------------------------------------------
            print(f"Spider başladylýar: {target_url}")
            scan_id = zap.spider.scan(target_url)
            
            # Spider gutarýança garaşmak
            while int(zap.spider.status(scan_id)) < 100:
                print(f"Spider progress: {zap.spider.status(scan_id)}%")
                time.sleep(1) # Gysga wagt garaşmak ýeterlik
            print("Spider tamamlandy.")

            # ----------------------------------------------------
            # 4. ACTIVE SCAN (Aktiw Skanirleme) - WAGTLAÝYN ÖÇÜRILEN
            # ----------------------------------------------------
            # Geljekde ulanmak üçin saklanylýar:
            """
            print(f"Active Scan başladylýar: {target_url}")
            scan_id = zap.ascan.scan(target_url)
            
            while int(zap.ascan.status(scan_id)) < 100:
                print(f"Active Scan progress: {zap.ascan.status(scan_id)}%")
                time.sleep(5)
            print("Active Scan tamamlandy.")
            """

            # ----------------------------------------------------
            # 5. NETIJELERI ALMAK (Alerts)
            # ----------------------------------------------------
            # Active scan bolmasa-da, Passive scan (trafigi diňlemek) 
            # arkaly tapylan ýalňyşlyklar (headers, cookies we ş.m.) çykar.
            alerts = zap.core.alerts(baseurl=target_url)
            translator = Translator()

            formatted_alerts = []
            
            risk_mapping = {
                'High': 'HIGH',
                'Medium': 'MEDIUM',
                'Low': 'LOW',
                'Informational': 'INFO'
            }

            for alert in alerts:
                try:
                    # Esasy sözbaşyny terjime etmek
                    translated_alert = translator.translate(alert.get('alert'), dest='tk').text
                    translated_desc = translator.translate(alert.get('description'), dest='tk').text
                    translated_sol = translator.translate(alert.get('solution'), dest='tk').text
                except:
                    # Eger internet ýok bolsa ýa-da hatalyk bolsa, originalyny goý
                    translated_alert = alert.get('alert')
                    translated_desc = alert.get('description')
                    translated_sol = alert.get('solution')

                # Alert kaydı oluştur
                Alert.objects.create(
                    scan_job=scan_obj,
                    risk_level=risk_mapping.get(alert.get('risk'), 'INFO'),
                    alert_name=translated_alert,
                    confidence=alert.get('confidence'),
                    description=translated_desc,
                    solution=translated_sol,
                    reference=alert.get('reference'),
                    url=alert.get('url'),
                    param=alert.get('param'),
                    evidence=alert.get('evidence'),
                    cwe_id=int(alert.get('cweid')) if alert.get('cweid') and str(alert.get('cweid')).isdigit() else None,
                    wasc_id=int(alert.get('wascid')) if alert.get('wascid') and str(alert.get('wascid')).isdigit() else None
                )

                formatted_alerts.append({
                    "alert": translated_alert,
                    "risk": alert.get('risk'), # Risk derejesi (Low/High) şeýle galany gowy
                    "confidence": alert.get('confidence'),
                    "url": alert.get('url'),
                    "description": translated_desc,
                    "solution": translated_sol
                })
            
            # Scan tamamlandı
            scan_obj.status = 'COMPLETED'
            scan_obj.end_time = timezone.now()
            scan_obj.save()

            return Response({
                "message": "Skanirleme (Spider & Passive) üstünlikli tamamlandy",
                "target": target_url,
                "total_alerts": len(formatted_alerts),
                "alerts": formatted_alerts
            }, status=status.HTTP_200_OK)

        except Exception as e:
            # Hata durumunda
            scan_obj.status = 'FAILED'
            scan_obj.end_time = timezone.now()
            scan_obj.save()
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class OWASPScanListView(APIView):
    def get(self, request):
        scans = Scan.objects.all()
        return Response({"scans": list(scans.values())})

# get scan Alerts 
class OWASPScanAlertsView(APIView):
    def get(self, request, scan_id):
        scan = Scan.objects.get(id=scan_id)
        alerts = Alert.objects.filter(scan_job=scan)
        return Response({"alerts": list(alerts.values())})