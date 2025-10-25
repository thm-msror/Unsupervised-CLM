import os
import json
import re
import time
from dotenv import load_dotenv
import google.generativeai as genai

from doc_reader import read_docu
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, RGBColor, Inches


def generate_contract(contract_data: dict, markdown_template: str, old_contract: str = "") -> str:
    """
    Generates a full professional contract in Markdown format using Gemini 2.5 Flash.
    """
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    genai.configure(api_key=api_key)

    if old_contract:
        old_contract_prompt = f"""
        ### 📄 Old contract:
        ### CRITICAL INSTRUCTION: You will use this old contract as a base for the new contract. You will try to use as much from the old as possible. You will only change sentences if the old is not compliant with the **{contract_data["Industry"]}** industry standards and the **{contract_data["Jurisdiction"]}** 
        {old_contract}

        ---
        """
    else: 
        old_contract_prompt = ""
    

    prompt = f"""
        You are a professional contract automation AI.

        Use the JSON data and Markdown structure below to generate a **complete, legally sound, and jurisdiction-specific contract** in Markdown format. 
        Fill all placeholders naturally and professionally — every section must align with the provided context.

        ---

        ### Contract Data (JSON)
        {json.dumps(contract_data, indent=2)}

        ---

        ### 📄 Markdown Template
        {markdown_template}

        ---

        {old_contract_prompt}

        ### CRITICAL INSTRUCTIONS — FOLLOW STRICTLY
        - You MUST adapt all clauses, tone, and terminology to **the specified Industry: "{contract_data["Industry"]}"**.  
        Example: a tech contract should include IP, confidentiality, and data protection clauses; a construction contract should include project scope, timelines, and site liability.
        - You MUST adapt all legal phrasing, governing law, and enforcement clauses to **the specified Jurisdiction: "{contract_data["Jurisdiction"]}"**.  
        Example: use region-appropriate terminology, legal references, and dispute resolution norms.
        - Do NOT include or reference any other jurisdiction, law, or country outside "{contract_data["Jurisdiction"]}".
        - Do NOT generalize clauses. Always ground them in the provided Industry and Jurisdiction context.
        - Replace all placeholders like {{PartyA.LegalName}} or {{EffectiveDate}} with actual JSON data.
        - Maintain Markdown structure and headings (e.g., `#`, `##`, `###`) exactly as given in the template.
        - The contract must be written entirely in **{contract_data["Language"]}**.
        - Output **only** the completed Markdown contract — no explanations, no notes.

        ---

        ### GOAL
        Produce a polished, realistic, and enforceable contract fully compliant with the **{contract_data["Industry"]}** industry standards and the **{contract_data["Jurisdiction"]}** legal system.
        """
    

    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(prompt)
    return response.text.strip()

def markdown_to_docx(text: str, output_path: str):
    """
    Converts Markdown-style contract text to a properly formatted, professional Word document.
    Supports headings (#), bold (**), italics (*), and normal paragraphs.
    """
    doc = Document()

    # Global style
    style = doc.styles["Normal"]
    font = style.font
    font.name = "Times New Roman"
    font.size = Pt(12)
    
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)

    lines = text.splitlines()
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # --- HEADINGS WITH FORMATTING ---
        if stripped.startswith("### "):
            heading = stripped.replace("### ", "").strip()
            p = doc.add_paragraph()
            run = p.add_run(heading)
            run.bold = True
            run.font.name = "Times New Roman"
            run.font.size = Pt(12)   # Heading 3: 12–13 pt
            run.font.color.rgb = RGBColor(0, 0, 0)
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_after = Pt(4)

        elif stripped.startswith("## "):
            heading = stripped.replace("## ", "").strip()
            p = doc.add_paragraph()
            run = p.add_run(heading.upper())  # optional all caps
            run.bold = True
            run.font.name = "Times New Roman"
            run.font.size = Pt(14)   # Heading 2: 14 pt
            run.font.color.rgb = RGBColor(0, 0, 0)
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_after = Pt(6)

        elif stripped.startswith("# "):
            heading = stripped.replace("# ", "").strip()
            p = doc.add_paragraph()
            run = p.add_run(heading.upper())
            run.bold = True
            run.font.name = "Times New Roman"
            run.font.size = Pt(16)   # Heading 1: 16–18 pt
            run.font.color.rgb = RGBColor(0, 0, 0)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_after = Pt(8)
            p.paragraph_format.space_before = Pt(30)


        else:
            # Convert bold and italics manually
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            tokens = re.split(r"(\*\*.*?\*\*|\*.*?\*)", stripped)
            for token in tokens:
                run = p.add_run()
                if token.startswith("**") and token.endswith("**"):
                    run.text = token[2:-2]
                    run.bold = True
                elif token.startswith("*") and token.endswith("*"):
                    run.text = token[1:-1]
                    run.italic = True
                else:
                    run.text = token

        p.paragraph_format.space_after = Pt(6)
        

    # Save as .docx
    doc.save(output_path)
    print(f"✅ Styled contract saved at: {output_path}")
    
def generate_contract_doc(contract_data, template_path, output_file_path, md_path=False, old_contract_path = False):
    start_time = time.time()

    # Read template_path
    with open(template_path, "r", encoding="utf-8") as f:
        markdown_template = f.read()

    if old_contract_path:
        old_contract= read_docu(old_contract_path)["full_text"]

    else:
        old_contract = ""


    #============================================
    # Generating contract
    final_contract = generate_contract(contract_data, markdown_template, old_contract)
    #============================================

    # Make output_file_path if missing
    output_folder = os.path.dirname(output_file_path)
    os.makedirs(output_folder, exist_ok=True)

    # Save as MD
    if md_path:
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(final_contract)
        print(f"✅ Markdown contract saved as: {md_path}")
    
    # Save as Word Document
    markdown_to_docx(final_contract, output_file_path)
    print(f"✅ Word contract saved as: {output_file_path}")

    print(f"⏱️ Contract generation completed in {time.time() - start_time:.2f} seconds.")
    

if __name__ == "__main__":
    contract_input_1 = {
        "ContractTemplate": "Services Agreement",
        "Industry": "Technology",
        "Jurisdiction": "Qatar",
        "Language": "English",
        "Start_date": "2025-11-01",
        "End_date": "2026-11-01",
        "PartyA": {
            "LegalName": "QTech Solutions W.L.L.",
            "Role": "Client",
            "Address": "Office 304, Doha Tower, West Bay, Doha, Qatar"
        },
        "PartyB": {
            "LegalName": "CodeBridge Technologies Ltd.",
            "Role": "Contractor",
            "Address": "45 Innovation Street, London, United Kingdom"
        },
        "Context": "Software development and maintenance of a web-based platform for QTech’s internal operations."
    }

    old = ''' AMENDED AND RESTATED INTERCOMPANY SERVICES AND COST ALLOCATION AGREEMENT\nThis Amended and Restated Intercompany Services and Cost Allocation Agreement (this “Agreement”) is made and entered into effective as to each Affiliate (as that term is defined below) as of the date such Affiliate first becomes a signatory hereto, by and among AMERICAN FAMILY MUTUAL INSURANCE COMPANY, S.I. (“AFMIC”) and each of its affiliates identified as the other signatories hereto, either in the signature lines below in this Agreement, or in a Joinder hereto substantially in the form set forth in Exhibit A, signed by AFMIC and such subsidiary (each an “Affiliate” and together the “Affiliates”).\nRECITALS\nWHEREAS, AFMIC may provide goods (“Goods”), third party services (“Third Party Services”), and management and other direct services including, without limitation, executive, corporate strategy, business development, legal, corporate governance, product management, product development, underwriting, marketing, customer sales, customer service, policy administration, billing, claims, reserving, sourcing and procurement, human resources, business integration, communications, strategic data and analytics, financial, investment, enterprise risk, reinsurance, internal audit, licensing, compliance, information and technology services (collectively, “Management Services”) used by the Affiliates in the conduct of their various businesses; and\nWHEREAS, AFMIC may at times, request Goods, Third Party Services and/or Management Services from one or more of the Affiliates for use in AFMIC’s various businesses, including the provision of services to other affiliates and/or subsidiaries of AFMIC; and\nWHEREAS, when and to the extent that a Party hereunder is the provider of Goods, Third Party Services or Management Services to another Party under the terms and conditions of this Agreement, it is referred to herein as a “Service Provider”; and\nWHEREAS, when and to the extent that a Party hereunder is the recipient of Goods, Third Party Services or Management Services from another Party under the terms and conditions of this Agreement, it is referred to herein as a “Service Recipient”.\nNOW, THEREFORE, in consideration of the mutual promises made and the terms and conditions hereunder described, the Parties agree as follows:\n1.\tGoods and Services Provided on the Cost Allocation Method\n1.1 Each Service Recipient shall be charged with its allocable share of the Service Provider’s actual costs incurred, or with the fair value of the services provided, as the case may be, in connection with the Service Provider’s provision of Goods, Third Party Services, and Management Services to the Service Recipient. Allocation of the Service Provider’s actual costs and/or the calculation of the fair value of the services provided shall occur in accordance with the following methods and procedures, in each case as applicable to and/or appropriate for the type of Goods, Third Party Services or Management Services at issue:\nThe Service Provider will charge each Service Recipient on a pass-through cost basis for the Goods actually used by such Service Recipient on a not less than quarterly basis.\nThe Service Provider will charge each Service Recipient on a pass-through cost basis for Third Party Services provided by third parties under contract with the Service Provider based on services actually used by such Service Recipient on a not less than quarterly basis.\nThe Service Provider may charge each Service Recipient a monthly rental charge for office space based on square footage actually used by personnel providing services on behalf of such Service Recipient, or used to house equipment or supplies used by such Service Recipient, times a rental factor per square foot, on a not less than quarterly basis.\nThe Service Provider will charge each Service Recipient a monthly Management Services charge for management, administrative, clerical and other direct services (including those included in the definition of Management Services contained in the first Recital of this Agreement) actually used by such Service Recipient in accordance with the following methods and procedures, on a not less than quarterly basis, and in each case as applicable to and/or appropriate for the type of Management Service at issue:\nbased on a percentage of a full-time employee (“FTE”) that will spend time on activities involved in providing such Management Services to the Service Recipient, calculated as a percentage of the costs the Service Provider incurs for wages for the FTE plus an appropriate load representing a share of the costs the Service Provider incurs for fringe benefits provided to the FTE;\nbased on actual hours that the Service Provider’s employees spend on activities involved in providing such Management Services to the Service Recipients, multiplied by an internally established billing rate; or\nbased on the fair value of the services provided as measured or determined by reference to what the Service Recipient would typically have to pay, either directly or on a pass-through basis, if the services at issue were provided to the Service Recipient by an unaffiliated third party in an arms-length transaction.\nNot less than quarterly, the Parties shall settle all charges incurred under this Agreement on a net basis.\nThe allocation and settlement methods described above shall be periodically reviewed, and may be amended by AFMIC in its reasonable discretion, upon notice to the Affiliates, if necessary for:\nChanges in business practices;\nChanges in Generally Acceptable Accounting Principles or Statutory Accounting Principles; and\nDeterminations that an inappropriate method has been used in the past which did not fairly distribute the costs among the parties.\nAny change in allocation or settlement methods shall apply on the same basis to all Service Providers and Service Recipients.\n2.\tGeneral\n2.1 AFMIC and the Affiliates agree that the fundamental purposes of this Agreement are: (i) to secure the provision of Goods, Third Party Services, and Management Services on a cost-efficient and effective basis for the mutual benefit of Service\nProviders and Service Recipients hereunder; and (ii) to assure that Service Providers hereunder receive appropriate payments from Service Recipients hereunder so that the Service Providers have no material net cost for providing the Goods, Third Party Services, and Management Services, and so that no Service Recipient pays materially more than fair value for the Goods, Third Party Services, and Management Services.\n2.2 Each Service Provider hereunder shall use its best efforts to provide the Management Services. Each Service Provider hereunder agrees to perform the Management Services in material compliance with: (i) applicable law; (ii) the same standards pursuant to which it performs similar functions with respect to its own operations; and (iii) the skill, diligence and expertise commonly expected from experienced and qualified personnel performing such duties in conformance with insurance industry standards. Notwithstanding the foregoing, each Service Recipient hereunder agrees that each Service Provider hereunder shall have no obligation to provide Management Services to a Service Recipient of a quality greater than the quality of such Management Services that the Service Provider maintains for its own operations.\n2.3 Nothing in this Agreement shall constitute or be construed to be or create a partnership or joint venture relationship between any Service Recipient, on the one hand, and Service Provider, on the other hand, and every Service Provider’s status under this Agreement shall be that of an independent contractor. In connection with the performance of Management Services under this Agreement, neither any Service Recipient nor any Service Provider shall make any statement or take any action that is inconsistent with the provisions of this Section 2.3. It is understood and agreed that the management, control and direction of the operations and policies of each Service Recipient shall remain at all times under the exclusive control of the Board of Directors of such Service Recipient.\nBooks and Records.\nEach Service Provider shall keep accurate records and accounts of all Goods, Third Party Services, and Management Services provided pursuant to this Agreement. Such records and accounts shall be maintained in accordance with sound business practices, in a manner that clearly and accurately discloses the nature and details of the transaction and services and which, in accordance with generally accepted accounting principles, permits ascertainment of charges relating to the transaction and services, and shall be subject to such systems of internal control as are required by law. All records and accounts applicable to the provision of Goods, Third Party Services, or Management Services to any Service Recipient shall be available for inspection by such Service Recipient and its representatives, including such Service Recipient’s independent public accounting firm, at any time upon request during commercially reasonable hours.\nAll such records and accounts shall be the property of each respective Service Provider, subject to the right of inspection of a Service Recipient under Section 3.1 of this Agreement and the examination rights of insurance and other applicable regulatory authorities. Notwithstanding the foregoing, to the extent that the Service Recipient is an insurance company, all such records and accounts shall be the property of the Service Recipient and shall at all times remain under the control of the Service Recipient.\nIndemnification.\nEach Service Recipient shall be solely responsible, severally and not jointly, for, and shall hold harmless and indemnify each of their respective Service\nProvider(s), including their successors, officers, directors, employees, agents, and affiliates, from and against all losses, claims, damages, liabilities, and expenses, including any and all reasonable expenses and attorneys’ fees and disbursements incurred in investigating, preparing or defending against any litigation or proceeding, whether commenced or threatened, or any other claim whatsoever, whether or not resulting in any liability, suffered, incurred, made, brought or asserted by any person not a party to this Agreement in connection with such Service Provider’s provision of Management Services to such Service Recipient, unless such loss, claim, damage, liability, or expense results from the negligence, willful misconduct, or fraud of the Service Provider or its officers, directors, employees, agents, or affiliates or any other person engaged by the Service Provider to provide Management Services to such Service Recipient.\nEach Service Provider shall be solely responsible for, and shall hold harmless and indemnify each of their respective Service Recipient(s), including their respective successors, officers, directors, employees, agents, and affiliates, from and against all losses, claims, damages, liabilities and expenses, including any and all reasonable expenses and attorneys’ fees and disbursements incurred in investigating, preparing or defending against any litigation or proceeding, whether commenced or threatened, or any other claim whatsoever, whether or not resulting in any liability, suffered, incurred, made, brought, or asserted by any person not a party to this Agreement resulting from the negligence, willful misconduct, or fraud of the Service Provider or its officers, directors, employees, agents, or affiliates or any other person engaged by the Service Provider to provide Management Services to such Service Recipient.\nTermination.\nThis Agreement shall have a term that commences as to each Affiliate on the date such Affiliate first becomes a signatory hereto (the “Initial Effective Date”), and initially expires as to such Subsidiary on the date which is five years after such Initial Effective Date, provided, however, that, on each December 31 after the Initial Effective Date of this Agreement for any Affiliate, the term of this Agreement as to such Affiliate shall be extended by one year so that at all times this Agreement shall have a then current term of five years; provided, however, that this Agreement may be terminated as to any Affiliate at any time prior to its then expiration date in any of the following events, subject, in all events, to the completion of any necessary insurance regulatory filings or receipt of any necessary insurance regulatory approvals:\nBy AFMIC, upon 30 days prior written notice to any Affiliate, if such Affiliate shall have become insolvent or shall have become subject to any voluntary or involuntary conservatorship, receivership, reorganization, liquidation or bankruptcy case or proceeding. Notwithstanding the foregoing, AFMIC shall not be entitled to terminate this Agreement pursuant to this clause if the relevant Affiliate is an insurance company.\nBy AFMIC and such Affiliate at any time by mutual written agreement.\nThe aforesaid respective rights of termination of the Affiliates and AFMIC may be exercised without prejudice to any other remedy to which the terminating Affiliate or AFMIC, as the case may be, is entitled in law or in equity.\nMiscellaneous.\nAFMIC shall not advance any funds to any Affiliate except to pay for services under this Agreement, and shall retain oversight for any Management Services provided to it by any Affiliate hereunder. All funds and invested assets of AFMIC are the exclusive property of AFMIC, held for the benefit of AFMIC, and are subject to the control of AFMIC.\nIf AFMIC is placed into delinquency proceedings or seized by the Wisconsin Commissioner of Insurance (the “Commissioner”) pursuant to ch. 645, Wis.\nStats.:\nAll of the rights of AFMIC under this Agreement extend to the receiver or Commissioner.\nAll books and records of AFMIC will immediately be made available to the receiver or Commissioner, and shall be turned over to the receiver or Commissioner immediately upon request.\nThe Affiliates shall have no automatic right to terminate this Agreement.\nThe Affiliates shall continue to maintain any systems, programs or other infrastructure and will make them available to the receiver or Commissioner for so long as the Affiliate continues to receive timely payments from AFMIC for services.\nAny notice under this Agreement shall be deemed given when personally delivered in writing, when sent via facsimile, when dispatched via overnight courier, or when mailed as described below and shall be deemed received when personally delivered in writing, on the date sent by facsimile transmission, 24 hours after being sent via overnight express courier, or 72 hours after it has been deposited in the United States Mail, registered or certified, postage pre-paid, properly addressed to the party to whom it is intended at the address set forth below or at such other address of which notice is given in accordance herewith:\nif to any Affiliate, to the address and other contact information maintained for the executive offices of such Affiliate on the books and records of AFMIC, Attention: Secretary\nif to AFMIC, to:\n[American Family Mutual Insurance Company, S.I.]\n6000 American Parkway\nMadison, Wisconsin 53783-0001 Attention: Secretary Facsimile:\nSuch notice shall be given at such other address or to such other representative as a party to this Agreement may furnish pursuant to this Section 6.3 to the other party to this Agreement.\nNo assignment, transfer or delegation, whether by merger or other operation of law or otherwise, of any rights or obligations under this Agreement shall be made by a party to this Agreement without the prior written consent of the other party to this Agreement and, if required by applicable law, the Wisconsin Commissioner\nof Insurance, and any other insurance regulatory authority having jurisdiction over this Agreement. This Agreement shall be binding upon the parties hereto and their respective permitted successors and assigns.\nThis Agreement constitutes the entire agreement of the parties to this Agreement with respect to its subject matter, supersedes all prior agreements, and may not be amended except in writing signed by the party to this Agreement against whom the change is asserted. The failure of any party to this Agreement at any time or times to require the performance of any provision of this Agreement shall in no manner affect the right to enforce the same and no waiver by any party to this Agreement of any provision or breach of any provision of this Agreement in any one or more instances shall be deemed or construed either as a further or continuing waiver of any such provision or breach or as a waiver of any other provision or breach of any other provision of this Agreement.\nIn case any one or more of the provisions contained herein shall, for any reason, be held to be invalid, illegal or unenforceable in any respect, such invalidity, illegality or unenforceability shall not affect any other provision of this Agreement, but this Agreement shall be construed as if such invalid, illegal or unenforceable provision or provisions had never been contained herein unless the deletion of such provision or provisions would result in such a material change as to cause continued performance of this Agreement as contemplated herein to be unreasonable or materially and adversely frustrate the objectives of the parties in originally entering into this Agreement as expressed in the Recitals to this Agreement.\nThis Agreement may be executed using two or more counterparts, each of which shall be deemed an original but all of which together constitute one and the same Agreement. This Agreement shall be deemed executed and delivered upon the exchange of executed documents by facsimile transmittal or scanned signature pages transmitted by electronic mail. Immediately following the exchange of executed documents by facsimile transmittal or electronic mail, the parties shall transmit signed original documents to each other, but the failure of either party to comply with this requirement shall not render this Agreement void or otherwise unenforceable.\nExcept as to matters covered by this Agreement or by another written agreement, no party hereto is an agent of any other, and shall not be liable for the obligations, acts or omissions of the other party.\nThe headings in this Agreement are for convenience only, and shall be accorded no weight in the construction of this Agreement.\nThis Agreement shall be construed and enforced according to the laws of the State of Wisconsin.\n[SIGNATURE PAGE FOLLOWS]\nIN WITNESS WHEREOF, AFMIC and the below-named Affiliates have executed this agreement to be effective as of the day and year set forth below the Affiliates’ signatures.\n[AMERICAN FAMILY MUTUAL INSURANCE COMPANY, S.I.]\nBy: __________________________________________\n[NAME]\n[TITLE]\n[AMERICAN FAMILY INSURANCE MUTUAL HOLDING COMPANY]\nBy:___________________________________________\n[NAME]\n[TITLE]\nDate:__________________________________________\n[AMFAM HOLDINGS, INC.]\nBy:___________________________________________\n[NAME]\n[TITLE]\nDate:__________________________________________\n[SIGNATURE PAGE TO\nExhibit A: Form of Joinder\nJOINDER AGREEMENT\nThis JOINDER AGREEMENT (this “Joinder”) dated as of the Effective Date written below, is entered into pursuant to that certain Intercompany Services and Cost Allocation Agreement, dated as of [_____________, 2016] (as amended, supplemented or otherwise modified from time to time, the “Agreement”) by and among [AMERICAN FAMILY MUTUAL\nINSURANCE COMPANY, S.I. (“AFMIC”)] and each of its affiliates identified as the other signatories thereto, either in the signature lines below in the Agreement, or in a joinder thereto, signed by AFMIC and such subsidiary. Unless otherwise defined herein, capitalized terms used herein and defined in the Agreement shall have the meanings given to them in the Agreement.\nRECITALS\nWHEREAS, the affiliate of AFMIC signing this Joinder (the “Joinder Party”) wishes to become a signatory to the Agreement;\nNOW, THEREFORE, in consideration of the mutual promises made and the terms and conditions described in the Agreement, AFMIC and the Joinder Party agree as follows:\nJoinder to the Agreement. The Joinder Party confirms that it has received a copy of the Agreement and such other information as it has deemed appropriate to make its own decision to enter into this Joinder and agrees to:\njoin and become a party to the Agreement as an Affiliate;\nbe bound by all covenants and agreements in the Agreement; and (c)\tperform all obligations required of it by the Agreement.\nEffective Date. The Effective Date of the Agreement, with respect to the Joinder Party, shall be the Effective Date set forth on the signature page to this Joinder.\nGoverning Law. This Joinder shall be construed and enforced according to the laws of the State of Wisconsin.\nSignature Pages. The execution of this Joinder shall be subect to Section 6.7 of the Agreement.\n[SIGNATURE PAGE FOLLOWS]\n[FORM OF JOINDER TO\nIN WITNESS WHEREOF, AFMIC and the below-named Joinder Party have executed this agreement as of the Effective Date set forth below.\n[AMERICAN FAMILY MUTUAL INSURANCE COMPANY, S.I.]\nBy: __________________________________________\n[NAME]\n[TITLE]\n[JOINDER PARTY]\nBy:___________________________________________\n[NAME]\n[TITLE]\nEffective Date:_______________________________\n[FORM OF JOINDER TO'''

# DOESNT WORK
#     contract_input_2 = {
#     "ContractTemplate": "عقد توريد",
#     "Industry": "الضيافة والمطاعم",
#     "Jurisdiction": "المملكة العربية السعودية",
#     "Language": "Arabic",
#     "Start_date": "2025-12-15",
#     "End_date": "2026-12-15",
#     "PartyA": {
#         "LegalName": "مطاعم الواحة الذهبية المحدودة",
#         "Role": "العميل",
#         "Address": "شارع التحلية، حي العليا، الرياض، المملكة العربية السعودية"
#     },
#     "PartyB": {
#         "LegalName": "شركة المذاق الفاخر للتوريد الغذائي",
#         "Role": "المورد",
#         "Address": "المنطقة الصناعية الثانية، جدة، المملكة العربية السعودية"
#     },
#     "Context": "تتعلق هذه الاتفاقية بتوريد المواد الغذائية والمكونات الطازجة لمجموعة مطاعم الواحة الذهبية بشكل دوري، وفقاً لمواصفات الجودة والمعايير المتفق عليها."
# }

   
    generate_contract_doc(contract_input_1, r"feature5\contract_template.md", r"feature5\contract_output_4.docx", old_contract_path=r"data\english\FinAmFamMut2016RestructExhA-19.docx")
