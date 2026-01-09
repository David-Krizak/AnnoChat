# Web Chat aplikacija (Flask)

## Opis projekta
Ova aplikacija je jednostavna web chat aplikacija izrađena u Pythonu korištenjem Flask frameworka. Korisnici mogu unijeti svoje korisničko ime i naziv chat sobe te komunicirati u stvarnom vremenu bez registracije i pohrane podataka. Aplikacija koristi WebSocket komunikaciju putem Flask-SocketIO biblioteke.

## Funkcionalnosti
- ulazak u chat sobu bez registracije
- odabir korisničkog imena
- kreiranje i ulazak u chat sobe po nazivu
- slanje i primanje poruka u stvarnom vremenu
- sustavne poruke pri ulasku i izlasku iz sobe
- responzivno sučelje (Bootstrap)

## Korištene tehnologije
- Python 3
- Flask
- Flask-SocketIO
- HTML5
- CSS3
- Bootstrap 5
- JavaScript (Socket.IO)

## Struktura projekta
Webchat/
├── app.py
├── requirements.txt
├── templates/
│   ├── index.html
│   └── chat.html
└── static/
    └── style.css

## Pokretanje aplikacije
1. Klonirati repozitorij  
git clone <URL_REPOZITORIJA>  
cd Webchat  

2. Kreirati virtualno okruženje  
python -m venv .venv  

Windows:  
.venv\Scripts\activate  

Linux / macOS:  
source .venv/bin/activate  

3. Instalirati ovisnosti  
pip install -r requirements.txt  

4. Pokrenuti aplikaciju  
python app.py  

Aplikacija je dostupna na adresi:  
http://127.0.0.1:5000

## Način korištenja
1. Otvoriti početnu stranicu aplikacije  
2. Unijeti korisničko ime  
3. Unijeti naziv chat sobe  
4. Slati poruke ostalim korisnicima u istoj sobi  

## Napomena
- Podaci o korisnicima i porukama se ne spremaju u bazu podataka
- Svi podaci vrijede samo tijekom trajanja sesije
- Aplikacija je namijenjena edukativnoj upotrebi

## Moguća proširenja
- slanje slika i datoteka
- prikaz liste aktivnih korisnika
- dodavanje vremenskih oznaka poruka
- autentikacija korisnika

