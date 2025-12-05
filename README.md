# Backend - Taslama Gollanmasy

Bu taslamanyň serwer tarapy (backend) **Django** çarçuwasy arkaly işlenip düzüldi.

## Talaplar (Prerequisites)

Kody işletmezden ozal aşakdaky programmalaryň kompýuteriňizde gurnalandygyny anyklaň:

- **Python 3.8+**
- **OWASP ZAP** (Windows üçin) - Howpsuzlyk barlaglary üçin zerur.

## Gurnamak we Işletmek (Installation & Running)

Taslamany öz kompýuteriňizde işletmek üçin aşakdaky ädimleri ýerine ýetiriň:

1. **Wirtual gurşawy dörediň we işjeňleşdiriň:**

   Windows üçin:

   ```bash
   python -m venv env
   .\env\Scripts\activate
   ```

   Linux/macOS üçin:

   ```bash
   python3 -m venv env
   source env/bin/activate
   ```

2. **Gerekli kitaphanalary gurnaň:**

   ```bash
   pip install django djangorestframework django-cors-headers
   # Eger requirements.txt faýly bar bolsa:
   # pip install -r requirements.txt
   ```

3. **Maglumat bazasyny täzeläň (Migrasiýa):**

   ```bash
   python manage.py migrate
   ```

4. **Serweri işlediň:**

   ```bash
   python manage.py runserver
   ```

   Serwer işläp başlansoň, `http://127.0.0.1:8000/` salgysyndan girip bilersiňiz.

## Howpsuzlyk (OWASP ZAP)

Bu taslamada howpsuzlyk barlaglaryny geçirmek üçin **OWASP ZAP** programmasynyň Windows wersiýasyny gurnamalylygyny ýatdan çykarmaň.
Bu gural arkaly API we web sahypanyň goraýyş ukybyny barlap bilersiňiz.

- Ýüklemek üçin: [OWASP ZAP Download](https://www.zaproxy.org/download/)
