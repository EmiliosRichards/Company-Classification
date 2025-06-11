import csv
import re

def extract_website_from_text(text_block):
    """
    Extracts a website URL from a block of text.
    Prioritizes explicit URLs (http/https/www) and markdown links.
    Also looks for context like "Website: domain.com".
    """
    # Priority 1: Markdown links like [Text](URL)
    md_link_match = re.search(r'\[[^\]]+\]\((https?://[^\s\)]+|www\.[^\s\)]+)\)', text_block, re.IGNORECASE)
    if md_link_match:
        return md_link_match.group(1)

    # Priority 2: Explicit http(s):// or www. URLs
    regex_priority = r'\b(https?://[^\s/$.?#].[^\s()<>"]*|www\.[^\s/$.?#].[^\s()<>"]*)'
    match = re.search(regex_priority, text_block, re.IGNORECASE)
    if match:
        url = match.group(0)
        # Remove trailing punctuation if not part of the URL
        if url.endswith(('.', ',', ')', ';')):
            url = url[:-1]
        return url

    # Priority 3: Lines with "Website:", "Homepage:", etc.
    lines = text_block.split('\n')
    for line in lines:
        m = re.search(r'(?:Website|Homepage|Webseite|Web)\s*:\s*(https?://[^\s]+|[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', line, re.IGNORECASE)
        if m:
            url = m.group(1)
            if not re.match(r'^https?://', url, re.IGNORECASE):
                url = 'http://' + url
            return url
    
    # Priority 4: Try to find domain names in the first few lines if they look like companyname.tld
    # This is more heuristic.
    first_few_lines = "\n".join(lines[:3]) # Check company name line and a bit after
    # Look for domain.tld not part of an email, often found near company name
    # Example: "CompanyName (domain.com)" or "domain.com" on its own line
    domain_pattern = r'(?<![\w@])([a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.(?:com|de|io|org|net|gmbh|info|eu|biz|ch|at|GmbH|COM|DE|IO|NET|ORG|INFO|EU|BIZ|CH|AT))(?![.\w])'
    domain_match = re.search(domain_pattern, first_few_lines)
    if domain_match:
        url = domain_match.group(1)
        if not re.match(r'^https?://', url, re.IGNORECASE):
            url = 'http://' + url
        return url

    return "N/A"

def extract_services_from_block(block_text):
    """
    Extracts product/service descriptions from a text block.
    Searches for keywords like "Dienstleistungen:", "Produkte:", etc.
    Uses refined end markers and filters to avoid premature truncation.
    """
    service_keywords = [
        "Dienstleistungen:", "Produkte und Dienstleistungen:", "Services:", "Leistungen:", 
        "Portfolio:", "Angebot:", "Produkte:", "Lösungen:", "Was wir anbieten:",
        "Unsere Leistungen im Überblick:", "Leistungsspektrum:",
        "Produkt:", "Hauptmerkmale:", "Hauptfunktionen:", "Kernfunktionen:",
        "Dienstleistungen & Produkte:", "Leistungen von Relias:" # Specific case, but general "Leistungen:" should catch it
    ]
    service_items_list = [] 
    in_service_section = False
    
    strong_end_markers = [
        "Tel:", "Mobil:", "Fax:", "Ansprechpartner:", "Geschäftsführer:", "Kontakt:", 
        "Website:", "Webseite:", "Adresse:", "Standort:", "E-Mail:", "Telefon:", "Homepage:",
        "Mehr unter:", "Quelle:", "Notizen:", "Anmerkungen:", "Fazit:", "Bewertung:", "Status:",
        "Kategorie:", "Schlagworte:", "Tags:", "Verknüpfungen:", "Siehe auch:", 
        "Ähnliche Unternehmen:", "Kooperationen:", "Partnerschaften:", "Referenzen:", 
        "Kunden:", "Projekte:", "Fallstudien:", "Erfolge:", "Auszeichnungen:", "Zertifizierungen:", 
        "Mitgliedschaften:", "Presse:", "Veröffentlichungen:", "News:", "Blog:", "Social Media:",
        "Impressum", "Datenschutz", "AGB", "Nutzungsbedingungen", "Haftungsausschluss", 
        "Copyright", "©", "Alle Rechte vorbehalten", "Stand:", "Version:", "Letzte Aktualisierung:",
        "Gegründet:", "Mitarbeiter:", "Umsatz:", "Branche:", "Sektor:", "Industrie:", "Nische:", 
        "Zielgruppe:", "Kundenfokus:", "Marktsegment:", "Wettbewerber:", "USP:", 
        "Alleinstellungsmerkmal:", "Vision:", "Mission:", "Werte:", "Philosophie:", "Geschichte:", 
        "Über uns", "Team:", "Karriere:", "Jobs:", "Stellenangebote:", "Investoren:", "Finanzierung:",
        "Vorteile:", "Nutzen:", "Zielsetzung:", "Herausforderungen:", "Lösungsansatz:",
        "Technologie-Stack:", "Methodik:", "Prozess:", "Ergebnisse:", "Nächste Schritte:",
        "### ", 
        "---", "\n* * *\n", "\n===", 
        "Standorte und Beteiligungen", 
        "________________________________________",
        "Unternehmensphilosophie:", # Added as strong end marker
        "Kontaktinformationen:",   # Added as strong end marker
        "Anwendungsfall – Kundenansprache:", # Added
        r"Warum [A-Za-zÄÖÜäöüß\s]+?:" # General "Warum Xyz?:"
    ]

    filter_out_patterns = [
        re.compile(r"^\s*\(.+\)\s*?\s*$"),
        re.compile(r"^\s*🚀?\s*[\"“»„].*[\"”«“]\s*$"), 
        re.compile(r"^\s*AL\s*\d+\s*$"), 
        re.compile(r"^\s*\d{5}\s+[A-Za-zÄÖÜäöüß\s.-]+$", re.IGNORECASE), 
        re.compile(r"^\s*[A-Za-zÄÖÜäöüß.\s-]+straße\s*\d+.*$", re.IGNORECASE), 
        re.compile(r"^\s*(Weitere Informationen|Über das Unternehmen|Über [A-Za-z\s]+ GmbH):?\s*$", re.IGNORECASE),
        re.compile(r"^\s*💰\s*"), 
        re.compile(r"^\s*Mehr Infos unter:", re.IGNORECASE),
        re.compile(r"^\s*Quelle:", re.IGNORECASE),
        re.compile(r"^\s*Tel\.?\s*:\s*.+", re.IGNORECASE), 
        re.compile(r"^\s*E-Mail\s*:\s*.+", re.IGNORECASE), 
        re.compile(r"^\s*Mobil\s*:\s*.+", re.IGNORECASE), 
        re.compile(r"^\s*Fax\s*:\s*.+", re.IGNORECASE),   
        re.compile(r"^\s*Anschrift\s*:", re.IGNORECASE),
        re.compile(r"^\s*Adresse\s*:\s*.+", re.IGNORECASE), 
        re.compile(r"^\s*Website\s*:\s*.+", re.IGNORECASE), 
        re.compile(r"^\s*Homepage\s*:\s*.+", re.IGNORECASE),
        re.compile(r"^\s*\(?mailto:.*?\)?$", re.IGNORECASE), 
        re.compile(r"^\s*Standorte und Beteiligungen\s*:\s*$", re.IGNORECASE), 
        re.compile(r"^\s*schrumpfenden Markt", re.IGNORECASE), 
        # Unternehmensphilosophie and Kontaktinformationen are now strong_end_markers
        re.compile(r"^\s*(📌|🚀|💡|✔|📍|📞|📧|🌐)\s*.*$", re.IGNORECASE), 
        re.compile(r"^\s*Haben Sie kurz drei Minuten.*$", re.IGNORECASE),
        # Anwendungsfall is now a strong_end_marker
        re.compile(r"^\s*Vorteile für Ihr Unternehmen:?", re.IGNORECASE),
        re.compile(r"^\s*Vorteile für Unternehmen & Kanzleien:?", re.IGNORECASE),
        re.compile(r"^\s*Unsere Vorteile für Ihr Unternehmen:?", re.IGNORECASE),
        # "Warum Xyz?:" is now a strong_end_marker
        re.compile(r"^\s*Für weitere Informationen.*$", re.IGNORECASE),
        re.compile(r"^\s*Kontakt & Demo\s*$", re.IGNORECASE),
        re.compile(r"^\s*Zertifizierungen und Auszeichnungen:?", re.IGNORECASE),
        re.compile(r"^\s*Technologie & Medizinischer Nutzen:?", re.IGNORECASE),
        re.compile(r"^\s*Medizinisches Personal finden\s*–\s*Schnell, einfach & flexibel:?", re.IGNORECASE),
        re.compile(r"^\s*Jetzt auch für ambulante Pflegedienste.*$", re.IGNORECASE),
        re.compile(r"^\s*Erfolgreiche Kunden wie .+", re.IGNORECASE),
        re.compile(r"^\s*Bis zu \d+% bessere Ausschreibungsergebnisse.*$", re.IGNORECASE),
        re.compile(r"^\s*(Mehr Reichweite|Zeitersparnis|Geführte Unterstützung):", re.IGNORECASE),
        re.compile(r"^\s*Best Practices für optimale Ergebnisse:?", re.IGNORECASE),
        re.compile(r"^\s*Mit ihrer umfassenden Expertise.*$", re.IGNORECASE),
        re.compile(r"^\s*In enger Zusammenarbeit mit der Wirtschaft.*$", re.IGNORECASE),
        re.compile(r"^\s*Cloud Ahoi verfolgt einen ganzheitlichen Ansatz.*$", re.IGNORECASE),
        re.compile(r"^\s*Unser umfassendes Netzwerk und unsere Expertise.*$", re.IGNORECASE),
        re.compile(r"^\s*Medlytics verfolgt die Mission.*$", re.IGNORECASE),
        re.compile(r"^\s*Cannaleo setzt neue Maßstäbe.*$", re.IGNORECASE),
        re.compile(r"^\s*MEDWING revolutioniert die Personalvermittlung.*$", re.IGNORECASE),
        re.compile(r"^\s*Profitbl kombiniert Beratung, Technologie.*$", re.IGNORECASE),
        re.compile(r"^\s*Die GVS Group bietet neben hochwertigen Produkten auch umfassende Serviceleistungen:?", re.IGNORECASE),
        re.compile(r"^\s*Egal, ob Pflegekräfte gesucht werden.*$", re.IGNORECASE),
        re.compile(r"^\s*Mit Notara sparen Notariate.*$", re.IGNORECASE),
        re.compile(r"^\s*Mit seiner Expertise hat Erik Kaatz.*$", re.IGNORECASE),
        re.compile(r"^\s*Mit fundierter Expertise und einem praxisorientierten Ansatz.*$", re.IGNORECASE),
        re.compile(r"^\s*Prozessoptimierung für Kanzleien:?", re.IGNORECASE),
        re.compile(r"^\s*Spezialisiert auf Steuerkanzleien:", re.IGNORECASE),
        re.compile(r"^\s*DATEV-Experten:", re.IGNORECASE),
        re.compile(r"^\s*Reduzierung von Verwaltungsaufwand:", re.IGNORECASE),
        re.compile(r"^\s*Optimierung der Mandantenkommunikation:", re.IGNORECASE),
        re.compile(r"^\s*Hochwertige Schokoladen für Hotels & Gastronomie:", re.IGNORECASE),
        re.compile(r"^\s*Als Willkommensgruß für Gäste.*$", re.IGNORECASE),
        re.compile(r"^\s*Als kleine Aufmerksamkeit oder Turndown-Service.*$", re.IGNORECASE),
        re.compile(r"^\s*Als exklusives Geschenkangebot.*$", re.IGNORECASE),
        re.compile(r"^\s*Als Highlight für das Restaurant.*$", re.IGNORECASE),
        re.compile(r"^\s*Kurzum: Coppeneur verleiht Hotels.*$", re.IGNORECASE),
        re.compile(r"^\s*Handwerkliche Herstellung mit höchsten Qualitätsansprüchen.*$", re.IGNORECASE),
        re.compile(r"^\s*Nachhaltige Kakao-Beschaffung & faire Produktionsstandards.*$", re.IGNORECASE),
        re.compile(r"^\s*Individualisierbare Genussprodukte.*$", re.IGNORECASE),
        re.compile(r"^\s*Erfahrung & Leidenschaft für feinste Schokoladenkunst.*$", re.IGNORECASE),
        re.compile(r"^\s*Juristische Expertise:", re.IGNORECASE),
        re.compile(r"^\s*Nachweisbare Erfolge:", re.IGNORECASE),
        re.compile(r"^\s*Kundenorientierter Ansatz:", re.IGNORECASE),
        re.compile(r"^\s*Vorteile der Zusammenarbeit mit vemeto:?", re.IGNORECASE),
        re.compile(r"^\s*Zertifizierte Beratungsqualität:", re.IGNORECASE),
        re.compile(r"^\s*Staatliche Fördermöglichkeiten:", re.IGNORECASE),
        re.compile(r"^\s*Langfristige Partnerschaften:", re.IGNORECASE),
        re.compile(r"^\s*Franchise-Möglichkeiten:", re.IGNORECASE),
        re.compile(r"^\s*Mit vemeto können Unternehmen und Steuerberater.*$", re.IGNORECASE),
        re.compile(r"^\s*Für ein unverbindliches Erstgespräch.*$", re.IGNORECASE),
        re.compile(r"^\s*Globale Präsenz:", re.IGNORECASE),
        re.compile(r"^\s*DEVIM legt großen Wert auf eine enge Zusammenarbeit.*$", re.IGNORECASE),
        re.compile(r"^\s*Für weitere Informationen oder zur Vereinbarung eines persönlichen Gesprächs.*$", re.IGNORECASE),
        re.compile(r"^\s*visitronic legt großen Wert auf Fairness und Vertrauen.*$", re.IGNORECASE),
        re.compile(r"^\s*Exzellenzbetrieb Deutscher Mittelstand.*$", re.IGNORECASE),
        re.compile(r"^\s*TOP 100 Innovator \d{4}.*$", re.IGNORECASE),
        re.compile(r"^\s*ISO \d+:\d+.*$", re.IGNORECASE) 
    ]
    
    current_services_buffer = []
    lines = block_text.split('\n')
    service_section_started_keyword_line_index = -1

    for line_num, line in enumerate(lines):
        stripped_line = line.strip()

        if not in_service_section:
            for keyword in service_keywords:
                if keyword.lower() in stripped_line.lower(): 
                    in_service_section = True
                    service_section_started_keyword_line_index = line_num
                    potential_service_on_keyword_line = stripped_line.split(keyword, 1)[-1].strip() 
                    if not potential_service_on_keyword_line: 
                         potential_service_on_keyword_line = re.split(keyword, stripped_line, flags=re.IGNORECASE, maxsplit=1)[-1].strip()

                    if potential_service_on_keyword_line and potential_service_on_keyword_line not in ["-", "–", ":", "•", "*"]:
                        if not (len(potential_service_on_keyword_line) < 5 and potential_service_on_keyword_line[-1] in ["-", "–", ":"]):
                            current_services_buffer.append(potential_service_on_keyword_line.lstrip(":-•* "))
                    break
            continue

        if in_service_section:
            line_lower = stripped_line.lower()
            found_strong_marker = False
            for marker_raw in strong_end_markers:
                marker = marker_raw.lower().strip()
                if not marker: continue
                # Check if the line *is* the marker or *starts with* the marker or contains it as a section
                if line_lower == marker or line_lower.startswith(marker) or (marker.endswith(":") and marker in line_lower):
                    # Specific check for "Warum Xyz?:" to avoid premature ending if it's part of a service description
                    if marker.startswith("warum ") and marker.endswith("?:") and len(line_lower) > len(marker) + 5: # if more text follows
                        continue
                    found_strong_marker = True
                    break
            if found_strong_marker:
                break 

            if not stripped_line and line_num > 0 and not lines[line_num-1].strip() \
               and line_num > service_section_started_keyword_line_index +1 : 
                break 
            
            is_filtered_out = False
            for pattern in filter_out_patterns:
                if pattern.search(stripped_line): 
                    is_filtered_out = True
                    break
            if is_filtered_out:
                continue
            
            # Heuristic for general section headers like "Some Section:"
            if re.match(r"^[A-ZÄÖÜ][a-zäöüß]+([\s\-][A-ZÄÖÜa-zäöüß]+){0,4}:$", stripped_line) and \
               line_num > service_section_started_keyword_line_index:
                # Avoid stopping for very long lines that happen to end with a colon
                if len(stripped_line) < 60 : 
                    # Check if this header is a known service keyword itself to avoid stopping service list
                    is_also_service_keyword = False
                    for skeyword in service_keywords:
                        if skeyword.lower() == stripped_line.lower():
                            is_also_service_keyword = True
                            break
                    if not is_also_service_keyword:
                        break


            if stripped_line and stripped_line not in ["-", "–", "•", "*"] and not stripped_line.startswith("---"):
                cleaned_line = re.sub(r"^\s*[-–•*o]\s*", "", stripped_line) 
                if cleaned_line:
                    current_services_buffer.append(cleaned_line)
    
    cleaned_buffer = []
    company_artifact_pattern = re.compile(
        r"(.*?)(;\s*(Cloud Ahoi|Smart2Success|FirmenEintrag|mscompanysolutions\.com|hospichef\.com|ProfitBL|BlueCrest Parcels|BlueCrest Inc\.|BlueCrest|Devim|Vemeto|Vemeto Franchise|visitronic\.de|pnp-media\.de|corominas-consulting\.de|dimarketing-salesconsulting\.de|tenderwise\.io|GVS EG|Medlytics GmbH|Cannaleo Digital GmbH|MEDWING GmbH|KSR Sales Group GmbH|AVIA CONCEPT|Coppeneur|PNP Media|Alim Inkasso|BlueCrest Inc|DEVIM|BSU-Akademie|SitePlan GmbH|Novaheal|Carl Goetz|Schlütersche|Elvari|Rodias|SPiE Rodias|Munich Startup|MyBestes|HR Lab|Steuerköpfe|Steuerköpfe VIP|Tap To Tie)\s*)$", 
        re.IGNORECASE
    )
    for service_line in current_services_buffer:
        original_line = service_line 
        while True: 
            match = company_artifact_pattern.match(service_line)
            if match:
                service_line = match.group(1).strip() 
                if not service_line: 
                    break
            else:
                break 
        
        if len(service_line) > 3 : 
             cleaned_buffer.append(service_line)
        elif len(original_line.split()) <=3 and company_artifact_pattern.search(original_line): 
            pass 
        elif service_line: 
            cleaned_buffer.append(service_line)


    current_services_buffer = cleaned_buffer 

    processed_services = []
    temp_line = ""
    for item_idx, item in enumerate(current_services_buffer): 
        is_subheader_followed_by_list = False
        if (item.endswith(":") or len(item.split()) > 2) and (item_idx + 1 < len(current_services_buffer)):
            next_item = current_services_buffer[item_idx+1]
            if next_item.startswith(("-", "–", "•", "*", "o ")) or next_item[0].islower() or len(next_item.split()) > 3: 
                is_subheader_followed_by_list = True
        
        if item.endswith(("&", "und", "oder", ",")) or \
           (item.endswith("-") and not item.endswith("--")) or \
           is_subheader_followed_by_list:
            temp_line += item + (" " if not is_subheader_followed_by_list else ": ") 
        else:
            temp_line += item
            processed_services.append(temp_line.strip().rstrip(':').strip()) 
            temp_line = ""
            
    if temp_line:
        processed_services.append(temp_line.strip().rstrip(':').strip())

    final_services_text = "; ".join(s for s in processed_services if s and len(s) > 1) 
    return final_services_text.strip()


def determine_industry_and_niche(company_name, services_text, company_block_text):
    """
    Determines the industry and customer niche based on company name, services, and block text.
    Contains a comprehensive set of heuristics for ~70 companies.
    """
    industry = "Unknown"
    niche = "Unknown"
    services_lower = services_text.lower()
    block_lower = company_block_text.lower()
    name_lower = company_name.lower()

    if "denkmalzukunft.com" in name_lower or "denkmalzukunft" in name_lower:
        industry = "Beratung"
        niche = "Effizienzsteigerung, Führungskräfteentwicklung, Prozessoptimierung"
        if "produktionsoptimierung" in services_lower and "change-management" in services_lower:
            niche = "Beratung für Produktionsoptimierung, Change-Management und Führungskräfteentwicklung"
    elif "caremates.de" in name_lower or "kuidado" in name_lower:
        industry = "Gesundheitswesen / Software"
        niche = "Software für Pflegeplanung und -management (digitale Anmeldebögen, KI-Pflegeanamnese)"
    elif "cloud-ahoi.de" in name_lower or "cloud ahoi" in name_lower:
        industry = "IT-Dienstleistungen / Informationssicherheit"
        niche = "Beratung und Implementierung von ISMS (ISO 27001, TISAX), Interim CISO"
    elif "mscompanysolutions.de" in name_lower or "ms company solutions" in name_lower:
        industry = "Personalvermittlung / IT-Beratung"
        niche = "Personalvermittlung (Gesundheitswesen), IT-Projektmanagement, Interkulturelles Training"
    elif "dbschenker.com" in name_lower or "db schenker" in name_lower:
        industry = "Logistik / Zulieferer"
        niche = "Globale Logistik (Land, Luft, See, Kontrakt), Zolldienstleistungen, Zulieferer von Bauteilen"
    elif "healthworks.de" in name_lower:
        industry = "Gesundheitswesen / Arbeitsmedizin"
        niche = "Arbeitsmedizinische Betreuung, Präventivmedizin, Gefährdungsbeurteilungen"
    elif "tenderwise.io" in name_lower:
        industry = "Software / Logistik"
        niche = "Digitale Plattform für Logistik-Ausschreibungen (SaaS), Tender Management"
    elif "recos.de" in name_lower:
        industry = "IT-Dienstleistungen"
        niche = "IT-Systemhaus (Consulting, Hardware-Support Fujitsu, Virtualisierung, Netzwerk/WLAN)"
    elif "vidify.me" in name_lower:
        industry = "Software / Marketing / KI"
        niche = "KI-gestützte Erklärvideo-Erstellung, Visuelle Content-Erstellung, Video-Marketing"
    elif "ecoblister.com" in name_lower:
        industry = "Verpackungsindustrie / Pharmazie / Maschinenbau"
        niche = "Nachhaltige Blisterverpackungen (Arzneikalender), Befüllsysteme (BlisterJacky®), Blisterautomaten (Celia®)"
    elif "hospichef.com" in name_lower:
        industry = "Software / Gastronomie / Gesundheitswesen"
        niche = "Digitales Menübestellsystem für Kliniken (Patientenbestellung, Echtzeit-Kommunikation)"
    elif "salutes.space" in name_lower:
        industry = "Technologie / Raumfahrt / KI"
        niche = "KI-Plattform (AstraDroid), Dezentrale Weltrauminfrastruktur als Service"
    elif "medlytics.ai" in name_lower:
        industry = "Software / KI / Gesundheitswesen"
        niche = "KI-basierte Frühwarnsysteme für Kliniken (Nierenversagen, Delir, Glukose, Mangelernährung)"
    elif "cannaleo.de" in name_lower:
        industry = "Pharma / Handel / Software"
        niche = "Digitale Lösungen für Medizinal-Cannabis Vertrieb (Webseiten, Bestellsysteme für Apotheken)"
    elif "medwing.com" in name_lower:
        industry = "Gesundheitswesen / Personalvermittlung / Plattform"
        niche = "Karriereplattform für Gesundheitswesen (Direktsuche, Jobanzeigen, Zeitarbeit, International Recruiting)"
    elif "dimarketing-salesconsulting.de" in name_lower:
        industry = "Beratung / Vertriebstraining"
        niche = "Vertriebscoaching (V360°-Methodik), Workshops, Mentoring, Neukundengewinnung"
    elif "profitbl.com" in name_lower:
        industry = "Vertriebsdienstleistungen / Software"
        niche = "Sales Outsourcing, Multichannel Outreach, Markteintrittsstrategien, KI-gestützte Sales Academy"
    elif "balzer-partner.de" in name_lower:
        industry = "Beratung / Vertriebsmanagement"
        niche = "Externe Vertriebsleitung für den Mittelstand, Vertrieb as a Service, Inside Sales Team Aufbau"
    elif "rocketta.de" in name_lower:
        industry = "IT-Dienstleistungen / Software / KI"
        niche = "Microsoft 365 & SharePoint Lösungen, KI-Erweiterungen für Microsoft Co-Pilot"
    elif "noor-vision.com" in name_lower:
        industry = "IT-Beratung / SAP"
        niche = "SAP S/4HANA & EWM-Consulting, SAP Public Cloud, Digitale Prozessoptimierung"
    elif "smart2success.com" in name_lower:
        industry = "Software / Beratung"
        niche = "Plattform für Projekt-, Ressourcen-, Lieferantenmanagement und Informationssicherheit (ISO 27001)"
    elif "razertech.de" in name_lower:
        industry = "IT-Dienstleistungen"
        niche = "IT-Sicherheit, Microsoft 365, Managed IT-Services, Cloud-Telefonie, Windows 11 Migration"
    elif "linovy.de" in name_lower:
        industry = "Software / KI / Beratung"
        niche = "KI-gestützte Automatisierung, Cloud-Entwicklung, Fördermittelvermittlung für KI-Projekte"
    elif "kieker.net" in name_lower:
        industry = "Software / Monitoring / Event-Technik"
        niche = "Open-Source Application Performance Monitoring (Kieker Framework), Technische Event-Dienstleistungen"
    elif "gvs-sg.de" in name_lower or "gvs schmidt" in name_lower or "gvs-grossverbraucherspezialisten eg" in name_lower:
        industry = "Großhandel / Dienstleistung / Bildung"
        niche = "Fachgroßhandel für Reinigung & Pflege, GVS AKADEMIE, Logistik, Technischer Service"
    elif "carelend.de" in name_lower:
        industry = "Personalvermittlung / Bildung / Gesundheitswesen"
        niche = "Vermittlung & Schulung ausländischer Pflegefachkräfte, Integrationsunterstützung"
    elif "notara.de" in name_lower:
        industry = "Software / Rechtstechnologie"
        niche = "Digitale Mandanten-Datenblätter für Notariate, Prozessoptimierung für Notare"
    elif "greentech.training" in name_lower:
        industry = "Personalvermittlung / Bildung / Nachhaltigkeit"
        niche = "Rekrutierung & Weiterbildung von Fachkräften für die grüne Energiewende (Green IT, Solar)"
    elif "elixionmedical.com" in name_lower:
        industry = "Medizintechnik / Software / Gesundheitswesen"
        niche = "SmartDrain System zur intelligenten Überwachung von medizinischen Drainagen/Kathetern"
    elif "erikkaatz.de" in name_lower:
        industry = "Beratung / Vertriebsmanagement"
        niche = "Vertriebsstrategie, Teamaufbau & Coaching, Mentoring, Provisionsmodelle (KSR Sales Group)"
    elif "avia-concept.de" in name_lower:
        industry = "Beratung / Compliance / Luftfahrt"
        niche = "Verfahrensdokumentation nach GoBD, Projektentwicklung (Luftfahrt), Luftverkehrsberatung"
    elif "debeleeftv.de" in name_lower:
        industry = "Medizintechnik / Software / Hilfsmittel für Pflege"
        niche = "De BeleefTV - Interaktiver Aktivitätstisch für Demenzpatienten in Pflegeeinrichtungen"
    elif "relias.de" in name_lower:
        industry = "Software / E-Learning / Gesundheitswesen"
        niche = "Digitale Weiterbildungsplattform für Gesundheits- & Sozialwesen (Pflege, Rettungsdienste)"
    elif "mediceo.com" in name_lower:
        industry = "Software / Gesundheitswesen"
        niche = "Clinical Decision Support System (CDSS), Digitale Kittelkarte, SOP-Optimierung für Kliniken"
    elif "uberblick.io" in name_lower:
        industry = "Software / Dokumentenmanagement"
        niche = "Intelligente Dokumentenverwaltung & -organisation (Cloud, KI-basiert)"
    elif "digitalagentur1.de" in name_lower:
        industry = "Marketing / Webentwicklung / Beratung"
        niche = "Webentwicklung, E-Commerce, SEO, Online-Marketing, Prozessoptimierung für Kanzleien (DATEV)"
    elif "kanzleipartnergmbh.de" in name_lower:
        industry = "Software / Beratung / IT-Dienstleistungen"
        niche = "Digitalisierung & Automatisierung für Steuerkanzleien (DATEV-Erweiterungen)"
    elif "dasmerch.com" in name_lower:
        industry = "Handel / Marketing / Produktion"
        niche = "Individuelle Merchandise-Produkte, Full-Service-Produktion (Design, Fertigung, Logistik)"
    elif "coppeneur.de" in name_lower:
        industry = "Lebensmittel / Handel / Manufaktur"
        niche = "Premium Schokoladen- & Pralinenmanufaktur (Bean-to-Bar), B2B für Hotels/Gastronomie"
    elif "corominas-consulting.de" in name_lower:
        industry = "Marketing / Beratung / Rechtstechnologie"
        niche = "Online-Marketing für Kanzleien (SEO, SEA, Social Media, Webdesign) geleitet von Jurist"
    elif "steuerkoepfe.de" in name_lower:
        industry = "Medien / Bildung / Community-Plattform"
        niche = "Informations- & Weiterbildungsplattform für Steuerberater (Podcast, VIP-Klub, taxflix)"
    elif "digi-bel.de" in name_lower:
        industry = "Software / IT-Dienstleistungen (für Steuerkanzleien)"
        niche = "Plattform für digitalen Dokumentenaustausch & Belegerfassung (DATEV-Alternative)"
    elif "lemonad.marketing" in name_lower:
        industry = "Marketing / Agentur"
        niche = "Performance-Marketing Agentur (datengetrieben, SEO, SEA, Social Media, Conversion-Optimierung)"
    elif "taptotie.com" in name_lower:
        industry = "Technologie / Konsumgüter / Nachhaltigkeit"
        niche = "NFC-basierte Holz-Visitenkarten (umweltfreundlich) - Service eingestellt Juni 2025"
    elif "hrlab.de" in name_lower:
        industry = "Software / HR-Technologie (SaaS)"
        niche = "Cloudbasierte HR-Software für KMU (Personalmanagement, Prozessautomatisierung, Zeitwirtschaft, Bewerbermanagement)"
    elif "pnp-media.de" in name_lower:
        industry = "Marketing / Webentwicklung / Agentur"
        niche = "Webdesign, SEO, SEA, Performance Marketing, Social Recruiting, Branding"
    elif "sns-corp.com" in name_lower or "nss-corp.com" in name_lower : 
        industry = "IT-Dienstleistungen / Telekommunikation"
        niche = "VoIP Services (Digium Switchvox, Asterisk), Data Services (Ethernet Switching, Wi-Fi), IT Support"
    elif "vemeto.de" in name_lower:
        industry = "Beratung / Software / Compliance"
        niche = "Verfahrensdokumentation GoBD, Prozessoptimierung, Schulungen, BAFA-gelisteter Berater, Franchise-System"
    elif "smyczekconsulting.de" in name_lower:
        industry = "Beratung / Personalvermittlung"
        niche = "Consulting (Markteintritt, Produktkonfiguration), Recruiting, Führungskräfte-Coaching"
    elif "w-v.co.uk" in name_lower:
        industry = "Rechtsberatung / Steuerberatung / Unternehmensberatung"
        niche = "Internationale Unternehmensgründung & -expansion, Vermögenssicherung, Steuerplanung, Erbschaftsplanung"
    elif "project-sp.de" in name_lower:
        industry = "Maschinenbau / Automatisierungstechnik"
        niche = "Verpackungsmaschinen (PROPAC), Palettiermaschinen (PROPAL), Fördertechnik, Etikettierlösungen (PROLABEL), Cobots"
    elif "aliminkasso.de" in name_lower:
        industry = "Finanzdienstleistungen / Inkasso / KI"
        niche = "Kostenloses Inkasso (erfolgsbasiert), KI-optimierte Schuldnerkommunikation, Mahnwesen, Bonitätsprüfung"
    elif "bluecrestinc.com" in name_lower:
        industry = "Technologie / Drucklösungen / Postautomatisierung"
        niche = "Produktionsdrucker, Kuvertiersysteme, Sortiersysteme, Paketautomatisierung, Softwarelösungen für Postverarbeitung"
    elif "devim.de" in name_lower:
        industry = "Softwareentwicklung"
        niche = "Individuelle Bürosoftware, DailyCentral (modulares digitales Büro für KMU & Selbstständige)"
    elif "salesby.de" in name_lower:
        industry = "Vertrieb / Beratung" 
        niche = "Vertriebsunterstützung / Sales-Strategien / Leadgenerierung" 
    elif "assemblean.com" in name_lower:
        industry = "Software / Logistik / Supply Chain Management"
        niche = "Cloud-basierte Software für Supply Chain Kollaboration und Logistikprozesse"
    elif "rocket9.cloud" in name_lower:
        industry = "Software / IT-Dienstleistungen / Cloud Computing"
        niche = "Maßgeschneiderte Cloud-Lösungen (ROCKET Cloud), Business as a Service, Prozessoptimierung (ROCKET Suit)"
    elif "bodo-schmitz-urban.de" in name_lower:
        industry = "Beratung / Coaching / Gesundheitswesen"
        niche = "Mentoring & Coaching für Apothekeninhaber (BSU-Akademie), Apotheker-Unternehmer-Tag"
    elif "tegoly.com" in name_lower:
        industry = "Software / Rechtstechnologie" 
        niche = "Software für digitale Signaturen (tegolySIGN) / Vertragsmanagement" 
    elif "siteplan.at" in name_lower:
        industry = "Software / Bauwesen / Geoinformation"
        niche = "Digitale Vermessungs- und Navigationslösung für den Tiefbau (SitePlan)"
    elif "dexter-health.com" in name_lower:
        industry = "Gesundheitswesen / Software / KI"
        niche = "KI-gestützte Software zur Optimierung der Patientenaufnahme und -steuerung in Kliniken"
    elif "primeblister.de" in name_lower:
        industry = "Verpackungsindustrie / Pharmazie / Maschinenbau"
        niche = "Nachhaltige Blisterverpackungen (plastikfrei), Systeme für Apotheken (manuell bis automatisch)"
    elif "novaheal.de" in name_lower:
        industry = "Software / E-Learning / Gesundheitswesen" 
        niche = "Digitale Lernlösungen und Weiterbildung für Pflegekräfte / Gesundheitswesen" 
    elif "carlgoetz.de" in name_lower:
        industry = "Großhandel / Bauwesen / Holzwerkstoffe" 
        niche = "Großhandel für Holzwerkstoffe, Bodenbeläge, Türen, Bauelemente" 
    elif "schluetersche.de" in name_lower:
        industry = "Medien / Verlagswesen / Marketing"
        niche = "Fachmedien (Handwerk, Bau, Industrie etc.), Online-Marketing Services (KMU), Verzeichnismedien (Gelbe Seiten)"
    elif "elvari.de" in name_lower:
        industry = "Gesundheitswesen / Handel / Wellness" 
        niche = "Gesundheitsprodukte (z.B. Elvari Kristallmatte), Testangebote, Finanzierung" 
    elif "rodias.de" in name_lower or "spie-rodias.de" in name_lower:
        industry = "IT-Dienstleistungen / Softwareentwicklung / Industrie 4.0"
        niche = "Predictive Maintenance, Condition Monitoring, Softwarelösungen für Industrie, IT-Service & Support"
    elif "visitronic.de" in name_lower:
        industry = "Sicherheitstechnik / IT-Dienstleistungen / Kommunikationstechnik"
        niche = "Einbruchschutzsysteme, Rufanlagen (Pflege), Datennetze (VoIP), Glasfaserinstallation"
    elif "nxtlog.io" in name_lower: 
        industry = "Software / Logistik / Supply Chain Management"
        niche = "SaaS-Plattform für Echtzeit-Transparenz und Management in der Supply Chain"


    # Generic fallbacks if no specific rule matches after all specific checks
    elif industry == "Unknown": 
        if "software" in services_lower or "saas" in services_lower or ".io" in name_lower or "digital" in services_lower or "plattform" in services_lower or ".ai" in name_lower:
            industry = "Software / IT"
            if "beratung" in services_lower or "consulting" in services_lower:
                niche = "Softwareentwicklung und IT-Beratung"
            elif "agentur" in services_lower:
                niche = "Digitalagentur, Softwareentwicklung"
            elif "ki" in services_lower or "künstliche intelligenz" in services_lower or ".ai" in name_lower:
                niche = "KI-Softwarelösungen"
            else:
                niche = "Softwarelösungen (SaaS), Digitale Plattformen"
        elif "beratung" in services_lower or "consulting" in services_lower or "coach" in services_lower:
            industry = "Beratung"
            if "it" in services_lower or "digital" in services_lower or "erp" in services_lower or "crm" in services_lower:
                niche = "IT- und Digitalisierungsberatung"
            elif "management" in services_lower or "strategie" in services_lower:
                niche = "Management- und Strategieberatung"
            elif "personal" in services_lower or "hr" in services_lower:
                niche = "Personalberatung / HR Consulting"
            else:
                niche = "Unternehmensberatung"
        elif "logistik" in services_lower or "supply chain" in services_lower or "transport" in services_lower or "spedition" in services_lower:
            industry = "Logistik / Transport"
            niche = "Logistikdienstleistungen, Supply Chain Management"
        elif "marketing" in services_lower or "agentur" in services_lower or "kommunikation" in services_lower or "seo" in services_lower or "sea" in services_lower:
            industry = "Marketing / Agentur"
            if "online" in services_lower or "digital" in services_lower:
                niche = "Online-Marketing Agentur"
            else:
                niche = "Marketing- und Kommunikationsagentur"
        elif "gesundheit" in services_lower or "medizin" in services_lower or "pflege" in services_lower or "pharma" in services_lower or "health" in name_lower:
            industry = "Gesundheitswesen / Pharma"
            if "software" in services_lower or "digital" in services_lower:
                niche = "Digital Health, Software für Gesundheitswesen"
            else:
                niche = "Dienstleistungen im Gesundheitswesen"
        elif "handel" in services_lower or "shop" in services_lower or "vertrieb" in services_lower or "e-commerce" in services_lower:
            industry = "Handel / E-Commerce"
            if "b2b" in services_lower or "großhandel" in services_lower:
                niche = "B2B Handel, Großhandel"
            else:
                niche = "Einzelhandel, E-Commerce"

    return industry, niche

def parse_markdown(markdown_content):
    companies_data = []
    markdown_content = markdown_content.replace('\r\n', '\n')
    content_lines = markdown_content.split('\n')
    
    data_start_line_idx = 0
    
    try:
        inhalt_idx = -1
        for i, line in enumerate(content_lines):
            if line.strip().lower() == "inhalt":
                inhalt_idx = i
                break
        
        if inhalt_idx != -1:
            current_idx = inhalt_idx + 1
            while current_idx < len(content_lines):
                line_strip = content_lines[current_idx].strip()
                is_toc_entry = re.match(r"^KUNDE\s+\d+:\s*.*[\s\t]+\d+$", line_strip, re.IGNORECASE)
                is_actual_header = re.match(r"^KUNDE\s+\d+:\s*.+", line_strip, re.IGNORECASE)
                
                if is_actual_header and not is_toc_entry:
                    data_start_line_idx = current_idx
                    break
                elif not line_strip and (current_idx > inhalt_idx + 1): 
                    peek_idx = current_idx + 1
                    while peek_idx < len(content_lines) and not content_lines[peek_idx].strip():
                        peek_idx += 1 
                    if peek_idx < len(content_lines) and \
                       re.match(r"^KUNDE\s+\d+:\s*.+", content_lines[peek_idx].strip(), re.IGNORECASE) and \
                       not re.match(r"^KUNDE\s+\d+:\s*.*[\s\t]+\d+$", content_lines[peek_idx].strip(), re.IGNORECASE):
                        data_start_line_idx = peek_idx
                        break
                current_idx += 1
            else: 
                for i, line in enumerate(content_lines):
                    if re.match(r"^KUNDE\s+\d+:\s*.+", line.strip(), re.IGNORECASE) and \
                       not re.match(r"^KUNDE\s+\d+:\s*.*[\s\t]+\d+$", line.strip(), re.IGNORECASE):
                        data_start_line_idx = i
                        break
                else: return companies_data 
        else: 
            for i, line in enumerate(content_lines):
                if re.match(r"^KUNDE\s+\d+:\s*.+", line.strip(), re.IGNORECASE) and \
                   not re.match(r"^KUNDE\s+\d+:\s*.*[\s\t]+\d+$", line.strip(), re.IGNORECASE):
                    data_start_line_idx = i
                    break
            else: return companies_data 
            
    except Exception: 
        return companies_data

    content_to_parse = "\n".join(content_lines[data_start_line_idx:])
    
    if not content_to_parse.strip():
        return companies_data

    company_header_indices = []
    for match in re.finditer(r"^KUNDE\s+\d+:\s*.+", content_to_parse, re.MULTILINE | re.IGNORECASE):
        if not re.match(r"^KUNDE\s+\d+:\s*.*[\s\t]+\d+$", match.group(0).strip(), re.IGNORECASE):
            company_header_indices.append(match.start())

    if not company_header_indices:
        return companies_data

    for i in range(len(company_header_indices)):
        block_start_idx = company_header_indices[i]
        block_end_idx = company_header_indices[i+1] if (i + 1) < len(company_header_indices) else len(content_to_parse)
        
        current_block_full_text = content_to_parse[block_start_idx:block_end_idx].strip()
        
        block_lines = current_block_full_text.split('\n', 1)
        company_header_line_text = block_lines[0].strip()
        actual_company_content_text = block_lines[1].strip() if len(block_lines) > 1 else ""

        name_match_obj = re.match(r"^KUNDE\s+\d+:\s*(.+)", company_header_line_text, re.IGNORECASE)
        if not name_match_obj:
            continue
        
        company_name_from_header = name_match_obj.group(1).strip()
        company_name_cleaned = re.sub(r"[\s\t]+\d+$", "", company_name_from_header).strip()
        company_name_final = company_name_cleaned.split(" – ")[0].split(" - ")[0].strip()
        
        md_link_name_match_obj = re.match(r'\[([^\]]+)\]\(.*\)', company_name_final)
        if md_link_name_match_obj:
            company_name_final = md_link_name_match_obj.group(1).strip()
        else:
            company_name_final = company_name_final.split('(')[0].strip()
        
        company_name_final = company_name_final.replace("#", "").strip() 

        if not company_name_final:
            continue
            
        website_url = extract_website_from_text(actual_company_content_text)
        if website_url == "N/A":
            website_url = extract_website_from_text(company_name_from_header) 

        services_text_extracted = extract_services_from_block(actual_company_content_text)
        industry_extracted, niche_extracted = determine_industry_and_niche(company_name_final, services_text_extracted, actual_company_content_text)

        companies_data.append({
            "CompanyName": company_name_final,
            "Website": website_url,
            "ExtractedProductsServices": services_text_extracted,
            "ExtractedIndustry": industry_extracted,
            "ExtractedCustomerNiche": niche_extracted
        })
        
    return companies_data

def write_to_csv(data, filename="script_output/extracted_partner_companies.csv"):
    """Writes the extracted company data to a CSV file."""
    if not data:
        print("No data to write to CSV.")
        return

    fieldnames = ["CompanyName", "Website", "ExtractedProductsServices", "ExtractedIndustry", "ExtractedCustomerNiche"]
    try:
        with open(filename, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in data:
                writer.writerow(row)
        print(f"Data successfully written to {filename}")
    except IOError:
        print(f"Error: Could not write to CSV file {filename}.")

if __name__ == "__main__":
    markdown_file_path = "docs/Manuav Kundenzusammenfassung für Klaus.md"
    try:
        with open(markdown_file_path, "r", encoding="utf-8") as f:
            markdown_text_content = f.read()
    except FileNotFoundError:
        print(f"Error: The markdown file '{markdown_file_path}' was not found.")
        exit()
    except Exception as e:
        print(f"An error occurred while reading '{markdown_file_path}': {e}")
        exit()
    
    if not markdown_text_content.strip():
        print(f"Error: The markdown file '{markdown_file_path}' is empty or contains only whitespace.")
        exit()

    parsed_companies_data = parse_markdown(markdown_text_content)
    
    if parsed_companies_data:
        write_to_csv(parsed_companies_data, filename="script_output/extracted_partner_companies.csv")
    else:
        print("No company data was parsed from the markdown file.")