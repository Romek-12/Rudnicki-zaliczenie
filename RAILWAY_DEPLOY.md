# 🚀 Jak wdrożyć aplikację na Railway

## Wymagania wstępne
- Konto na [Railway.app](https://railway.app)
- Konto GitHub (Railway automatycznie deployuje kod z repozytorium)

## Krok 1: Wyślij kod na GitHub

1. Stwórz nowe repozytorium na GitHub (np. `dietician-app`)
2. W terminalu, w folderze projektu, wykonaj:

```powershell
git add .
git commit -m "Przygotowanie do deployment na Railway"
git branch -M main
git remote add origin https://github.com/TWOJA-NAZWA/dietician-app.git
git push -u origin main
```

## Krok 2: Wdróż na Railway

1. Wejdź na https://railway.app i zaloguj się przez GitHub
2. Kliknij **"New Project"**
3. Wybierz **"Deploy from GitHub repo"**
4. Wybierz swoje repozytorium (`dietician-app`)
5. Railway automatycznie wykryje Python i zainstaluje zależności

## Krok 3: Ustaw zmienną środowiskową SECRET_KEY

1. W Railway, kliknij na swój projekt
2. Przejdź do zakładki **"Variables"**
3. Dodaj nową zmienną:
   - **Nazwa**: `SECRET_KEY`
   - **Wartość**: wygeneruj losowy ciąg znaków (np. użyj: https://randomkeygen.com/)
   
Przykład: `SECRET_KEY=k9j2h3g4f5d6s7a8q9w0e1r2t3y4u5i6o7p8`

## Krok 4: Dodaj domenę publiczną

1. W zakładce **"Settings"**
2. W sekcji **"Domains"**, kliknij **"Generate Domain"**
3. Railway wygeneruje darmowy adres URL typu: `twoja-aplikacja.up.railway.app`

## ⚠️ WAŻNE: Problem z SQLite na Railway

Railway **może resetować pliki** (w tym bazę danych SQLite) przy każdym wdrożeniu!

### **Rozwiązanie 1: PostgreSQL (ZALECANE dla produkcji)**

Railway oferuje **darmową bazę PostgreSQL**:

1. W projekcie Railway kliknij **"New" → "Database" → "Add PostgreSQL"**
2. Railway automatycznie utworzy zmienną `DATABASE_URL`
3. Zmień `app.py`:

```python
# Zamiast SQLite:
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'

# Użyj PostgreSQL:
import os
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///users.db')

# UWAGA: Railway używa postgres://, ale SQLAlchemy wymaga postgresql://
database_url = os.environ.get('DATABASE_URL', 'sqlite:///users.db')
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
```

4. Dodaj `psycopg2-binary` do `requirements.txt`:

```txt
Flask
Flask-SQLAlchemy
Flask-Login
werkzeug
gunicorn
psycopg2-binary
```

### **Rozwiązanie 2: Railway Volumes (dla SQLite)**

Jeśli chcesz zostać z SQLite:

1. W Railway, przejdź do **Settings → Volumes**
2. Dodaj nowy volumen:
   - **Mount Path**: `/app/instance`
3. To zachowa bazę danych między deployami

## Krok 5: Sprawdź logi

Po wdrożeniu:
1. Przejdź do zakładki **"Deployments"**
2. Kliknij na najnowszy deployment
3. Sprawdź **"View Logs"** by zobaczyć czy aplikacja działa

## 🎉 Gotowe!

Twoja aplikacja powinna być teraz dostępna pod adresem nadanym przez Railway!

---

## 📝 Aktualizacje aplikacji

Po każdej zmianie w kodzie:

```powershell
git add .
git commit -m "Opis zmian"
git push
```

Railway automatycznie wykryje zmiany i wdroży nową wersję!
