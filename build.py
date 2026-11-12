#!/usr/bin/env python3
"""
Bouwt de Amakhosi-pagina's uit src/ naar de hoofdmap.

    python3 build.py
    python3 build.py --voorbeeld          alle blogartikels, ook met een datum in de toekomst
    python3 build.py --datum=2026-11-09   bouwen alsof het die dag is

- src/partials/   gedeelde stukken (iconen, header, footer, mobiele balk)
- src/pages/      inhoud per pagina (alles binnen <main>)
- src/blog/       tekst per blogartikel (HTML-fragment, zie BLOG hieronder)

Hier staan ook de gedeelde gegevens (navigatie, prijzen, FAQ's, SEO per
pagina), zodat HTML, prijzen en gestructureerde data (JSON-LD) altijd
overeenkomen. Alleen de standaardbibliotheek van Python is nodig.

Let op: een build met --voorbeeld of --datum is alleen om lokaal na te
kijken. Bouw daarna opnieuw zonder optie voor je publiceert.
"""
import html
import json
import math
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"

SITE = "https://amakhosi.be"
MEDIA = "https://assets.cdn.filesafe.space/8mwRjKt9TFTVWGHrrl0R/media/"
LOGO = MEDIA + "6a8428d4acc26e1326c1092e.png"
PHONE_DISPLAY = "+32 (0)469 217 550"
PHONE_TEL = "+32469217550"
EMAIL = "info@amakhosi.be"
# Sociale media (meeting Patrick 31/10/2026, pagina's nagekeken op 5/11/2026): footer en sameAs
FACEBOOK = "https://www.facebook.com/people/Amakhosi/61553652565496/"
INSTAGRAM = "https://www.instagram.com/amakhosiwellness/"

# Navigatie: (sleutel, url, label)
NAV = [
    ("home", "/", "Home"),
    ("impressie", "/privesauna-wellness-impressie", "Impressie"),
    ("arrangementen", "/arrangementen", "Arrangementen"),
    ("prijslijst", "/prijslijst", "Prijslijst"),
    ("deals", "/koninklijke-deals", "Koninklijke deals"),
]

# --------------------------------------------------------------------------
# Prijzen (enige bron voor kaarten, tabellen en schema)
# --------------------------------------------------------------------------
# Namen, prijzen en duur zijn gelijk aan de online agenda (GHL-boekingswidget),
# zodat klanten op de site en in de agenda hetzelfde zien.
WELLNESS = [
    dict(name="Even ontsnappen", price=169, time="3 uur", hours=3,
         desc="Even weg uit de dagelijkse drukte."),
    dict(name="Een dagdeel", price=199, time="4 uur", hours=4,
         desc="Extra tijd om alles rustig te beleven."),
    dict(name="Ultieme verwennerij", price=239, time="5 uur", hours=5,
         desc="Een oase van warmte, rust en comfort."),
    dict(name="Extra long stay", price=279, time="6 uur", hours=6,
         desc="Uitgebreid genieten, zonder op de klok te kijken.", badge="Meeste tijd voor jou"),
]
NACHT = [
    dict(name="Kom overnachten", price=335, time="20:00 – 10:00", hours=14,
         desc="Overnachten met onbeperkt toegang tot de wellness."),
    dict(name="Slaap lekker uit", price=399, time="20:00 – 12:00", hours=16,
         desc="Uitslapen en nagenieten tot 12:00, zonder wekker.", badge="Uitslapen tot 12 u"),
]

# --------------------------------------------------------------------------
# Cadeaubon (digitale cadeaubon in ons platform, Payments -> Gift cards)
# --------------------------------------------------------------------------
# Zet hier het ID van de cadeaubon "Cadeaubon Amakhosi" (te vinden in de
# deellink https://link.fastpaydirect.com/gift-card/<ID>). Zolang het leeg is,
# wordt /cadeaubon niet gebouwd en verschijnen er nergens links naar.
# Let op: maak je in ons platform een nieuwe bon aan, dan werkt de oude niet
# meer en moet het nieuwe ID hier komen.
GIFTCARD_ID = "6acc98faeb8d718348d77bc0"
GIFTCARD_URL = "https://link.fastpaydirect.com/gift-card/" + GIFTCARD_ID

# Directe link naar de online agenda (volledig scherm, handig op telefoons)
# Boekingspagina "Amakhosi Reserveren" (29/10/2026): alleen de 6 gewone diensten,
# zonder de koninklijke deals. De deal-knoppen hebben een eigen link (scripts.js, deel 18).
BOOKING_URL = "https://api.leadconnectorhq.com/booking/amakhosi/bp/4jpwBFxC0goDq4tb5x6L?showHeader=true"
CHECKS_WELLNESS = [
    "Volledige privéwellness",
    "Finse sauna, stoombad &amp; whirlpool",
    "Gratis frisdrank, koffie &amp; thee",
]
CHECKS_NACHT = [
    "Aparte slaapsuite met inloopdouche",
    "Onbeperkt gebruik van alle faciliteiten",
    "Ontbijt voor twee bij te boeken",
]

# --------------------------------------------------------------------------
# Koninklijke deals (enige bron voor de dealkaarten op /koninklijke-deals en
# de meta description van die pagina)
# --------------------------------------------------------------------------
# Akkoord van de klant op 23/10/2026 (deal 1 en 2 van het voorstel). Een deal
# staat online tot en met "end": bouw opnieuw na die datum (28/2 en 31/3/2027),
# dan verdwijnt de kaart en past de meta description zich aan. Zonder lopende
# deal valt de hele sectie weg.
# - slug: de deal-knop opent /reserveren?deal=<slug> (scripts.js, deel 18)
# - lead: stukje van de inleiding boven de kaarten
# - meta: stukje van de meta description ({price} = de dealprijs)
DEALS_HEAD = dict(
    eyebrow="Deze winter",
    lead="Doordeweeks krijg je deze winter net iets meer: {}.",
    # Vaste link naar het winterartikel (SEO-plan A8). Valt mee weg met de deals.
    more=('Waarom een privésauna in de winter zo fijn is, lees je in ons artikel over '
          '<a class="amk-inline-link" href="/blog/privesauna-in-de-winter">sauna in de winter</a>.'),
)
DEALS = [
    dict(
        slug="winterdagen", name="Koninklijke Winterdagen", icon="snow",
        label="Vanaf 1 november &middot; maandag tot donderdag",
        text="Kom je van november tot en met februari op een maandag, dinsdag, woensdag of donderdag? Dan krijg je bij &lsquo;Een dagdeel&rsquo; het vijfde uur cadeau. Je geniet 5 uur van de wellness voor de prijs van 4 uur.",
        old_price=239, price=199, price_note="voor 5 uur",
        terms=["Start om 10:00 of 14:30",
               "Geldig van 1 november 2026 tot en met 28 februari 2027",
               "Niet op 24 en 31 december"],
        button="Reserveer je winterdag",
        lead="een uur extra wellness",
        meta="doordeweeks 5 uur privéwellness voor €{price}",
        end="2027-02-28",
    ),
    dict(
        slug="uitslapen", name="Koninklijk Uitslapen", icon="bed",
        label="Vanaf 1 november &middot; overnachting",
        text="Kom je van november tot en met maart overnachten, met aankomst op een maandag, dinsdag of woensdag? Dan slaap je zonder meerprijs uit tot 12:00. Je betaalt de prijs van &lsquo;Kom overnachten&rsquo; en blijft twee uur langer.",
        old_price=399, price=335, price_note="van 20:00 tot 12:00",
        terms=["Aankomst op maandag, dinsdag of woensdag",
               "Geldig van 1 november 2026 tot en met 31 maart 2027",
               "Ontbijt is niet inbegrepen"],
        button="Reserveer je overnachting",
        lead="uitslapen tot 12:00",
        meta="overnachten met uitslapen tot 12:00 voor €{price}",
        end="2027-03-31",
    ),
]

# --------------------------------------------------------------------------
# Veelgestelde vragen (HTML + FAQPage-schema uit dezelfde bron)
# --------------------------------------------------------------------------
FAQ = {
    "home": [
        ("Is de wellness echt volledig privé?",
         "Ja. Tijdens je arrangement heb je de volledige wellness voor jezelf: de Finse sauna, het stoombad, de whirlpool, de inloopdouche en de lounge. Er zijn geen gedeelde ruimtes en geen andere gasten."),
        ("Hoe lang kan ik blijven?",
         f"Het kortste arrangement duurt {WELLNESS[0]['time']} ({WELLNESS[0]['name']}, € {WELLNESS[0]['price']}). "
         'Je kiest voor 3, 4, 5 of 6 uur wellness, of voor een overnachting van 20:00 tot 10:00 (14 uur) of van 20:00 tot 12:00 (16 uur). Bekijk alle prijzen op de <a href="/prijslijst">prijslijst</a>.'),
        ("Kan ik eten en drinken bijboeken?",
         'Zeker. Denk aan een luxe tapas-, kaas- of fruitplank, snacks, champagne, prosecco of Afrikaanse wijn, en bij een overnachting een ontbijt voor twee. Alle gerechten kunnen halal of vegetarisch bereid worden. Bekijk alle <a href="/arrangementen">extra\'s</a>.'),
        ("Wat is inbegrepen?",
         "Gratis frisdrank, koffie en thee tijdens je verblijf, een smart-tv met sfeerhaard, airconditioning en een gratis privéparkeerplaats met laadpaal. Bij een overnachting krijg je een aparte slaapsuite met eigen inloopdouche."),
        ("Wat zijn de openingstijden?",
         'Amakhosi werkt op afspraak. Kies je moment in de <a href="/reserveren">online agenda</a> of bel ons voor de mogelijkheden.'),
        ("Waar ligt Amakhosi?",
         "In de Watertorenstraat 64 in Hamont-Achel, op de grens van Belgisch en Nederlands Limburg. Vlot bereikbaar vanuit Pelt, Lommel, Bree, Peer, Budel, Weert en Eindhoven."),
    ],
    "prijslijst": [
        ("Wat kost een privésauna bij Amakhosi?",
         "Een wellnessarrangement kost €169 voor 3 uur, €199 voor 4 uur, €239 voor 5 uur of €279 voor 6 uur. Een overnachting met aparte slaapsuite kost €335 (20:00 tot 10:00, 14 uur) of €399 (20:00 tot 12:00, 16 uur)."),
        ("Wat is inbegrepen in de prijs?",
         "Het volledig privégebruik van de Finse sauna, het stoombad, de whirlpool, de inloopdouche en de lounge, gratis frisdrank, koffie en thee, smart-tv met sfeerhaard, airco en een gratis privéparkeerplaats met laadpaal. Bij een overnachting hoort daar een aparte slaapsuite met inloopdouche bij."),
        ("Kan ik extra's bijboeken?",
         'Ja: een romantisch pakket, een ontbijt voor twee (bij overnachting), champagne of wijn en luxe tapas-, kaas- of fruitplanken. Alles staat op de pagina <a href="/arrangementen">arrangementen</a>.'),
        ("Hoe reserveer ik?",
         'Kies je arrangement, datum en tijdstip in de <a href="/reserveren">online agenda</a>. Liever persoonlijk? Bel ons op ' + PHONE_DISPLAY + "."),
    ],
    "arrangementen": [
        ("Moet ik planken vooraf bestellen?",
         "De luxe tapasplank en de fruitplank bestel je minstens één dag vooraf. Toch last minute zin in iets lekkers? Bel ons even, dan bekijken we wat mogelijk is."),
        ("Zijn er halal of vegetarische opties?",
         "Ja. Alle gerechten kunnen halal of vegetarisch bereid worden. Geef het gewoon door bij je reservatie."),
        ("Kan ik ontbijt bijboeken?",
         "Het ontbijt voor twee personen (€ 38) is extra te boeken bij een overnachting: verse broodjes, croissants, een eitje naar keuze, vleeswaren, kaas en zoet beleg, vers fruit, yoghurt, een Afrikaanse muffin en verse jus d'orange."),
        ("Kan de champagne koud klaarstaan bij aankomst?",
         "Ja. De gekoelde fles champagne kan op verzoek koud geserveerd worden wanneer je aankomt."),
    ],
    "reserveren": [
        ("Hoe werkt online reserveren?",
         "Kies in de agenda je arrangement, eventuele extra's, de datum en het tijdstip, en vul je gegevens in. Lukt het op je telefoon niet goed? Open de agenda dan op volledig scherm met de knop boven de agenda, of bel ons."),
        ("Ik heb een Nederlands telefoonnummer. Wat vul ik in?",
         "Typ je nummer met landcode, bijvoorbeeld +31 6 12345678. Een Belgisch nummer mag gewoon zoals je het kent, bijvoorbeeld 0470 12 34 56."),
        ("Kan ik ook telefonisch reserveren?",
         "Natuurlijk. Bel ons op " + PHONE_DISPLAY + " of mail naar " + EMAIL + "."),
        ("Wanneer is Amakhosi open?",
         "Amakhosi werkt op afspraak. In de online agenda zie je welke momenten nog vrij zijn."),
        ("Waar kan ik parkeren?",
         "Je parkeert gratis op je eigen privéparkeerplaats, direct bij de ingang. Er is ook een laadpaal voor elektrische wagens."),
    ],
}


def _of(items):
    """'a, b of c'"""
    return ", ".join(items[:-1]) + " of " + items[-1] if len(items) > 1 else items[0]


def _van_tot(p):
    """'20:00 – 10:00' -> 'van 20:00 tot 10:00'"""
    start, end = p["time"].split(" – ")
    return f"van {start} tot {end}"


# /cadeaubon (SEO-plan A4, 12/11/2026): alleen feiten die al op de site staan.
# Geldigheid en gedeeltelijk gebruik van de bon NIET vermelden: wacht op de klant.
FAQ["cadeaubon"] = [
    ("Voor welke bedragen bestaat de cadeaubon?",
     "De waarde van de bon is de prijs van het arrangement dat je cadeau doet: "
     + _of([f"€ {p['price']} ({p['time']})" for p in WELLNESS]
           + [f"€ {p['price']} (overnachting {_van_tot(p)})" for p in NACHT]) + "."),
    ("Hoe bestel ik een cadeaubon?",
     "Kies op deze pagina het bedrag, vul je gegevens in en betaal veilig online. De bon komt per mail, "
     "met een unieke code. Lukt het niet? Bel ons op " + PHONE_DISPLAY + "."),
    ("Hoe wisselt de ontvanger de cadeaubon in?",
     "De ontvanger belt naar " + PHONE_DISPLAY + " of mailt naar " + EMAIL + " en geeft de code van de bon "
     "door. Amakhosi werkt op afspraak: de dag en het uur worden dan samen vastgelegd."),
    ("Kan ik ook een overnachting cadeau doen?",
     "Ja. Kies " + _of([f"{p['name']} ({_van_tot(p)}, € {p['price']})" for p in NACHT]) + ". De ontvangers "
     "krijgen een aparte slaapsuite met eigen inloopdouche en gebruiken alle faciliteiten onbeperkt."),
    ("Wat krijgt de ontvanger met de bon?",
     "Een arrangement bij Amakhosi in Hamont-Achel, ideaal voor twee. Tijdens het arrangement is de volledige "
     "wellness van hen alleen: Finse sauna, stoombad, whirlpool, inloopdouche en loungebed met sfeerhaard. "
     "Frisdrank, koffie en thee en de privéparking met laadpaal zijn gratis."),
]

# SEO-plan A8 (12/11/2026): extra vragen op de home en /reserveren, alleen met
# bevestigde feiten. Meeting 31/10/2026: badjassen en badslippers liggen klaar,
# douchegel en shampoo ook; last minute boeken mag. NIET vermelden zolang de
# klant het niet bevestigt: handdoeken, het maximum aantal personen, openingsuren
# en de geldigheid van de cadeaubon.
FAQ_KLAAR = (
    "Liggen er badjassen en badslippers klaar?",
    "Ja. Badjassen en badslippers liggen voor je klaar, net als douchegel en shampoo.")


def faq_last_minute(agenda):
    return ("Kan ik last minute reserveren?",
            f"Ja, last minute boeken kan. Kijk in de {agenda} welke momenten nog vrij zijn, of bel ons op "
            + PHONE_DISPLAY + ". Een luxe tapasplank of fruitschaal bestel je wel minstens één dag vooraf.")


FAQ_NEDERLAND = (
    "Kan ik vanuit Nederland online reserveren?",
    "Ja. Vul in de online agenda je gsm-nummer in met landcode, bijvoorbeeld +31 6 12345678. "
    "Telefonisch reserveren kan ook, op " + PHONE_DISPLAY + ".")
FAQ_KORTST = (
    "Wat is het kortste arrangement?",
    f"{WELLNESS[0]['name']}: {WELLNESS[0]['time']} privéwellness voor € {WELLNESS[0]['price']}. "
    f"Je kan ook {_of([p['time'].split()[0] for p in WELLNESS[1:]])} uur blijven, of overnachten. "
    'Alle prijzen staan op de <a href="/prijslijst">prijslijst</a>.')

FAQ["home"][4:4] = [FAQ_KLAAR]
FAQ["home"][-1:-1] = [faq_last_minute('<a href="/reserveren">online agenda</a>'), FAQ_NEDERLAND]
FAQ["reserveren"][3:3] = [FAQ_KORTST, faq_last_minute("online agenda hierboven")]
if GIFTCARD_ID:
    FAQ["home"][-1:-1] = [(
        "Kan ik een arrangement cadeau doen?",
        f"Ja, met een cadeaubon. De waarde van de bon is de prijs van het arrangement, van € {WELLNESS[0]['price']} "
        f"({WELLNESS[0]['time']}) tot € {NACHT[-1]['price']} (overnachting tot {NACHT[-1]['time'].split(' – ')[1]}). "
        "Je bestelt en betaalt online en de bon komt met een unieke code per mail. "
        'Bekijk de <a href="/cadeaubon">cadeaubon</a>.')]
    FAQ["reserveren"][5:5] = [(
        "Ik heb een cadeaubon. Hoe reserveer ik?",
        "Bel ons op " + PHONE_DISPLAY + " of mail naar " + EMAIL + " en geef de code van de bon door. "
        "Dan leggen we samen de dag en het uur vast.")]
FAQ["reserveren"][-2:-2] = [FAQ_KLAAR]

# --------------------------------------------------------------------------
# Blog (/blog en /blog/<slug>)
# --------------------------------------------------------------------------
# De teksten worden geschreven in Websites/Amakhosi/blog/teksten/<slug>.md
# (buiten deze map) en na akkoord letterlijk overgezet naar src/blog/<slug>.html.
# Per artikel: een regel in BLOG, de FAQ in FAQ["blog:<slug>"] en het fragment.
# - date/modified: publicatiedatum en laatste wijziging (JJJJ-MM-DD). Een
#   artikel met een datum na vandaag wordt niet gebouwd en staat nergens (niet
#   op /blog, de home, "Lees ook" of in de sitemap). Links ernaar worden gewone
#   tekst en zinnen tussen <!--ALS:slug--> en <!--/ALS--> vallen weg. Op de
#   publicatiedatum opnieuw bouwen en publiceren.
# - related: artikels voor "Lees ook" (alleen gepubliceerde worden getoond).
# - slot: slotblok onderaan. None = reserveren ({{PARTIAL:cta}}), anders
#   src/partials/cta-<slot>.html.
# - reserve_href: doel van de mobiele balk en de vaste knop. Een deal kan je
#   alleen boeken via de knop op /koninklijke-deals: een artikel over de deals
#   linkt daarom daarheen, nooit naar /reserveren?deal=...
# - home_until: het artikel staat tot en met die datum zeker in de blogteaser
#   op de home, ook als er nieuwere artikels zijn (anders: de nieuwste).
# Auteur van alle artikels (meeting 31/10/2026): de gastvrouw, Connie. Patrick
# wil niet vermeld worden.
BLOG_AUTHOR_NAME = "Connie"
BLOG_AUTHOR_LABEL = "je gastvrouw Connie"
BLOG = [
    dict(
        slug="wellness-cadeaubon-voor-2",
        title="Wellness cadeaubon voor 2: privésauna als cadeau | Amakhosi",
        description="Op zoek naar een wellness cadeaubon voor 2? Geef privéwellness vanaf €169 of een overnachting in Hamont-Achel. Tips voor Sinterklaas en kerst.",
        h1="Een wellness cadeaubon voor 2: zo kies en geef je het juiste cadeau",
        crumb="Cadeaubon voor twee", eyebrow="Cadeau",
        date="2026-11-02", modified="2026-11-02",
        image=("6a84993996d2b224d38ad40e.jpg", 2560, 1677),
        image_alt="Gekoelde champagne met twee glazen bij de sfeerhaard van Amakhosi",
        excerpt="Tijd samen cadeau doen: zo kies, bestel en geef je een wellness cadeaubon van Amakhosi, van 3 uur privéwellness tot een overnachting.",
        related=["privesauna-in-de-winter", "privesauna-met-overnachting-limburg", "privesauna-met-jacuzzi"],
        slot="cadeaubon",
    ),
    dict(
        slug="privesauna-in-de-winter",
        title="Sauna in de winter: opwarmen in je privésauna | Amakhosi",
        description="Sauna in de winter in Hamont-Achel: van maandag tot donderdag 5 uur privéwellness voor €199, of uitslapen tot 12:00. Bekijk de winterdeals.",
        h1="Sauna in de winter: opwarmen in je eigen privéwellness",
        crumb="Sauna in de winter", eyebrow="Winter",
        date="2026-11-02", modified="2026-11-02",
        image=("6a84993bd1abe28fc98f8e6d.jpg", 2560, 1707),
        image_alt="Whirlpool met warme oranje verlichting en de sfeerhaard van Amakhosi",
        excerpt="Koude dagen, warme sauna. Waarom een privésauna in de winter zo goed voelt, en hoe je van maandag tot donderdag 5 uur wellness krijgt voor € 199.",
        related=["wellness-cadeaubon-voor-2", "privesauna-met-overnachting-limburg", "privesauna-met-jacuzzi"],
        slot="deals", reserve_href="/koninklijke-deals",
        # Blijft op de home staan zolang de winterdeals lopen (SEO-plan A8)
        home_until=max(d["end"] for d in DEALS),
    ),
    dict(
        slug="privesauna-met-overnachting-limburg",
        title="Privésauna met overnachting in Limburg | Amakhosi",
        description="Privésauna met overnachting in Limburg: sauna, stoombad en whirlpool tot de volgende ochtend, met een aparte slaapsuite. Vanaf €335 in Hamont-Achel.",
        h1="Privésauna met overnachting in Limburg: zo verloopt jullie nacht bij Amakhosi",
        crumb="Privésauna met overnachting", eyebrow="Overnachten",
        date="2026-11-12", modified="2026-11-12",
        image=("6a849936b71315ed5245054d.jpg", 2048, 1365),
        image_alt="Slaapsuite van Amakhosi met tweepersoonsbed en Afrikaans beddengoed",
        excerpt="Sauna, stoombad en whirlpool de hele avond, slapen in je eigen suite en 's ochtends nog nagenieten. Zo verloopt een overnachting bij Amakhosi in Hamont-Achel.",
        related=["privesauna-in-de-winter", "privesauna-met-jacuzzi", "wellness-cadeaubon-voor-2"],
    ),
    dict(
        slug="privesauna-met-jacuzzi",
        title="Privésauna met jacuzzi voor twee | Amakhosi Hamont-Achel",
        description="Finse sauna, stoombad en een zeer ruime whirlpool voor jullie twee. Zo combineer je alles in je privésauna met jacuzzi in Hamont-Achel, vanaf €169.",
        h1="Privésauna met jacuzzi voor twee: sauna, stoombad en whirlpool combineren",
        crumb="Privésauna met jacuzzi", eyebrow="Wellness",
        date="2026-11-12", modified="2026-11-12",
        image=("6a84993662d4d706d4110075.jpg", 2048, 1292),
        image_alt="Privé-wellnessruimte van Amakhosi met ronde whirlpool, zebramuur en doorkijk naar het stoombad",
        excerpt="Een privésauna met jacuzzi, alleen voor jullie twee: zo combineer je Finse sauna, stoombad en whirlpool en kies je hoeveel tijd je neemt.",
        related=["privesauna-met-overnachting-limburg", "privesauna-in-de-winter"],
    ),
]

# Veelgestelde vragen per artikel: letterlijk uit het .md-bestand (HTML + FAQPage-schema)
FAQ["blog:wellness-cadeaubon-voor-2"] = [
    ("Voor welke bedragen bestaat de cadeaubon van Amakhosi?",
     "De waarde van de bon is de prijs van het arrangement dat je cadeau doet: € 169 (3 uur), € 199 (4 uur), € 239 (5 uur), € 279 (6 uur), € 335 (overnachting van 20:00 tot 10:00) of € 399 (overnachting van 20:00 tot 12:00)."),
    ("Hoe krijg ik de cadeaubon?",
     "Je kiest de bon op de pagina cadeaubon van Amakhosi, vult je gegevens in en betaalt veilig online. De bon komt per mail, met een unieke code."),
    ("Hoe wisselt de ontvanger de cadeaubon in?",
     "De ontvanger belt naar +32 (0)469 217 550 of mailt naar info@amakhosi.be en geeft de code van de bon door. Amakhosi werkt op afspraak: de dag en het uur worden in overleg vastgelegd."),
    ("Waar kan je de cadeaubon besteden?",
     "De cadeaubon besteed je bij Amakhosi zelf, in de Watertorenstraat 64 in Hamont-Achel, voor een arrangement privéwellness of een overnachting."),
    ("Kan ik ook een overnachting cadeau doen?",
     "Ja. Je kiest Kom overnachten (van 20:00 tot 10:00, € 335) of Slaap lekker uit (van 20:00 tot 12:00, € 399). De ontvangers hebben dan onbeperkt gebruik van alle faciliteiten en een aparte slaapsuite met eigen inloopdouche."),
]
FAQ["blog:privesauna-in-de-winter"] = [
    ("Waarom is een sauna in de winter zo fijn?",
     "Veel mensen ervaren de warmte van een sauna als extra fijn wanneer het buiten koud en donker is. In Finland, het land van de sauna, draait de sauna van oudsher vooral om plezier en ontspanning (Laukkanen e.a.)."),
    ("Tot wanneer lopen de winterdeals?",
     "Koninklijke Winterdagen loopt van 1 november 2026 tot en met 28 februari 2027, van maandag tot en met donderdag. Koninklijk Uitslapen loopt van 1 november 2026 tot en met 31 maart 2027, bij aankomst op maandag, dinsdag of woensdag."),
    ("Hoe boek ik een winterdeal?",
     "Alleen via de knop bij de deal op de pagina Koninklijke deals. Die knop opent de online agenda meteen bij de juiste deal. In de gewone agenda staan de deals niet."),
    ("Is ontbijt inbegrepen bij Koninklijk Uitslapen?",
     "Nee, bij deze deal is het ontbijt niet inbegrepen."),
    ("Kan ik een deal combineren met een andere actie?",
     "Nee. De deals gelden volgens beschikbaarheid en zijn niet combineerbaar met andere acties."),
]
FAQ["blog:privesauna-met-overnachting-limburg"] = [
    ("Hoe laat kom ik aan en vertrek ik bij een overnachting?",
     "Je komt om 20:00 aan. Bij Kom overnachten vertrek je om 10:00, bij Slaap lekker uit om 12:00."),
    ("Is het ontbijt inbegrepen bij een overnachting?",
     "Nee. Het ontbijt voor twee boek je extra bij een overnachting, voor € 38."),
    ("Kan ik tijdens mijn overnachting de sauna en de whirlpool blijven gebruiken?",
     "Ja. Tijdens je overnachting gebruik je alle faciliteiten onbeperkt."),
    ("Wat kost een privésauna met overnachting bij Amakhosi?",
     "Kom overnachten (van 20:00 tot 10:00) kost € 335 en Slaap lekker uit (van 20:00 tot 12:00) kost € 399. Van 1 november 2026 tot en met 31 maart 2027 blijf je bij aankomst op maandag, dinsdag of woensdag, volgens beschikbaarheid, tot 12:00 voor € 335. Die winterdeal boek je alleen via de knop op de pagina <a href=\"/koninklijke-deals\">Koninklijke deals</a>."),
    ("Ik woon in Nederland. Kan ik online reserveren?",
     "Ja. Vul in de online agenda je gsm-nummer (mobiel nummer) in met landcode, bijvoorbeeld +31 6 12345678. Telefonisch reserveren kan ook, op +32 (0)469 217 550."),
]
FAQ["blog:privesauna-met-jacuzzi"] = [
    ("Heeft Amakhosi een jacuzzi?",
     "Amakhosi heeft een zeer ruime whirlpool, wat veel mensen een jacuzzi of bubbelbad noemen. De whirlpool staat binnen, naast een Finse sauna en een stoombad, en tijdens je arrangement is alles volledig privé."),
    ("Wat doe je eerst: sauna, stoombad of whirlpool?",
     "Er is geen vaste volgorde. Begin met een douche, wissel warmte af met afkoelen en rust, en luister naar je lichaam."),
    ("Hoe lang blijf je best in de sauna?",
     "Volgens de Cleveland Clinic hou je een saunaronde best rond 15 tot 20 minuten, en begin je korter als je het niet gewoon bent. Voel je je duizelig of niet goed, ga dan meteen uit de sauna."),
    ("Wat kost een privésauna met jacuzzi bij Amakhosi?",
     "Een arrangement met Finse sauna, stoombad en whirlpool kost € 169 voor 3 uur, € 199 voor 4 uur, € 239 voor 5 uur of € 279 voor 6 uur. Een overnachting kost € 335 (van 20:00 tot 10:00) of € 399 (van 20:00 tot 12:00)."),
    ("Is de wellness geschikt voor een koppel?",
     "Zeker. Er is een whirlpool voor twee, een ruime inloopdouche voor twee personen en een loungebed om samen na te genieten."),
]


def _publish_date():
    """Tot en met welke datum artikels gepubliceerd worden (standaard vandaag)."""
    for arg in sys.argv[1:]:
        if arg == "--voorbeeld":
            return date.max
        if arg.startswith("--datum="):
            return date.fromisoformat(arg.split("=", 1)[1])
    return date.today()


PUBLISH_DATE = _publish_date()
# Gepubliceerde artikels, nieuwste eerst
BLOG_LIVE = sorted((a for a in BLOG if date.fromisoformat(a["date"]) <= PUBLISH_DATE),
                   key=lambda a: a["date"], reverse=True)
BLOG_SLUGS_LIVE = {a["slug"] for a in BLOG_LIVE}
BLOG_BY_SLUG = {a["slug"]: a for a in BLOG}
# Lopende deals (tot en met hun einddatum)
DEALS_LIVE = [d for d in DEALS if PUBLISH_DATE <= date.fromisoformat(d["end"])]


def deals_description():
    """Meta description van /koninklijke-deals, uit DEALS (max. 160 tekens)."""
    if not DEALS_LIVE:
        return ("De Koninklijke deals van Amakhosi: tijdelijke acties voor je privésauna "
                "en wellness in Hamont-Achel. Bel of mail ons gerust voor de mogelijkheden.")
    parts = [d["meta"].format(price=d["price"]) for d in DEALS_LIVE]
    text = ("Koninklijke deals in Hamont-Achel: " + " of ".join(parts)
            + ". Bekijk de voorwaarden.")
    assert len(text) <= 160, f"meta description deals te lang ({len(text)} tekens): {text}"
    return text


def arrangementen_description():
    """Meta description van /arrangementen, met de prijzen uit WELLNESS en NACHT."""
    text = (f"{WELLNESS[0]['hours']} tot {WELLNESS[-1]['hours']} uur privéwellness vanaf "
            f"€{min(p['price'] for p in WELLNESS)} of een overnachting vanaf "
            f"€{min(p['price'] for p in NACHT)} in Hamont-Achel. Vul aan met een romantisch "
            "pakket, ontbijt, champagne of een tapasplank.")
    assert len(text) <= 160, f"meta description arrangementen te lang ({len(text)} tekens): {text}"
    return text


# --------------------------------------------------------------------------
# Pagina's + SEO
# --------------------------------------------------------------------------
PAGES = [
    dict(
        key="home", src="index.html", out="index.html", path="/",
        title="Privésauna & Wellness Hamont-Achel | Amakhosi",
        description="Luxe privésauna & wellness in Hamont-Achel: Finse sauna, stoombad, whirlpool en overnachting voor twee. Koninklijk genieten in alle privacy. Reserveer online!",
        image=("6a84993662d4d706d4110075.jpg", 2048, 1292),
        image_alt="Privé-wellnessruimte van Amakhosi met whirlpool en zebramuur",
        faq="home",
    ),
    dict(
        key="impressie", src="impressie.html", out="privesauna-wellness-impressie.html",
        path="/privesauna-wellness-impressie", crumb="Impressie",
        title="Sfeerimpressie privésauna & wellness | Amakhosi Hamont-Achel",
        description="Ontdek de sfeer van Amakhosi: Finse sauna, stoombad, whirlpool voor twee, lounge met sfeerhaard en slaapsuite, in warme Afrikaanse stijl. Bekijk de foto's.",
        image=("6a84993b96d2b224d38addc6.jpg", 2560, 1707),
        image_alt="Lounge met loungebed, sfeerhaard en whirlpool bij Amakhosi",
        gallery=True,
    ),
    dict(
        key="arrangementen", src="arrangementen.html", out="arrangementen.html",
        path="/arrangementen", crumb="Arrangementen",
        title="Wellness arrangementen & extra's | Amakhosi Hamont-Achel",
        description=arrangementen_description(),
        image=("6a84993996d2b224d38ad40e.jpg", 2560, 1677),
        image_alt="Fles champagne met twee glazen bij de sfeerhaard",
        faq="arrangementen",
    ),
    dict(
        key="prijslijst", src="prijslijst.html", out="prijslijst.html",
        path="/prijslijst", crumb="Prijslijst",
        title="Prijzen privésauna & overnachting | Amakhosi Hamont-Achel",
        description="Prijslijst Amakhosi: privéwellness van €169 (3 uur) tot €279 (6 uur). Overnachting met aparte slaapsuite vanaf €335. Helemaal privé in Hamont-Achel.",
        image=("6a84993bd1abe28fc98f8e6d.jpg", 2560, 1707),
        image_alt="Whirlpool met warm oranje verlichting",
        faq="prijslijst",
        offers=True,
    ),
    dict(
        key="deals", src="koninklijke-deals.html", out="koninklijke-deals.html",
        path="/koninklijke-deals", crumb="Koninklijke deals",
        title="Koninklijke deals & acties | Amakhosi Hamont-Achel",
        description=deals_description(),
        image=("6a846eb24aaffc55cd792746.jpg", 1024, 784),
        image_alt="Loungebed versierd met een hart van rozenblaadjes",
    ),
    dict(
        key="reserveren", src="reserveren.html", out="reserveren.html",
        path="/reserveren", crumb="Reserveren",
        title="Reserveer je privésauna online | Amakhosi Hamont-Achel",
        description="Reserveer online je privésauna en wellness bij Amakhosi in Hamont-Achel. Kies je arrangement, datum en tijdstip, of bel ons op +32 (0)469 217 550.",
        image=("6a8435f545dbba232fa5362a.jpg", 2048, 1365),
        image_alt="Finse sauna met sfeerverlichting",
        faq="reserveren",
        booking=True,
    ),
]

LEGAL_PAGES = [
    dict(
        key="voorwaarden", src="algemene-voorwaarden.html", out="algemene-voorwaarden.html",
        path="/algemene-voorwaarden", crumb="Algemene voorwaarden", legal=True,
        title="Algemene voorwaarden | Amakhosi privésauna Hamont-Achel",
        description="De algemene voorwaarden van Amakhosi: reservatie, betaling, annuleren, aankomst en vertrek, huisregels en aansprakelijkheid voor je privésauna in Hamont-Achel.",
        image=("6a8435f545dbba232fa5362a.jpg", 2048, 1365),
        image_alt="Finse sauna van Amakhosi",
    ),
    dict(
        key="privacy", src="privacybeleid.html", out="privacybeleid.html",
        path="/privacybeleid", crumb="Privacybeleid", legal=True,
        title="Privacybeleid | Amakhosi privésauna Hamont-Achel",
        description="Hoe Amakhosi met je persoonsgegevens omgaat: welke gegevens we verzamelen bij een reservatie, waarom, met wie we ze delen, hoe lang we ze bewaren en je rechten.",
        image=("6a84993a62d4d706d41100e9.jpg", 1620, 2560),
        image_alt="Stoombad van Amakhosi met kaarslicht",
    ),
]
if GIFTCARD_ID:
    PAGES.append(dict(
        key="cadeaubon", src="cadeaubon.html", out="cadeaubon.html",
        path="/cadeaubon", crumb="Cadeaubon", lastmod="2026-11-12", faq="cadeaubon",
        title="Cadeaubon privésauna & wellness | Amakhosi Hamont-Achel",
        description="Geef een cadeaubon van Amakhosi: een arrangement privéwellness of een overnachting voor twee in Hamont-Achel. Online bestellen en betalen, de bon komt per mail.",
        image=("6a84993b96d2b224d38addc6.jpg", 2560, 1707),
        image_alt="Lounge met loungebed, sfeerhaard en whirlpool bij Amakhosi",
    ))
# Blog: alleen als er al een artikel gepubliceerd is (anders geen /blog en
# nergens een link naar de blog).
if BLOG_LIVE:
    PAGES.append(dict(
        key="blog", src="blog.html", out="blog.html", path="/blog", crumb="Blog",
        title="Blog over privésauna en wellness | Amakhosi Hamont-Achel",
        description="Tips en ideeën over privésauna en wellness in Hamont-Achel: van een cadeaubon voor twee tot overnachten in je eigen wellness. Lees de blog van Amakhosi.",
        image=("6a846a7cd07034adc2cd9d9f.jpg", 2048, 1365),
        image_alt="Afrikaanse muurschildering met doorkijk naar de slaapsuite",
        lastmod=max(a["modified"] for a in BLOG_LIVE), changefreq="weekly", priority="0.7",
        blog_index=True,
    ))
    for _a in BLOG_LIVE:
        PAGES.append(dict(
            key="blog:" + _a["slug"], src="blog-artikel.html", out=f"blog/{_a['slug']}.html",
            path=f"/blog/{_a['slug']}", crumb=_a["crumb"], crumbs=[("Blog", "/blog")],
            title=_a["title"], description=_a["description"],
            image=_a["image"], image_alt=_a["image_alt"],
            faq="blog:" + _a["slug"], lastmod=_a["modified"], changefreq="monthly", priority="0.6",
            article=_a, reserve_href=_a.get("reserve_href"),
        ))
PAGES += LEGAL_PAGES

GALLERY = [
    ("6a84993662d4d706d4110075.jpg", 2048, 1292, "Wellnessruimte met whirlpool, zebramuur en doorkijk naar het stoombad"),
    ("6a84993dd1abe28fc98f8e85.jpg", 1707, 2560, "Finse sauna met houten banken en indirecte verlichting"),
    ("6a84993b96d2b224d38addc6.jpg", 2560, 1707, "Loungebed met Afrikaanse kussens, sfeerhaard en whirlpool"),
    ("6a84993a62d4d706d41100e9.jpg", 1620, 2560, "Stoombad met groene mozaïektegels en kaarslicht"),
    ("6a846a7cd07034adc2cd9d9f.jpg", 2048, 1365, "Afrikaanse muurschildering met doorkijk naar de slaapsuite"),
    ("6a84993bd1abe28fc98f8e6d.jpg", 2560, 1707, "Whirlpool met warme verlichting en sfeerhaard"),
    ("6a846eb2d1abe28fc956684b.jpg", 660, 1024, "Inloopdouche met gouden mozaïek"),
    ("6a849936b71315ed5245054d.jpg", 2048, 1365, "Slaapsuite met tweepersoonsbed en Afrikaans beddengoed"),
    ("6a846eb24aaffc55cd792746.jpg", 1024, 784, "Loungebed met een hart van rozenblaadjes"),
    ("6a84993996d2b224d38ad40e.jpg", 2560, 1677, "Champagne en twee glazen bij de sfeerhaard"),
    ("6a84993dd1abe28fc98f8e9b.jpg", 1084, 2560, "Muur met Afrikaanse spreuken"),
    ("6a84993696d2b224d38ac965.jpg", 2560, 1707, "Luxe schaal met vers seizoensfruit"),
    ("6a8435f545dbba232fa5362a.jpg", 2048, 1365, "Finse sauna met verlichte banken en handdoeken"),
]

AREAS = ["Hamont-Achel", "Pelt", "Lommel", "Bree", "Peer", "Budel", "Weert", "Eindhoven"]


# --------------------------------------------------------------------------
# Hulpfuncties voor HTML
# --------------------------------------------------------------------------
def icon(name, cls=""):
    c = "amk-icon" + (" " + cls if cls else "")
    return f'<svg class="{c}" aria-hidden="true"><use href="#amk-i-{name}"/></svg>'


def esc(s):
    return html.escape(s, quote=True)


def strip_tags(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s))


def time_label(p):
    """'3 uur' of '20:00 – 10:00 · 14 uur'."""
    return f"{p['time']} · {p['hours']} uur" if ":" in p["time"] else p["time"]


def euro(amount):
    """Belgische notatie: € 32,50 of € 35."""
    if float(amount).is_integer():
        return f"€ {int(amount)}"
    return "€ " + f"{amount:.2f}".replace(".", ",")


def summary_rows(kind):
    items = NACHT if kind == "nacht" else WELLNESS
    out = []
    for p in items:
        left = f"{p['name']} · {time_label(p)}"
        out.append(f'<div class="amk-summary__row"><span>{left}</span><strong>{euro(p["price"])}</strong></div>')
    return "\n            ".join(out)


def price_card(p, checks, kind):
    featured = bool(p.get("badge"))
    badge = (f'<span class="amk-price__badge">{icon("crown")}{p["badge"]}</span>' if featured else "")
    unit = "per overnachting" if kind == "nacht" else "per arrangement"
    btn_cls = "amk-btn--gold" if featured else "amk-btn--ghost"
    label = "Reserveer overnachting" if kind == "nacht" else f"Reserveer {p['time']}"
    checks_html = "".join(f"<li>{icon('check')}{c}</li>" for c in checks)
    return f"""
          <article class="amk-price amk-spot{' amk-price--featured' if featured else ''}" data-amk-tilt="5">
            <div class="amk-price__top">
              <span class="amk-price__time">{icon("clock")}{time_label(p)}</span>
              {badge}
            </div>
            <h3 class="amk-price__name">{p["name"]}</h3>
            <p class="amk-price__desc">{p["desc"]}</p>
            <p class="amk-price__amount"><span>€</span><strong data-amk-count>{p["price"]}</strong><small>{unit}</small></p>
            <ul class="amk-checks">{checks_html}</ul>
            <a class="amk-btn {btn_cls} amk-btn--block" href="/reserveren">{label}{icon("arrow", "amk-icon--arrow")}</a>
          </article>"""


def price_cards(kind):
    items, checks = (NACHT, CHECKS_NACHT) if kind == "nacht" else (WELLNESS, CHECKS_WELLNESS)
    return "".join(price_card(p, checks, kind) for p in items)


def faq_list(key, open_first=True):
    out = []
    for i, (q, a) in enumerate(FAQ[key]):
        is_open = " open" if (open_first and i == 0) else ""
        out.append(f"""
          <details class="amk-faq__item"{is_open}>
            <summary>{q}<span class="amk-faq__toggle" aria-hidden="true">{icon("plus")}</span></summary>
            <div class="amk-faq__answer"><div><p>{a}</p></div></div>
          </details>""")
    return "".join(out)


def durations():
    out = []
    for p in WELLNESS:
        out.append(f"""
          <a class="amk-duration" href="/prijslijst">
            <span class="amk-duration__time">{p["time"]}</span>
            <span class="amk-duration__name">{p["name"]}</span>
            <span class="amk-duration__price">€ {p["price"]}</span>
          </a>""")
    for p in NACHT:
        out.append(f"""
          <a class="amk-duration amk-duration--night" href="/prijslijst">
            <span class="amk-duration__time">{p["time"]} · {p["hours"]} uur</span>
            <span class="amk-duration__name">{p["name"]}</span>
            <span class="amk-duration__price">€ {p["price"]}</span>
          </a>""")
    return "".join(out)


def compare_table():
    cols = WELLNESS + NACHT
    head = "".join(f'<th scope="col">{p["name"]}<small>{time_label(p)}</small></th>' for p in cols)
    ok = icon("check")
    no = '<span class="amk-dash" aria-hidden="true">—</span><span class="amk-sr-only">niet inbegrepen</span>'
    n_well, n_night = len(WELLNESS), len(NACHT)
    rows = [
        ("Prijs", [euro(p["price"]) for p in cols]),
        ("Volledige privéwellness", [ok] * len(cols)),
        ("Finse sauna, stoombad &amp; whirlpool", [ok] * len(cols)),
        ("Inloopdouche &amp; loungebed", [ok] * len(cols)),
        ("Gratis frisdrank, koffie &amp; thee", [ok] * len(cols)),
        ("Smart-tv met sfeerhaard", [ok] * len(cols)),
        ("Aparte slaapsuite met inloopdouche", [no] * n_well + [ok] * n_night),
        ("Ontbijt voor twee bij te boeken (€ 38)", [no] * n_well + [ok] * n_night),
        ("Gratis privéparking met laadpaal", [ok] * len(cols)),
    ]
    body = ""
    for label, cells in rows:
        tds = "".join(
            f"<td>{c}</td>" if not c.startswith("<svg") else f'<td><span class="amk-sr-only">inbegrepen</span>{c}</td>'
            for c in cells
        )
        body += f'<tr><th scope="row">{label}</th>{tds}</tr>'
    return f"""
        <div class="amk-compare-wrap" data-amk-reveal>
          <table class="amk-compare">
            <caption class="amk-sr-only">Vergelijking van de arrangementen van Amakhosi</caption>
            <thead><tr><td></td>{head}</tr></thead>
            <tbody>{body}</tbody>
          </table>
        </div>"""


def gallery():
    out = []
    for f, w, h, alt in GALLERY:
        out.append(f"""
          <a class="amk-gallery__item" href="{MEDIA}{f}" data-amk-gallery data-caption="{esc(alt)}">
            <img src="{MEDIA}{f}" alt="{esc(alt)}" width="{w}" height="{h}" loading="lazy" decoding="async">
          </a>""")
    return "".join(out)


def gift_options():
    """Keuze van de cadeaubon: de bedragen zijn de prijzen van de arrangementen."""
    out = []
    for p in WELLNESS + NACHT:
        night = " amk-duration--night" if p in NACHT else ""
        out.append(f"""
          <a class="amk-duration{night}" href="#bestellen">
            <span class="amk-duration__time">{time_label(p)}</span>
            <span class="amk-duration__name">{p["name"]}</span>
            <span class="amk-duration__price">{euro(p["price"])}</span>
          </a>""")
    return "".join(out)


def gift_link(kind):
    """Links naar /cadeaubon, alleen als de cadeaubon in ons platform bestaat."""
    if not GIFTCARD_ID:
        return ""
    if kind == "footer":
        return '<li><a href="/cadeaubon">Cadeaubon</a></li>'
    if kind == "inline":
        return f'<a class="amk-link" href="/cadeaubon">Geef een cadeaubon {icon("arrow")}</a>'
    if kind == "zin":
        # Stukje zin in een lopende tekst (home, SEO-plan A8)
        return ' of geef een arrangement cadeau met een <a class="amk-inline-link" href="/cadeaubon">cadeaubon</a>'
    if kind == "block":
        return (f'<p class="amk-gift__note" data-amk-reveal>{icon("gift")}'
                f'<span>Een arrangement cadeau doen? Geef een '
                f'<a class="amk-inline-link" href="/cadeaubon">cadeaubon van Amakhosi</a>.</span></p>')
    raise KeyError(kind)


def deal_card(d):
    terms = "".join(f"\n              <li>{t}</li>" for t in d["terms"])
    return f"""
          <article class="amk-deal amk-spot" data-amk-tilt="4">
            <span class="amk-deal__label">{icon(d["icon"])}{d["label"]}</span>
            <h3>{d["name"]}</h3>
            <p>{d["text"]}</p>
            <p class="amk-deal__prijs"><del>&euro;{d["old_price"]}</del> <strong>&euro;{d["price"]}</strong> <span>{d["price_note"]}</span></p>
            <ul class="amk-deal__voorwaarden">{terms}
            </ul>
            <a class="amk-btn amk-btn--gold" href="/reserveren?deal={d["slug"]}#agenda">{icon("calendar")}{d["button"]}</a>
          </article>"""


def deals_section():
    """Sectie met de lopende deals op /koninklijke-deals (niets als er geen loopt)."""
    if not DEALS_LIVE:
        return ""
    lead = DEALS_HEAD["lead"].format(" of ".join(d["lead"] for d in DEALS_LIVE))
    cards = "".join(deal_card(d) for d in DEALS_LIVE)
    return f"""    <!-- =================================================================
         DEALS (uit DEALS in build.py)
         ================================================================= -->
    <section class="amk-section amk-section--deep" id="deals" aria-labelledby="amk-deals-title">
      <div class="amk-container">
        <div class="amk-head amk-head--split">
          <div data-amk-reveal>
            <p class="amk-eyebrow">{DEALS_HEAD["eyebrow"]}</p>
            <h2 class="amk-title" id="amk-deals-title" data-amk-split>Onze <em>koninklijke deals</em></h2>
          </div>
          <p class="amk-lead" data-amk-reveal>{lead}</p>
        </div>

        <div class="amk-deals" data-amk-stagger="0.1">{cards}
        </div>
        <p class="amk-deals__noot" data-amk-reveal>Volgens beschikbaarheid en niet combineerbaar met andere acties.</p>
        <p class="amk-deals__noot" data-amk-reveal>{DEALS_HEAD["more"]}</p>
      </div>
    </section>"""


# --------------------------------------------------------------------------
# Blog: hulpfuncties
# --------------------------------------------------------------------------
MAANDEN = ["januari", "februari", "maart", "april", "mei", "juni", "juli",
           "augustus", "september", "oktober", "november", "december"]


def nl_date(d):
    """'2026-11-02' -> '2 november 2026'."""
    y, m, dd = map(int, d.split("-"))
    return f"{dd} {MAANDEN[m - 1]} {y}"


def iso_time(d):
    """Datum als ISO 8601 om 09:00, met de tijdzone van Brussel (zomer- of wintertijd)."""
    y, m, dd = map(int, d.split("-"))

    def last_sunday(month):
        return 31 - (date(y, month, 31).weekday() + 1) % 7

    summer = (3, last_sunday(3)) <= (m, dd) < (10, last_sunday(10))
    return f"{d}T09:00:00{'+02:00' if summer else '+01:00'}"


def article_html(a):
    """Tekst van een artikel (src/blog/<slug>.html), zonder de opmerking bovenaan."""
    text = (SRC / "blog" / f"{a['slug']}.html").read_text(encoding="utf-8")
    return re.sub(r"\A\s*<!--.*?-->\s*", "", text, flags=re.S)


def word_count(a):
    text = article_html(a) + " " + " ".join(q + " " + ans for q, ans in FAQ["blog:" + a["slug"]])
    text = re.sub(r"\{\{[^}]+\}\}", " ", strip_tags(text))
    return len(re.findall(r"\w+", text))


def reading_time(a):
    """Leestijd in minuten: woorden / 200, naar boven afgerond."""
    return max(1, math.ceil(word_count(a) / 200))


def h1_html(text):
    """Het deel na de dubbele punt in goud cursief, zoals bij de andere titels."""
    head_, sep, tail = text.partition(": ")
    return f"{esc(head_)}: <em>{esc(tail)}</em>" if sep else esc(text)


def only_published(text):
    """Verwijzingen naar artikels die nog niet gepubliceerd zijn, weghalen:
    zinnen tussen <!--ALS:slug--> en <!--/ALS--> vallen weg, een gewone link
    wordt gewone tekst. Zo geeft geen enkele link een 404."""
    text = re.sub(r"<!--ALS:([a-z0-9-]+)-->(.*?)<!--/ALS-->",
                  lambda m: m.group(2) if m.group(1) in BLOG_SLUGS_LIVE else "", text, flags=re.S)
    return re.sub(r'<a [^>]*href="/blog/([a-z0-9-]+)"[^>]*>(.*?)</a>',
                  lambda m: m.group(0) if m.group(1) in BLOG_SLUGS_LIVE else m.group(2), text, flags=re.S)


def post_card(a, level=3):
    img, w, h = a["image"]
    return f"""
          <article class="amk-post amk-spot" data-amk-tilt="3">
            <div class="amk-post__img"><img src="{MEDIA}{img}" alt="" width="{w}" height="{h}" loading="lazy" decoding="async"></div>
            <div class="amk-post__body">
              <p class="amk-post__tag">{esc(a["eyebrow"])}</p>
              <h{level} class="amk-post__title"><a class="amk-post__link" href="/blog/{a["slug"]}">{esc(a["h1"])}</a></h{level}>
              <p class="amk-post__excerpt">{esc(a["excerpt"])}</p>
              <p class="amk-post__meta"><time datetime="{a["date"]}">{nl_date(a["date"])}</time><span aria-hidden="true">·</span>{reading_time(a)} min leestijd</p>
            </div>
          </article>"""


def post_list(items, extra=""):
    single = " amk-posts--single" if len(items) == 1 else ""
    cards = "".join(post_card(a) for a in items)
    return f'<div class="amk-posts{extra}{single}" data-amk-stagger="0.1">{cards}\n        </div>'


HOME_POSTS = 4


def home_posts():
    """Artikels in de blogteaser op de home: eerst de vastgezette (home_until),
    aangevuld met de nieuwste, tot HOME_POSTS; nieuwste eerst."""
    pinned = [a for a in BLOG_LIVE
              if a.get("home_until") and PUBLISH_DATE <= date.fromisoformat(a["home_until"])]
    items = pinned[:HOME_POSTS]
    items += [a for a in BLOG_LIVE if a not in items][:HOME_POSTS - len(items)]
    return [a for a in BLOG_LIVE if a in items]


def blog_teaser():
    """Home: de nieuwste artikels (niets zolang er geen artikel gepubliceerd is)."""
    if not BLOG_LIVE:
        return ""
    items = home_posts()
    extra = " amk-posts--scroll" + (" amk-posts--four" if len(items) == 4 else "")
    return f"""
    <!-- =================================================================
         UIT ONZE BLOG (nieuwste artikels, uit BLOG in build.py)
         ================================================================= -->
    <section class="amk-section amk-section--line" id="blog" aria-labelledby="amk-blog-title">
      <div class="amk-container">
        <div class="amk-head amk-head--split">
          <div data-amk-reveal>
            <p class="amk-eyebrow">Uit onze blog</p>
            <h2 class="amk-title" id="amk-blog-title" data-amk-split>Ideeën voor <em>jouw volgende bezoek</em></h2>
          </div>
          <div class="amk-posts__intro" data-amk-reveal>
            <p class="amk-lead">Tips en inspiratie rond privésauna en wellness, van een cadeau voor twee tot een nacht in je eigen wellness.</p>
            <a class="amk-link" href="/blog">Alle artikels {icon("arrow")}</a>
          </div>
        </div>
        {post_list(items, extra)}
      </div>
    </section>
"""


def blog_related(a):
    """'Lees ook' onder een artikel: alleen artikels die al gepubliceerd zijn."""
    items = [BLOG_BY_SLUG[s] for s in a["related"] if s in BLOG_SLUGS_LIVE and s != a["slug"]][:3]
    if not items:
        return ""
    return f"""
    <!-- =================================================================
         LEES OOK
         ================================================================= -->
    <section class="amk-section amk-section--line" id="lees-ook" aria-labelledby="amk-related-title">
      <div class="amk-container">
        <div class="amk-head" data-amk-reveal>
          <p class="amk-eyebrow">Lees ook</p>
          <h2 class="amk-title" id="amk-related-title" data-amk-split>Meer uit <em>onze blog</em></h2>
        </div>
        {post_list(items, " amk-posts--scroll")}
      </div>
    </section>
"""


def blog_link(kind):
    """Link naar /blog, alleen als er al een artikel gepubliceerd is."""
    if not BLOG_LIVE:
        return ""
    if kind == "footer":
        return '\n          <li><a href="/blog">Blog</a></li>'
    raise KeyError(kind)


def article_part(part, page):
    """Stukken van de artikelpagina (src/pages/blog-artikel.html)."""
    a = page["article"]
    if part == "hero":
        img, w, h = a["image"]
        return f'<img src="{MEDIA}{img}" alt="" width="{w}" height="{h}" fetchpriority="high" decoding="async">'
    if part == "eyebrow":
        return esc(a["eyebrow"])
    if part == "h1":
        return h1_html(a["h1"])
    if part == "meta":
        items = [f'{icon("calendar")}<time datetime="{a["date"]}">{nl_date(a["date"])}</time>']
        if a["modified"] != a["date"]:
            items.append(f'Bijgewerkt op <time datetime="{a["modified"]}">{nl_date(a["modified"])}</time>')
        items.append(f'{icon("clock")}{reading_time(a)} min leestijd')
        items.append(f'{icon("crown")}Door {BLOG_AUTHOR_LABEL}')
        lis = "".join(f"<li>{i}</li>" for i in items)
        return f'<ul class="amk-postmeta" aria-label="Over dit artikel">{lis}</ul>'
    if part == "body":
        return article_html(a)
    if part == "slot":
        return "{{PARTIAL:" + ("cta-" + a["slot"] if a.get("slot") else "cta") + "}}"
    raise KeyError(part)


def nav_links(current):
    items = ['<li class="amk-nav__glider" aria-hidden="true"></li>']
    for key, url, label in NAV:
        cur = ' aria-current="page"' if key == current else ""
        items.append(f'<li><a href="{url}"{cur}>{label}</a></li>')
    return "\n            ".join(items)


def menu_links(current):
    items = []
    gift = [("cadeaubon", "/cadeaubon", "Cadeaubon")] if GIFTCARD_ID else []
    blog = [("blog", "/blog", "Blog")] if BLOG_LIVE else []
    all_links = NAV + gift + blog + [("reserveren", "/reserveren", "Reserveren")]
    for i, (key, url, label) in enumerate(all_links, start=1):
        is_cur = key == current or (key == "blog" and current.startswith("blog"))
        cur = ' aria-current="page"' if is_cur else ""
        items.append(
            f'<li><a href="{url}"{cur}><span class="amk-menu__num">{i:02d}</span>{label}{icon("arrow")}</a></li>'
        )
    return "\n        ".join(items)


def breadcrumbs(page):
    if page["key"] == "home":
        return ""
    between = "".join(f'\n              <li><a href="{url}">{name}</a></li>' for name, url in page.get("crumbs", []))
    return f"""<nav class="amk-breadcrumbs" aria-label="Kruimelpad">
            <ol>
              <li><a href="/">Home</a></li>{between}
              <li><span aria-current="page">{page["crumb"]}</span></li>
            </ol>
          </nav>"""


# --------------------------------------------------------------------------
# Gestructureerde data (JSON-LD)
# --------------------------------------------------------------------------
def offers():
    out = []
    for p in WELLNESS:
        out.append({
            "@type": "Offer",
            "name": f"{p['name']} — {p['time']} privéwellness",
            "price": str(p["price"]),
            "priceCurrency": "EUR",
            "url": SITE + "/prijslijst",
            "availability": "https://schema.org/InStock",
            "itemOffered": {
                "@type": "Service",
                "name": f"Privésauna & wellness — {p['time']}",
                "description": p["desc"] + " Volledig privé: Finse sauna, stoombad, whirlpool, inloopdouche en lounge.",
            },
        })
    for p in NACHT:
        out.append({
            "@type": "Offer",
            "name": f"{p['name']} — overnachting {p['time'].replace(' – ', '-')} ({p['hours']} uur)",
            "price": str(p["price"]),
            "priceCurrency": "EUR",
            "url": SITE + "/prijslijst",
            "availability": "https://schema.org/InStock",
            "itemOffered": {
                "@type": "Service",
                "name": f"Wellness met overnachting ({p['time']})",
                "description": p["desc"] + " Met aparte slaapsuite en eigen inloopdouche.",
            },
        })
    return out


def business_node():
    return {
        "@type": "DaySpa",
        "@id": SITE + "/#business",
        "name": "Amakhosi",
        "alternateName": "Amakhosi Privésauna & Wellness",
        "description": "Luxe privésauna en wellness in Hamont-Achel met Finse sauna, stoombad, whirlpool voor twee, lounge met sfeerhaard en overnachting in een aparte slaapsuite. Helemaal privé, in warme Afrikaanse sferen.",
        "slogan": "Koninklijk genieten, helemaal privé.",
        "url": SITE + "/",
        "telephone": PHONE_TEL,
        "email": EMAIL,
        "logo": LOGO,
        "image": [MEDIA + f for f in (
            "6a84993662d4d706d4110075.jpg", "6a84993b96d2b224d38addc6.jpg",
            "6a8435f545dbba232fa5362a.jpg", "6a849936b71315ed5245054d.jpg")],
        "priceRange": "€169 – €399",
        "currenciesAccepted": "EUR",
        "address": {
            "@type": "PostalAddress",
            "streetAddress": "Watertorenstraat 64",
            "postalCode": "3930",
            "addressLocality": "Hamont-Achel",
            "addressRegion": "Limburg",
            "addressCountry": "BE",
        },
        "geo": {"@type": "GeoCoordinates", "latitude": 51.242986, "longitude": 5.533069},
        "hasMap": "https://www.google.com/maps/search/?api=1&query=Google&query_place_id=ChIJqR5gKe8qx0cRj2TNlUwF8Rg",
        "sameAs": [FACEBOOK, INSTAGRAM],
        "areaServed": [{"@type": "City", "name": c} for c in AREAS],
        "amenityFeature": [
            {"@type": "LocationFeatureSpecification", "name": n, "value": True}
            for n in ("Finse sauna", "Stoombad", "Whirlpool voor twee", "Inloopdouche",
                      "Loungebed", "Smart-tv met sfeerhaard", "Airconditioning",
                      "Aparte slaapsuite", "Gratis privéparking", "Laadpaal voor elektrische wagens")
        ],
        "hasOfferCatalog": {
            "@type": "OfferCatalog",
            "name": "Arrangementen Amakhosi",
            "itemListElement": offers(),
        },
    }


def jsonld(page):
    url = SITE + page["path"]
    img = MEDIA + page["image"][0]
    graph = [
        {
            "@type": "WebSite",
            "@id": SITE + "/#website",
            "url": SITE + "/",
            "name": "Amakhosi",
            "inLanguage": "nl-BE",
            "publisher": {"@id": SITE + "/#business"},
        },
        business_node(),
    ]
    webpage = {
        "@type": "CollectionPage" if page.get("blog_index") else "WebPage",
        "@id": url + "#webpage",
        "url": url,
        "name": page["title"],
        "description": page["description"],
        "inLanguage": "nl-BE",
        "isPartOf": {"@id": SITE + "/#website"},
        "about": {"@id": SITE + "/#business"},
        "primaryImageOfPage": {
            "@type": "ImageObject", "url": img,
            "width": page["image"][1], "height": page["image"][2],
        },
    }
    if page["key"] != "home":
        webpage["breadcrumb"] = {"@id": url + "#breadcrumb"}
        trail = [("Home", SITE + "/")] + [(n, SITE + u) for n, u in page.get("crumbs", [])] + [(page["crumb"], url)]
        graph.append({
            "@type": "BreadcrumbList",
            "@id": url + "#breadcrumb",
            "itemListElement": [
                {"@type": "ListItem", "position": i, "name": n, "item": u}
                for i, (n, u) in enumerate(trail, start=1)
            ],
        })
    graph.append(webpage)
    if page.get("blog_index"):
        webpage["mainEntity"] = {"@id": SITE + "/blog#blog"}
        graph.append({
            "@type": "Blog",
            "@id": SITE + "/blog#blog",
            "url": SITE + "/blog",
            "name": "Blog van Amakhosi",
            "inLanguage": "nl-BE",
            "publisher": {"@id": SITE + "/#business"},
            "blogPost": [
                {"@type": "BlogPosting", "@id": f"{SITE}/blog/{a['slug']}#artikel",
                 "headline": a["h1"], "url": f"{SITE}/blog/{a['slug']}",
                 "datePublished": iso_time(a["date"]), "image": MEDIA + a["image"][0]}
                for a in BLOG_LIVE
            ],
        })
    if page.get("article"):
        a = page["article"]
        graph.append({
            "@type": "BlogPosting",
            "@id": url + "#artikel",
            "headline": a["h1"],
            "description": page["description"],
            "image": {"@type": "ImageObject", "url": img,
                      "width": page["image"][1], "height": page["image"][2]},
            "datePublished": iso_time(a["date"]),
            "dateModified": iso_time(a["modified"]),
            "inLanguage": "nl-BE",
            "mainEntityOfPage": {"@id": url + "#webpage"},
            "isPartOf": {"@id": SITE + "/blog#blog"},
            "articleSection": a["eyebrow"],
            "wordCount": word_count(a),
            "author": {"@type": "Person", "name": BLOG_AUTHOR_NAME, "jobTitle": "Gastvrouw",
                       "worksFor": {"@id": SITE + "/#business"}},
            "publisher": {"@id": SITE + "/#business"},
        })
    if page.get("faq"):
        graph.append({
            "@type": "FAQPage",
            "@id": url + "#faq",
            "mainEntity": [
                {"@type": "Question", "name": strip_tags(q),
                 "acceptedAnswer": {"@type": "Answer", "text": strip_tags(a)}}
                for q, a in FAQ[page["faq"]]
            ],
        })
    if page.get("offers"):
        graph.append({
            "@type": "OfferCatalog",
            "@id": url + "#prijzen",
            "name": "Prijslijst Amakhosi",
            "itemListElement": offers(),
        })
    if page.get("gallery"):
        graph.append({
            "@type": "ImageGallery",
            "@id": url + "#galerij",
            "name": "Sfeerimpressie Amakhosi",
            "image": [
                {"@type": "ImageObject", "contentUrl": MEDIA + f, "width": w, "height": h, "caption": alt}
                for f, w, h, alt in GALLERY
            ],
        })
    data = {"@context": "https://schema.org", "@graph": graph}
    return json.dumps(data, ensure_ascii=False, indent=2)


# --------------------------------------------------------------------------
# Pagina samenstellen
# --------------------------------------------------------------------------
def head(page):
    url = SITE + page["path"]
    img, w, h = page["image"]
    img_url = MEDIA + img
    extra = ""
    if page.get("booking"):
        extra += '\n  <link rel="preconnect" href="https://api.leadconnectorhq.com">'
    og_type = "article" if page.get("article") else "website"
    og_article = ""
    if page.get("article"):
        a = page["article"]
        og_article = (f'\n  <meta property="article:published_time" content="{iso_time(a["date"])}">'
                      f'\n  <meta property="article:modified_time" content="{iso_time(a["modified"])}">'
                      f'\n  <meta property="article:section" content="{esc(a["eyebrow"])}">')
    return f"""<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">

  <!-- ===== SEO ===== -->
  <title>{esc(page["title"])}</title>
  <meta name="description" content="{esc(page["description"])}">
  <meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">
  <link rel="canonical" href="{url}">
  <link rel="alternate" hreflang="nl-BE" href="{url}">
  <link rel="alternate" hreflang="x-default" href="{url}">
  <meta name="author" content="{BLOG_AUTHOR_NAME + ', gastvrouw van Amakhosi' if page.get('article') else 'Amakhosi'}">
  <meta name="theme-color" content="#1d0000">
  <meta name="format-detection" content="telephone=yes">

  <!-- ===== Lokale SEO ===== -->
  <meta name="geo.region" content="BE-VLI">
  <meta name="geo.placename" content="Hamont-Achel">
  <meta name="geo.position" content="51.242986;5.533069">
  <meta name="ICBM" content="51.242986, 5.533069">

  <!-- ===== Open Graph / sociale media ===== -->
  <meta property="og:type" content="{og_type}">
  <meta property="og:locale" content="nl_BE">
  <meta property="og:site_name" content="Amakhosi">
  <meta property="og:title" content="{esc(page["title"])}">
  <meta property="og:description" content="{esc(page["description"])}">
  <meta property="og:url" content="{url}">
  <meta property="og:image" content="{img_url}">
  <meta property="og:image:width" content="{w}">
  <meta property="og:image:height" content="{h}">
  <meta property="og:image:alt" content="{esc(page["image_alt"])}">{og_article}
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{esc(page["title"])}">
  <meta name="twitter:description" content="{esc(page["description"])}">
  <meta name="twitter:image" content="{img_url}">

  <!-- ===== Snelheid: hoofdbeeld & lettertypes vroeg laden ===== -->
  <link rel="preload" as="image" href="{img_url}" fetchpriority="high">
  <link rel="preconnect" href="https://assets.cdn.filesafe.space" crossorigin>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>{extra}
  <link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=Playfair+Display:ital,wght@0,400;0,500;0,600;1,400;1,500&display=swap" rel="stylesheet">

  <!-- ===== Gedeelde stijlen (absoluut pad, ook voor /blog/<slug>) ===== -->
  <link rel="stylesheet" href="/styles.css">
  <link rel="icon" href="{LOGO}">
</head>"""


def render(text, page):
    """Vervangt {{...}}-placeholders in een paginabron."""
    def repl(m):
        token = m.group(1)
        if token == "M":
            return MEDIA
        if token.startswith("i:"):
            parts = token.split(":")
            return icon(parts[1], parts[2] if len(parts) > 2 else "")
        if token == "PRICES:wellness":
            return price_cards("wellness")
        if token == "PRICES:nacht":
            return price_cards("nacht")
        if token.startswith("FAQ:"):
            return faq_list(token.split(":", 1)[1])
        if token == "DURATIONS":
            return durations()
        if token == "SUMMARY:wellness":
            return summary_rows("wellness")
        if token == "SUMMARY:nacht":
            return summary_rows("nacht")
        if token == "GIFT_OPTIONS":
            return gift_options()
        if token == "GIFTCARD_ID":
            return GIFTCARD_ID
        if token == "GIFTCARD_URL":
            return GIFTCARD_URL
        if token.startswith("GIFT_LINK:"):
            return gift_link(token.split(":")[1])
        if token == "DEALS":
            return deals_section()
        if token == "BOOKING_URL":
            return html.escape(BOOKING_URL)
        if token == "RESERVE_HREF":
            if page.get("reserve_href"):
                return page["reserve_href"]
            return "#agenda" if page.get("booking") else "/reserveren"
        if token.startswith("BLOG_LINK:"):
            return blog_link(token.split(":")[1])
        if token == "BLOG_LIST":
            return post_list(BLOG_LIVE, " amk-posts--index")
        if token == "BLOG_TEASER":
            return blog_teaser()
        if token == "BLOG_RELATED":
            return blog_related(page["article"])
        if token.startswith("ARTICLE:"):
            return article_part(token.split(":", 1)[1], page)
        if token == "COMPARE":
            return compare_table()
        if token == "GALLERY":
            return gallery()
        if token == "BREADCRUMBS":
            return breadcrumbs(page)
        if token == "PHONE":
            return PHONE_DISPLAY
        if token == "TEL":
            return PHONE_TEL
        if token == "EMAIL":
            return EMAIL
        if token == "FACEBOOK":
            return FACEBOOK
        if token == "INSTAGRAM":
            return INSTAGRAM
        if token == "AREAS":
            return ", ".join(AREAS[1:-1]) + " en " + AREAS[-1]
        if token.startswith("PARTIAL:"):
            return render((SRC / "partials" / (token.split(":")[1] + ".html")).read_text(encoding="utf-8"), page)
        if token == "NAV":
            return nav_links(page["key"])
        if token == "MENU":
            return menu_links(page["key"])
        if token == "LOGO":
            return LOGO
        raise KeyError(f"Onbekende placeholder: {{{{{token}}}}} in {page['src']}")

    # Herhalen tot alle geneste placeholders (partials) vervangen zijn
    prev = None
    while prev != text:
        prev = text
        text = re.sub(r"\{\{([A-Za-z0-9_:\-]+)\}\}", repl, text)
    return text


def toc(body):
    """Inhoudsopgave uit de <h2 id="..."> koppen van een juridische pagina."""
    items = re.findall(r'<h2 id="([^"]+)">(.*?)</h2>', body)
    return "".join(f'\n            <li><a href="#{i}">{t}</a></li>' for i, t in items)


def build_page(page):
    body = (SRC / "pages" / page["src"]).read_text(encoding="utf-8")
    if "{{TOC}}" in body:
        body = body.replace("{{TOC}}", toc(body))
    booking_script = ""
    if page.get("booking"):
        booking_script = '\n  <script src="https://link.msgsndr.com/js/form_embed.js"></script>'
    doc = f"""<!DOCTYPE html>
<html lang="nl-BE">
{head(page)}
<body>

<!-- =====================================================================
     START GHL-PLAKBLOK
     Alles tussen START en EINDE plak je in één "Custom JS/HTML"-element
     in GoHighLevel (volle breedte, zonder padding). Zie README.md.
     Gegenereerd door build.py — pas src/ aan en bouw opnieuw.
     ===================================================================== -->
<div class="amk">

{{{{PARTIAL:sprite}}}}

  <a class="amk-skip" href="#amk-main">Naar de inhoud</a>

{{{{PARTIAL:header}}}}

  <main id="amk-main">
{body}
  </main>

{{{{PARTIAL:footer}}}}

{{{{PARTIAL:mobilebar}}}}

  <!-- Gestructureerde data voor Google -->
  <script type="application/ld+json">
{jsonld(page)}
  </script>{booking_script}

</div>
<!-- =====================================================================
     EINDE GHL-PLAKBLOK
     ===================================================================== -->

<script src="/scripts.js" defer></script>
</body>
</html>
"""
    out = only_published(render(doc, page))
    target = ROOT / page["out"]
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(out, encoding="utf-8")
    return out


def sitemap_lastmod(p):
    lastmod = p.get("lastmod", "2026-10-07")
    if p["key"] == "home" and BLOG_LIVE:
        # De home toont de nieuwste artikels: wijzigt bij elk nieuw artikel.
        lastmod = max(lastmod, BLOG_LIVE[0]["date"])
    return lastmod


def build_sitemap():
    urls = "".join(
        f"""
  <url>
    <loc>{SITE}{p["path"]}</loc>
    <lastmod>{sitemap_lastmod(p)}</lastmod>
    <changefreq>{p.get("changefreq") or ("weekly" if p["key"] in ("home", "deals") else ("yearly" if p.get("legal") else "monthly"))}</changefreq>
    <priority>{p.get("priority") or ("1.0" if p["key"] == "home" else ("0.3" if p.get("legal") else "0.8"))}</priority>
    <image:image><image:loc>{MEDIA}{p["image"][0]}</image:loc></image:image>
  </url>"""
        for p in PAGES
    )
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">{urls}
</urlset>
"""
    (ROOT / "sitemap.xml").write_text(xml, encoding="utf-8")


# Oude adressen (WordPress- en GHL-site) die nu een 404 gaven, met de best
# passende huidige pagina. Gevonden via de Wayback Machine (CDX-API voor
# amakhosi.be/* en www.amakhosi.be/*) en de bekende adressen; elk adres op
# 2026-10-11 live getest (404). Elk adres krijgt een regel met en zonder
# slash op het einde. Doel is altijd een pagina uit de sitemap (geen ketens).
OLD_REDIRECTS = [
    ("/home", "/"),
    ("/privesauna-hamont-achel", "/"),
    ("/privesauna-lommel", "/"),
    ("/privesauna-bocholt-belgie", "/"),
    ("/hello-world", "/"),
    ("/category/uncategorized", "/"),
    ("/index.php", "/"),
    ("/impressie", "/privesauna-wellness-impressie"),
    ("/sfeer-impressie", "/privesauna-wellness-impressie"),
    ("/index.php/arrangementen", "/arrangementen"),
    ("/index.php/prijslijst", "/prijslijst"),
    ("/cookiebeleid-eu", "/privacybeleid"),
    # SEO-plan A3 (12/11/2026): nog 404 volgens Search Console en curl.
    # Lommel, Bocholt en de algemene plaatsadressen voorlopig naar de home.
    # Komt er een plaatspagina (A13, bv. /privesauna-pelt-lommel), laat dan
    # /spa-lommel, /privesauna-lommel en /spa-bocholt-belgie (en
    # /privesauna-bocholt-belgie hierboven) daarheen wijzen.
    ("/spa-lommel", "/"),
    ("/spa-bocholt-belgie", "/"),
    ("/spa-hamont-achel", "/"),
    ("/spa-belgie", "/"),
    ("/spa-vlaanderen", "/"),
    ("/spa-budel", "/"),
    ("/privesauna-belgie", "/"),
    ("/privesauna-vlaanderen", "/"),
    ("/privesauna-budel", "/"),
    ("/index.php/reserveren", "/reserveren"),
    ("/index.php/impressie", "/privesauna-wellness-impressie"),
    ("/privacy-verklaring", "/privacybeleid"),
]


def build_redirects():
    """_redirects voor Cloudflare, alles permanent (301) en zonder ketens.

    1. /pagina/ -> /pagina. Zonder deze regels stuurt Cloudflare de
       slash-variant zelf door met een tijdelijke 307.
    2. /pagina.html (en /index, /index.html) -> het adres zonder .html.
       Cloudflare doet dat anders zelf met een 307.
    3. Oude adressen van de vorige sites -> de best passende pagina.

    Alleen statische regels (limiet Cloudflare: 2.000 statische, 100
    dynamische). Geen doel is zelf een bron, dus geen lussen of ketens.
    """
    lines = [
        "# Gegenereerd door build.py: niet met de hand aanpassen.",
        "# 1. Adressen met een slash op het einde permanent (301) naar het adres zonder slash.",
    ]
    for p in PAGES:
        if p["path"] != "/":
            lines.append(f'{p["path"]}/ {p["path"]} 301')
    lines.append("# 2. Adressen met .html permanent (301) naar het adres zonder .html.")
    lines.append("/index / 301")
    for p in PAGES:
        lines.append(f'/{p["out"]} {p["path"]} 301')
    lines.append("# 3. Oude adressen (WordPress/GHL) naar de best passende huidige pagina.")
    for old, new in OLD_REDIRECTS:
        lines.append(f"{old} {new} 301")
        lines.append(f"{old}/ {new} 301")

    # Controle: geen doel mag zelf een bron zijn (ketens of lussen).
    rules = [l.split() for l in lines if not l.startswith("#")]
    sources = {r[0] for r in rules}
    for src, dst, _ in rules:
        assert dst not in sources, f"redirectketen: {src} -> {dst}"
    assert len(sources) == len(rules), "dubbele bron in _redirects"
    (ROOT / "_redirects").write_text("\n".join(lines) + "\n", encoding="utf-8")


def clean_blog():
    """Blogpagina's die (nog) niet gepubliceerd zijn weghalen, bv. na een
    build met --voorbeeld, zodat ze niet per ongeluk online komen."""
    for a in BLOG:
        f = ROOT / "blog" / f"{a['slug']}.html"
        if a["slug"] not in BLOG_SLUGS_LIVE and f.exists():
            f.unlink()
            print("verwijderd (nog niet gepubliceerd):", f.relative_to(ROOT).as_posix())
    if not BLOG_LIVE and (ROOT / "blog.html").exists():
        (ROOT / "blog.html").unlink()
        print("verwijderd (nog geen artikels): blog.html")
    if (ROOT / "blog").is_dir() and not any((ROOT / "blog").iterdir()):
        # OneDrive zet een lege map soms op alleen-lezen: dan blijft de lege
        # map staan (onschuldig) in plaats van dat de build hier stopt vóór
        # sitemap.xml en _redirects opnieuw gebouwd zijn.
        try:
            (ROOT / "blog").rmdir()
        except OSError as e:
            print("let op: lege map blog/ niet verwijderd:", e)


if __name__ == "__main__":
    for p in PAGES:
        build_page(p)
        print("gebouwd:", p["out"])
    clean_blog()
    build_sitemap()
    print("gebouwd: sitemap.xml")
    build_redirects()
    print("gebouwd: _redirects")
    later = [a for a in BLOG if a["slug"] not in BLOG_SLUGS_LIVE]
    print(f"blog: {len(BLOG_LIVE)} gepubliceerd" + (", later: " + ", ".join(
        f'{a["slug"]} ({a["date"]})' for a in later) if later else ""))
    if not DEALS_LIVE:
        print("LET OP: geen lopende deals meer in DEALS: /koninklijke-deals toont geen dealkaarten.")
    if PUBLISH_DATE != date.today():
        print("LET OP: gebouwd met --voorbeeld of --datum, alleen om na te kijken. "
              "Bouw opnieuw zonder optie voor je publiceert.")
