#!/usr/bin/env python3
"""
Bouwt de Amakhosi-pagina's uit src/ naar de hoofdmap.

    python3 build.py

- src/partials/   gedeelde stukken (iconen, header, footer, mobiele balk)
- src/pages/      inhoud per pagina (alles binnen <main>)

Hier staan ook de gedeelde gegevens (navigatie, prijzen, FAQ's, SEO per
pagina), zodat HTML, prijzen en gestructureerde data (JSON-LD) altijd
overeenkomen. Alleen de standaardbibliotheek van Python is nodig.
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"

SITE = "https://amakhosi.be"
MEDIA = "https://assets.cdn.filesafe.space/8mwRjKt9TFTVWGHrrl0R/media/"
LOGO = MEDIA + "6a8428d4acc26e1326c1092e.png"
PHONE_DISPLAY = "+32 (0)469 217 550"
PHONE_TEL = "+32469217550"
EMAIL = "info@amakhosi.be"

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
         desc="Uitgebreid genieten, zonder op de klok te kijken.", badge="Meeste tijd voor u"),
]
NACHT = [
    dict(name="Kom overnachten", price=335, time="20:00 – 10:00", hours=14,
         desc="Overnachten met onbeperkt toegang tot de wellness."),
    dict(name="Slaap lekker uit", price=399, time="20:00 – 12:00", hours=16,
         desc="Uitslapen en nagenieten tot 12:00, zonder wekker.", badge="Uitslapen tot 12 u"),
]

# Directe link naar de online agenda (volledig scherm, handig op telefoons)
BOOKING_URL = "https://api.leadconnectorhq.com/booking/amakhosi?showHeader=true"
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
# Veelgestelde vragen (HTML + FAQPage-schema uit dezelfde bron)
# --------------------------------------------------------------------------
FAQ = {
    "home": [
        ("Is de wellness echt volledig privé?",
         "Ja. Tijdens uw arrangement heeft u de volledige wellness voor uzelf: de Finse sauna, het stoombad, de whirlpool, de inloopdouche en de lounge. Er zijn geen gedeelde ruimtes en geen andere gasten."),
        ("Hoe lang kan ik blijven?",
         'U kiest voor 3, 4, 5 of 6 uur wellness, of voor een overnachting van 20:00 tot 10:00 (14 uur) of van 20:00 tot 12:00 (16 uur). Bekijk alle prijzen op de <a href="/prijslijst">prijslijst</a>.'),
        ("Kan ik eten en drinken bijboeken?",
         'Zeker. Denk aan een luxe tapas-, kaas- of fruitplank, snacks, champagne, prosecco of Afrikaanse wijn, en bij een overnachting een ontbijt voor twee. Alle gerechten kunnen halal of vegetarisch bereid worden. Bekijk alle <a href="/arrangementen">extra\'s</a>.'),
        ("Wat is inbegrepen?",
         "Gratis frisdrank, koffie en thee tijdens uw verblijf, een smart-tv met sfeerhaard, airconditioning en een gratis privéparkeerplaats met laadpaal. Bij een overnachting krijgt u een aparte slaapsuite met eigen inloopdouche."),
        ("Wat zijn de openingstijden?",
         'Amakhosi werkt op afspraak. Kies uw moment in de <a href="/reserveren">online agenda</a> of bel ons voor de mogelijkheden.'),
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
         'Kies uw arrangement, datum en tijdstip in de <a href="/reserveren">online agenda</a>. Liever persoonlijk? Bel ons op ' + PHONE_DISPLAY + "."),
    ],
    "arrangementen": [
        ("Moet ik planken vooraf bestellen?",
         "De luxe tapasplank en de fruitplank bestelt u minstens één dag vooraf. Toch last minute zin in iets lekkers? Bel ons even, dan bekijken we wat mogelijk is."),
        ("Zijn er halal of vegetarische opties?",
         "Ja. Alle gerechten kunnen halal of vegetarisch bereid worden. Geef het gewoon door bij uw reservatie."),
        ("Kan ik ontbijt bijboeken?",
         "Het ontbijt voor twee personen (€ 38) is extra te boeken bij een overnachting: verse broodjes, croissants, een eitje naar keuze, vleeswaren, kaas en zoet beleg, vers fruit, yoghurt, een Afrikaanse muffin en verse jus d'orange."),
        ("Kan de champagne koud klaarstaan bij aankomst?",
         "Ja. De gekoelde fles champagne kan op verzoek koud geserveerd worden wanneer u aankomt."),
    ],
    "reserveren": [
        ("Hoe werkt online reserveren?",
         "Kies in de agenda uw arrangement, eventuele extra's, de datum en het tijdstip, en vul uw gegevens in. Lukt het op uw telefoon niet goed? Open de agenda dan op volledig scherm met de knop boven de agenda, of bel ons."),
        ("Ik heb een Nederlands telefoonnummer. Wat vul ik in?",
         "Typ uw nummer met landcode, bijvoorbeeld +31 6 12345678. Een Belgisch nummer mag gewoon zoals u het kent, bijvoorbeeld 0470 12 34 56."),
        ("Kan ik ook telefonisch reserveren?",
         "Natuurlijk. Bel ons op " + PHONE_DISPLAY + " of mail naar " + EMAIL + "."),
        ("Wanneer is Amakhosi open?",
         "Amakhosi werkt op afspraak. In de online agenda ziet u welke momenten nog vrij zijn."),
        ("Waar kan ik parkeren?",
         "U parkeert gratis op uw eigen privéparkeerplaats, direct bij de ingang. Er is ook een laadpaal voor elektrische wagens."),
    ],
}

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
        description="Stel uw wellnessmoment samen: 3, 4 of 5 uur privéwellness of een overnachting, aan te vullen met een romantisch pakket, ontbijt, champagne of luxe tapasplanken.",
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
        description="Ontdek de Koninklijke deals van Amakhosi: tijdelijke promoties en acties die u het hele jaar door kunt benutten voor uw privésauna en wellness in Hamont-Achel.",
        image=("6a846eb24aaffc55cd792746.jpg", 1024, 784),
        image_alt="Loungebed versierd met een hart van rozenblaadjes",
    ),
    dict(
        key="reserveren", src="reserveren.html", out="reserveren.html",
        path="/reserveren", crumb="Reserveren",
        title="Reserveer uw privésauna online | Amakhosi Hamont-Achel",
        description="Reserveer online uw privésauna en wellness bij Amakhosi in Hamont-Achel. Kies uw arrangement, datum en tijdstip, of bel ons op +32 (0)469 217 550.",
        image=("6a8435f545dbba232fa5362a.jpg", 2048, 1365),
        image_alt="Finse sauna met sfeerverlichting",
        faq="reserveren",
        booking=True,
    ),
]

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


def nav_links(current):
    items = ['<li class="amk-nav__glider" aria-hidden="true"></li>']
    for key, url, label in NAV:
        cur = ' aria-current="page"' if key == current else ""
        items.append(f'<li><a href="{url}"{cur}>{label}</a></li>')
    return "\n            ".join(items)


def menu_links(current):
    items = []
    all_links = NAV + [("reserveren", "/reserveren", "Reserveren")]
    for i, (key, url, label) in enumerate(all_links, start=1):
        cur = ' aria-current="page"' if key == current else ""
        items.append(
            f'<li><a href="{url}"{cur}><span class="amk-menu__num">{i:02d}</span>{label}{icon("arrow")}</a></li>'
        )
    return "\n        ".join(items)


def breadcrumbs(page):
    if page["key"] == "home":
        return ""
    return f"""<nav class="amk-breadcrumbs" aria-label="Kruimelpad">
            <ol>
              <li><a href="/">Home</a></li>
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
        "@type": "WebPage",
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
        graph.append({
            "@type": "BreadcrumbList",
            "@id": url + "#breadcrumb",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
                {"@type": "ListItem", "position": 2, "name": page["crumb"], "item": url},
            ],
        })
    graph.append(webpage)
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
  <meta name="author" content="Amakhosi">
  <meta name="theme-color" content="#1d0000">
  <meta name="format-detection" content="telephone=yes">

  <!-- ===== Lokale SEO ===== -->
  <meta name="geo.region" content="BE-VLI">
  <meta name="geo.placename" content="Hamont-Achel">
  <meta name="geo.position" content="51.242986;5.533069">
  <meta name="ICBM" content="51.242986, 5.533069">

  <!-- ===== Open Graph / sociale media ===== -->
  <meta property="og:type" content="website">
  <meta property="og:locale" content="nl_BE">
  <meta property="og:site_name" content="Amakhosi">
  <meta property="og:title" content="{esc(page["title"])}">
  <meta property="og:description" content="{esc(page["description"])}">
  <meta property="og:url" content="{url}">
  <meta property="og:image" content="{img_url}">
  <meta property="og:image:width" content="{w}">
  <meta property="og:image:height" content="{h}">
  <meta property="og:image:alt" content="{esc(page["image_alt"])}">
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

  <!-- ===== Gedeelde stijlen ===== -->
  <link rel="stylesheet" href="styles.css">
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
            return faq_list(token.split(":")[1])
        if token == "DURATIONS":
            return durations()
        if token == "SUMMARY:wellness":
            return summary_rows("wellness")
        if token == "SUMMARY:nacht":
            return summary_rows("nacht")
        if token == "BOOKING_URL":
            return html.escape(BOOKING_URL)
        if token == "RESERVE_HREF":
            return "#agenda" if page.get("booking") else "/reserveren"
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


def build_page(page):
    body = (SRC / "pages" / page["src"]).read_text(encoding="utf-8")
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

<script src="scripts.js" defer></script>
</body>
</html>
"""
    out = render(doc, page)
    (ROOT / page["out"]).write_text(out, encoding="utf-8")
    return out


def build_sitemap():
    urls = "".join(
        f"""
  <url>
    <loc>{SITE}{p["path"]}</loc>
    <lastmod>2026-10-07</lastmod>
    <changefreq>{"weekly" if p["key"] in ("home", "deals") else "monthly"}</changefreq>
    <priority>{"1.0" if p["key"] == "home" else "0.8"}</priority>
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


if __name__ == "__main__":
    for p in PAGES:
        build_page(p)
        print("gebouwd:", p["out"])
    build_sitemap()
    print("gebouwd: sitemap.xml")
