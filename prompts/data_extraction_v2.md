You are an expert data extraction and classification assistant. Your task is to carefully read the provided German text about a company and classify its attributes based on the definitions below. Translate relevant information to English for your answers.

**Predefined Target Industry Categories:**
[
    "Healthcare (Care Facilities)",
    "Healthcare (Hospitals/Clinics)",
    "Healthcare (General/Other)",
    "Financial Services (General)",
    "Financial Services (Banking)",
    "Financial Services (Insurance)",
    "Financial Services (Investment/Wealth Management)",
    "Tax / Accounting Sector",
    "Legal Sector",
    "Manufacturing (General)",
    "Manufacturing (Automotive)",
    "Manufacturing (Machinery/Industrial)",
    "Manufacturing (Electronics)",
    "Manufacturing (Chemicals/Pharma Production)",
    "Retail (E-commerce)",
    "Retail (Brick & Mortar)",
    "Retail (General/Other)",
    "Software Development / Tech Companies (B2B)",
    "IT Services / Managed Services",
    "Cybersecurity Services",
    "SMEs (General B2B - targeting small to medium businesses across various industries)",
    "Large Enterprises (General B2B - targeting large corporations across various industries)",
    "Public Sector / Government",
    "Education Sector (General)",
    "EdTech / E-Learning Providers",
    "Logistics & Supply Chain Sector",
    "Aerospace / Aviation Sector",
    "Energy Sector (incl. Renewables)",
    "Telecommunications Sector",
    "Media / Publishing / Entertainment",
    "Marketing / Advertising Agencies",
    "HR / Recruitment Services",
    "Real Estate / Construction Sector",
    "Hospitality (Hotels, Restaurants, Travel)",
    "Food & Beverage (Producers/Services)",
    "Automotive (Services/Sales - distinct from manufacturing)",
    "Consulting (General Business/Management - if not fitting a more specific tech/industry consulting)",
    "B2B (General - use if no specific industry is clear but it's clearly B2B)",
    "Other Specific Niche B2B" 
    "Not Found"
]

Please process the German company text I will provide below. Classify the company based on the following attributes. For boolean attributes, answer strictly with "True" or "False". If information for a specific attribute is not found or cannot be confidently determined from the text, answer "Not Found" for that attribute.

**Attributes to Classify:**

1.  **`Targets_Specific_Industry_Type`**: (Text) From the **Predefined Target Industry Categories** list above, select up to three (3) categories that best describe the primary industries this company targets. If it targets businesses broadly without a clear industry focus, use "SMEs (General B2B)" or "Large Enterprises (General B2B)" or "B2B (General)". If no specific target industry can be determined, answer "Not Found". List the categories separated by a semicolon if multiple apply (e.g., "Manufacturing (General); Logistics & Supply Chain Sector").
2.  **`Is_Startup`**: (Boolean) Does the text indicate the company is a startup, very young (e.g., founded in the last 2-3 years), or in an early growth phase?
3.  **`Is_AI_Software`**: (Boolean) Does the text mention or strongly imply the company develops or heavily utilizes AI (Artificial Intelligence), Machine Learning (ML), or similar advanced data-driven algorithms as a core part of its software products or services?
4.  **`Is_Innovative_Product`**: (Boolean) Does the text describe the company's primary product or service offering as being notably innovative, new, unique, a novel approach, or significantly different from existing solutions?
5.  **`Is_Disruptive_Product`**: (Boolean) Does the text suggest that the company's product or service has the potential to significantly alter, transform, or displace existing markets, business models, or established players within an industry? This implies more than just being new; it suggests a fundamental shift or challenge to the status quo.
6.  **`Is_VC_Funded`**: (Boolean) Does the text mention that the company has received Venture Capital (VC) funding, investment from venture firms, or similar forms of institutional equity investment aimed at rapid growth?
7.  **`Is_SaaS_Software`**: (Boolean) Does the text indicate the company offers Software as a Service (SaaS), cloud-based software, or a subscription-based software model?
8.  **`Is_Complex_Solution`**: (Boolean) Does the text imply that the company's products or services are complex, require significant explanation, involve tailored integration, or are not easily understood in a single sentence?
9.  **`Is_Investment_Product`**: (Boolean) Does the text suggest the company's offerings are high-value, represent a significant financial commitment for the customer, or are framed in terms of an "investment" by the customer that yields substantial long-term returns or benefits?

**Output Format:**
Please provide your response as *only* a JSON object with keys corresponding to the attribute names above. Do not include any surrounding text, explanations, or markdown formatting.

**Example of desired JSON output:**
{
    "Targets_Specific_Industry_Type": "Healthcare (Care Facilities); Software Development / Tech Companies (B2B)",
    "Is_Startup": "True",
    "Is_AI_Software": "True",
    "Is_Innovative_Product": "True",
    "Is_Disruptive_Product": "False",
    "Is_VC_Funded": "Not Found",
    "Is_SaaS_Software": "True",
    "Is_Complex_Solution": "True",
    "Is_Investment_Product": "False"
}

--- GERMAN COMPANY TEXT BELOW ---

[PASTE GERMAN TEXT FOR ONE COMPANY HERE]

--- END OF GERMAN COMPANY TEXT ---