from django.shortcuts import render
from django_filters.views import FilterView
from .models import Blog, BlogCategory
from .filtrs import BlogFilter
from rest_framework.views import APIView
from .serializer import BlogSerializer, BlogCategorySerializer
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from zapv2 import ZAPv2
import time
# get all blogcategories

@api_view(['GET'])
def blogcategory_list(request): 
    blogcategories = BlogCategory.objects.all()
    serializer = BlogCategorySerializer(blogcategories, many=True)
    return Response(serializer.data)

# get all blogs with filter
@api_view(['GET'])
def blog_list(request):
    blogs = Blog.objects.all()
    filter = BlogFilter(request.GET, queryset=blogs)
    serializer = BlogSerializer(filter.qs, many=True)
    return Response(serializer.data)

ZAP_API_KEY = 'u3a642dp7nchdoi6vqotikufs'  
ZAP_PROXY_HOST = '127.0.0.1'
ZAP_PROXY_PORT = '8080'

class OWASPScanView(APIView):
    """
    URL-i kabul edýär, diňe Spider işleýär (Active Scan wagtlaýyn öçürilen).
    Netijede Passive Scan (Passiw howpsuzlyk barlagy) netijelerini gaýtarýar.
    """
    
    def post(self, request):
        target_url = request.data.get('url')

        if not target_url:
            return Response({"error": "URL hökman girizilmeli"}, status=status.HTTP_400_BAD_REQUEST)

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
            # Spider adatça çalt gutarýar
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
            
            formatted_alerts = []
            for alert in alerts:
                formatted_alerts.append({
                    "alert": alert.get('alert'),
                    "risk": alert.get('risk'),
                    "confidence": alert.get('confidence'),
                    "url": alert.get('url'),
                    "description": alert.get('description'),
                    "solution": alert.get('solution')
                })

            return Response({
                "message": "Skanirleme (Spider & Passive) üstünlikli tamamlandy",
                "target": target_url,
                "total_alerts": len(formatted_alerts),
                "alerts": formatted_alerts
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)