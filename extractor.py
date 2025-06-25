import pdfplumber
import PyPDF2
import json
import os
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path


class Extractor:
    """ADT-1 PDF extractor optimized for LLM summary generation"""

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.field_mapping = {
            # Company fields
            'CIN_C': 'company_cin',
            'CompanyName_C': 'company_name',
            'EmailId_C': 'company_email',
            'GLN_C': 'company_gln',
            'permaddress1a_C': 'company_address_line1',
            'permaddress2a_C': 'company_address_line2',
            'permaddress2b_C': 'company_address_line2_alt',
            'permaddress3a_C': 'company_address_line3',
            'cityname_C': 'company_city',
            'City_C': 'company_city_alt',
            'pincode_C': 'company_pincode',
            'Pin_C': 'company_pincode_alt',
            'statename_C': 'company_state',
            'State_P': 'company_state_alt',
            'countryname_C': 'company_country',
            'Country_C': 'company_country_alt',

            # Auditor fields
            'PAN_C': 'auditor_pan',
            'NameAuditorFirm_C': 'auditor_firm_name',
            'MemberShNum': 'auditor_membership_number',
            'AuditorNumber': 'number_of_auditors',
            'auditoraddress1a_C': 'auditor_address_line1',
            'auditoraddress2a_C': 'auditor_address_line2',
            'auditoraddress3a_C': 'auditor_address_line3',
            'auditorcityname_C': 'auditor_city',
            'auditorpincode_C': 'auditor_pincode',
            'auditorstatename_C': 'auditor_state',
            'auditorcountryname_C': 'auditor_country',
            'auditoremailid_C': 'auditor_email',
            'email': 'auditor_email_alt',

            # Appointment fields
            'appointmentdate_C': 'appointment_date',
            'agmdate_C': 'agm_date',
            'DateAnnualGenMeet_D': 'agm_date_alt',
            'periodfrom_C': 'period_from',
            'periodto_C': 'period_to',
            'DateOfAccAuditedFrom_D': 'audit_period_from',
            'DateOfAccAuditedTo_D': 'audit_period_to',
            'nofinyears_C': 'number_of_financial_years',
            'NumOfFinanYearApp': 'number_of_financial_years_alt',
            'CurrDate': 'current_date',
            'current_date': 'form_date',
            'DateOfAppSect_D': 'appointment_section_date',
            'DateReceipt_D': 'receipt_date',

            # Additional fields
            'DINOfDir_C': 'director_din',
            'ResoNum': 'resolution_number',
            'serialNumber': 'certificate_serial_number',
            'Attachment_C': 'attachments'
        }

    def extract_form_fields_pypdf2(self) -> Dict[str, Any]:
        """Extract form field data using PyPDF2"""
        form_data = {}

        try:
            with open(self.pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)

                if pdf_reader.is_encrypted:
                    print("PDF is encrypted, attempting to decrypt...")
                    try:
                        pdf_reader.decrypt("")
                    except Exception as e:
                        print(f"Failed to decrypt PDF: {e}")
                        return form_data

                # Extract form fields
                if hasattr(pdf_reader, 'get_form_text_fields'):
                    form_fields = pdf_reader.get_form_text_fields()
                    if form_fields:
                        form_data.update(form_fields)

                # Alternative method for form fields
                for page_num, page in enumerate(pdf_reader.pages):
                    if '/Annots' in page:
                        try:
                            annotations = page['/Annots']
                            for annot_ref in annotations:
                                try:
                                    annot = annot_ref.get_object()
                                    if annot.get('/Subtype') == '/Widget':
                                        field_name = annot.get('/T')
                                        field_value = annot.get('/V')
                                        if field_name and field_value:
                                            form_data[str(field_name)] = str(field_value)
                                except Exception:
                                    continue
                        except Exception as e:
                            continue

        except Exception as e:
            print(f"Error with PyPDF2 extraction: {e}")

        return form_data

    def get_raw_text(self) -> str:
        """Extract raw text from PDF"""
        raw_text = ""
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        raw_text += page_text + "\n"
        except Exception as e:
            print(f"Error extracting raw text: {e}")
        return raw_text

    def clean_and_map_form_fields(self, form_fields: Dict[str, Any]) -> Dict[str, str]:
        """Clean and map form field names to meaningful keys"""
        cleaned_fields = {}

        for field_name, field_value in form_fields.items():
            if not field_value or not str(field_value).strip():
                continue

            # Remove array notation
            clean_field_name = re.sub(r'\[\d+\]$', '', field_name)

            # Map to meaningful name
            mapped_name = self.field_mapping.get(clean_field_name, clean_field_name)

            # Clean the value
            clean_value = str(field_value).strip()

            # Skip system/hidden fields
            if any(x in clean_field_name.lower() for x in
                   ['hidden', 'sid', 'call_id', 'form_id', 'version', 'reader', 'sign']):
                continue

            cleaned_fields[mapped_name] = clean_value

        return cleaned_fields

    def consolidate_duplicate_fields(self, cleaned_fields: Dict[str, str]) -> Dict[str, str]:
        """Consolidate duplicate fields"""
        consolidated = {}
        alt_fields = {}

        for field, value in cleaned_fields.items():
            if field.endswith('_alt'):
                base_field = field[:-4]
                alt_fields[base_field] = value
            else:
                consolidated[field] = value

        # Use alt fields if main fields are empty
        for base_field, alt_value in alt_fields.items():
            if base_field not in consolidated or not consolidated[base_field]:
                consolidated[base_field] = alt_value

        return consolidated

    def extract_contextual_information(self, raw_text: str) -> Dict[str, Any]:
        """Extract contextual information for better LLM understanding"""
        context = {}

        # Extract appointment type context
        if re.search(r'first appointment', raw_text, re.IGNORECASE):
            context['appointment_type'] = 'First Appointment'
        elif re.search(r'reappointment', raw_text, re.IGNORECASE):
            context['appointment_type'] = 'Reappointment'
        elif re.search(r'casual vacancy', raw_text, re.IGNORECASE):
            context['appointment_type'] = 'Casual Vacancy'
        else:
            context['appointment_type'] = 'Unknown'

        # Extract company type information
        if re.search(r'private limited', raw_text, re.IGNORECASE):
            context['company_type'] = 'Private Limited Company'
        elif re.search(r'public limited', raw_text, re.IGNORECASE):
            context['company_type'] = 'Public Limited Company'
        elif re.search(r'one person company', raw_text, re.IGNORECASE):
            context['company_type'] = 'One Person Company'

        # Extract regulatory compliance context
        context['regulatory_sections'] = []
        if re.search(r'section 139', raw_text, re.IGNORECASE):
            context['regulatory_sections'].append('Section 139 - Appointment of Auditors')
        if re.search(r'section 140', raw_text, re.IGNORECASE):
            context['regulatory_sections'].append('Section 140 - Removal of Auditors')

        # Extract AGM context
        agm_match = re.search(r'annual general meeting.*?(\d{1,2}[/-]\d{1,2}[/-]\d{4})', raw_text, re.IGNORECASE)
        if agm_match:
            context['agm_conducted'] = True
            context['agm_date'] = agm_match.group(1)
        else:
            context['agm_conducted'] = False

        # Extract auditor qualification context
        if re.search(r'chartered accountant', raw_text, re.IGNORECASE):
            context['auditor_qualification'] = 'Chartered Accountant'

        # Extract joint auditor context
        if re.search(r'joint auditor', raw_text, re.IGNORECASE):
            context['joint_auditors'] = True
        else:
            context['joint_auditors'] = False

        return context

    def create_llm_ready_summary_data(self, fields: Dict[str, str], raw_text: str) -> Dict[str, Any]:
        """Create structured data optimized for LLM summary generation"""

        # Extract contextual information
        context = self.extract_contextual_information(raw_text)

        # Create LLM-ready structure
        llm_data = {
            "document_type": "ADT-1 Form - Notice of Auditor Appointment",
            "summary_context": {
                "purpose": "This document notifies the Registrar of Companies about the appointment of an auditor",
                "legal_framework": "Filed under the Companies Act, 2013",
                "appointment_nature": context.get('appointment_type', 'Unknown'),
                "compliance_sections": context.get('regulatory_sections', [])
            },

            "company_information": {
                "name": fields.get('company_name', 'Not specified'),
                "cin": fields.get('company_cin', 'Not specified'),
                "type": context.get('company_type', 'Not specified'),
                "email": fields.get('company_email', 'Not specified'),
                "address": self._build_address(fields, 'company'),
                "state": fields.get('company_state', 'Not specified'),
                "pincode": fields.get('company_pincode', 'Not specified')
            },

            "auditor_information": {
                "firm_name": fields.get('auditor_firm_name', 'Not specified'),
                "pan": fields.get('auditor_pan', 'Not specified'),
                "membership_number": fields.get('auditor_membership_number', 'Not specified'),
                "email": fields.get('auditor_email', 'Not specified'),
                "address": self._build_address(fields, 'auditor'),
                "qualification": context.get('auditor_qualification', 'Not specified'),
                "number_of_auditors": fields.get('number_of_auditors', '1'),
                "joint_appointment": context.get('joint_auditors', False)
            },

            "appointment_details": {
                "appointment_date": fields.get('appointment_date', 'Not specified'),
                "audit_period_start": fields.get('audit_period_from', 'Not specified'),
                "audit_period_end": fields.get('audit_period_to', 'Not specified'),
                "financial_years_count": fields.get('number_of_financial_years', 'Not specified'),
                "agm_date": fields.get('agm_date', context.get('agm_date', 'Not specified')),
                "agm_conducted": context.get('agm_conducted', False),
                "resolution_number": fields.get('resolution_number', 'Not specified'),
                "director_din": fields.get('director_din', 'Not specified')
            },

            "compliance_information": {
                "form_filing_date": fields.get('form_date', fields.get('current_date', 'Not specified')),
                "receipt_date": fields.get('receipt_date', 'Not specified'),
                "certificate_serial": fields.get('certificate_serial_number', 'Not specified'),
                "attachments": self._parse_attachments(fields.get('attachments', '')),
                "digital_signature": "Present" if any('sign' in k.lower() for k in fields.keys()) else "Not verified"
            },

            "key_narrative_points": self._extract_narrative_points(fields, context, raw_text),

            "summary_template": {
                "executive_summary": "This ADT-1 form represents the {appointment_nature} of {auditor_firm_name} as auditor for {company_name} (CIN: {company_cin}) for the financial period from {audit_period_start} to {audit_period_end}.",
                "key_parties": "Company: {company_name}, Auditor: {auditor_firm_name}",
                "timeline": "Appointment effective from {appointment_date}, covering {financial_years_count} financial year(s)",
                "compliance_status": "Form filed on {form_filing_date} with certificate serial {certificate_serial}"
            }
        }

        return llm_data

    def _build_address(self, fields: Dict[str, str], prefix: str) -> str:
        """Build complete address from address components"""
        address_parts = []

        for i in range(1, 4):  # address_line1, address_line2, address_line3
            addr_key = f'{prefix}_address_line{i}'
            if addr_key in fields and fields[addr_key]:
                address_parts.append(fields[addr_key])

        # Add city, state, pincode
        city = fields.get(f'{prefix}_city', '')
        state = fields.get(f'{prefix}_state', '')
        pincode = fields.get(f'{prefix}_pincode', '')

        if city:
            address_parts.append(city)
        if state:
            address_parts.append(state)
        if pincode:
            address_parts.append(pincode)

        return ', '.join(address_parts) if address_parts else 'Not specified'

    def _parse_attachments(self, attachments_str: str) -> List[str]:
        """Parse attachment string into list"""
        if not attachments_str:
            return []
        return [att.strip() for att in attachments_str.split(',') if att.strip()]

    def _extract_narrative_points(self, fields: Dict[str, str], context: Dict[str, Any], raw_text: str) -> List[str]:
        """Extract key narrative points for LLM summary generation"""
        points = []

        # Company information
        if fields.get('company_name'):
            points.append(f"The company {fields['company_name']} has appointed an auditor")

        # Appointment type
        if context.get('appointment_type'):
            points.append(f"This is a {context['appointment_type'].lower()}")

        # Auditor information
        if fields.get('auditor_firm_name'):
            points.append(f"The appointed auditor is {fields['auditor_firm_name']}")

        # Joint auditors
        if context.get('joint_auditors'):
            points.append("Joint auditors have been appointed")

        # Audit period
        if fields.get('audit_period_from') and fields.get('audit_period_to'):
            points.append(f"Audit period is from {fields['audit_period_from']} to {fields['audit_period_to']}")

        # Financial years
        if fields.get('number_of_financial_years'):
            points.append(f"Appointment covers {fields['number_of_financial_years']} financial year(s)")

        # AGM information
        if context.get('agm_conducted') and context.get('agm_date'):
            points.append(f"Annual General Meeting was conducted on {context['agm_date']}")

        # Compliance
        if fields.get('form_date'):
            points.append(f"Form was filed on {fields['form_date']}")

        return points

    def generate_llm_prompt_data(self, llm_data: Dict[str, Any]) -> Dict[str, str]:
        """Generate structured prompts for different types of LLM summaries"""

        prompts = {
            "executive_summary_prompt": f"""
            Based on the collected data, generate a concise executive summary:

            Company: {llm_data['company_information']['name']} (CIN: {llm_data['company_information']['cin']})
            Auditor: {llm_data['auditor_information']['firm_name']} (PAN: {llm_data['auditor_information']['pan']})
            Appointment Type: {llm_data['summary_context']['appointment_nature']}
            Audit Period: {llm_data['appointment_details']['audit_period_start']} to {llm_data['appointment_details']['audit_period_end']}
            Financial Years: {llm_data['appointment_details']['financial_years_count']}

            Key Points:
            {chr(10).join(['- ' + point for point in llm_data['key_narrative_points']])}
            """,

            "compliance_summary_prompt": f"""
            Generate a compliance-focused summary for this file:

            Form Filing Date: {llm_data['compliance_information']['form_filing_date']}
            Certificate Serial: {llm_data['compliance_information']['certificate_serial']}
            Legal Framework: {llm_data['summary_context']['legal_framework']}
            Applicable Sections: {', '.join(llm_data['summary_context']['compliance_sections'])}
            Digital Signature: {llm_data['compliance_information']['digital_signature']}
            Attachments: {len(llm_data['compliance_information']['attachments'])} file(s)
            """,

            "business_summary_prompt": f"""
            Create a business-oriented summary of this auditor appointment:

            Company: {llm_data['company_information']['name']}
            Business Type: {llm_data['company_information']['type']}
            Location: {llm_data['company_information']['state']}

            Auditor Firm: {llm_data['auditor_information']['firm_name']}
            Joint Appointment: {'Yes' if llm_data['auditor_information']['joint_appointment'] else 'No'}

            Timeline: {llm_data['appointment_details']['audit_period_start']} to {llm_data['appointment_details']['audit_period_end']}
            AGM Date: {llm_data['appointment_details']['agm_date']}
            """
        }

        return prompts

    def extract_for_llm_summary(self) -> Dict[str, Any]:
        """Main extraction method optimized for LLM summary generation"""
        print("Extracting ADT-1 data for LLM summary generation...")

        # Extract form fields
        print("Extracting form fields...")
        form_fields = self.extract_form_fields_pypdf2()

        # Get raw text
        print("Extracting raw text...")
        raw_text = self.get_raw_text()

        # Clean and consolidate fields
        print("Processing fields...")
        cleaned_fields = self.clean_and_map_form_fields(form_fields)
        consolidated_fields = self.consolidate_duplicate_fields(cleaned_fields)

        # Create LLM-ready data structure
        print("Creating LLM-ready data structure...")
        llm_data = self.create_llm_ready_summary_data(consolidated_fields, raw_text)

        # Generate LLM prompts
        print("Generating LLM prompts...")
        llm_prompts = self.generate_llm_prompt_data(llm_data)

        # Final structure
        final_data = {
            "extraction_metadata": {
                "timestamp": datetime.now().isoformat(),
                "pdf_file": os.path.basename(self.pdf_path),
                "extraction_purpose": "LLM Summary Generation",
                "total_fields_extracted": len(form_fields),
                "processed_fields": len(consolidated_fields)
            },
            "structured_data": llm_data,
            "llm_prompts": llm_prompts,
            "raw_fields": consolidated_fields,  # Keep for reference
            "raw_text_sample": raw_text[:1000] + "..." if len(raw_text) > 1000 else raw_text  # Sample for context
        }

        return final_data


def generate_ai_summary(llm_data: Dict[str, Any]) -> str:
    """Generate a sample AI summary (you can replace this with actual LLM API calls)"""

    company_name = llm_data['structured_data']['company_information']['name']
    auditor_name = llm_data['structured_data']['auditor_information']['firm_name']
    appointment_type = llm_data['structured_data']['summary_context']['appointment_nature']
    audit_period_start = llm_data['structured_data']['appointment_details']['audit_period_start']
    audit_period_end = llm_data['structured_data']['appointment_details']['audit_period_end']
    financial_years = llm_data['structured_data']['appointment_details']['financial_years_count']

    summary = f"""
    📋 Form Summary

    Company: {company_name}
    Auditor: {auditor_name}
    Action: {appointment_type}

    Key Details:
    • Audit Period: {audit_period_start} to {audit_period_end}
    • Duration: {financial_years} financial year(s)
    • Joint Auditors: {'Yes' if llm_data['structured_data']['auditor_information']['joint_appointment'] else 'No'}

    Compliance:
    • Form filed under Companies Act, 2013
    • Digital signature verified
    • Required attachments included

    Business Impact:
    This appointment ensures statutory compliance and independent financial oversight for the specified audit period.
    """

    return summary.strip()


def start() -> None:
    """Process every PDF in pdf/ and save JSON next to it in output/"""
    pdf_dir = Path("pdf")
    output_dir = Path("structured_data")
    output_dir.mkdir(exist_ok=True)

    pdf_files = sorted(pdf_dir.glob("*.pdf"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not pdf_files:
        print("No PDF files found in pdf/.")
        return

    for pdf_path in pdf_files:
        try:
            # Build output path with same stem + .json
            output_path = output_dir / pdf_path.with_suffix(".json").name

            print("\n" + "=" * 100)
            print(f"Processing {pdf_path}  ➜  {output_path}")
            print("=" * 100)

            extractor = Extractor(pdf_path)
            llm_ready_data = extractor.extract_for_llm_summary()

            with output_path.open("w", encoding="utf-8") as f:
                json.dump(llm_ready_data, f, indent=2, ensure_ascii=False)

            print(f"  ✅ Saved JSON to {output_path}")
            print(f"  📊 {llm_ready_data['extraction_metadata']['processed_fields']} fields extracted\n")

            # Print LLM prompts for reference
            print("AVAILABLE LLM PROMPTS:")
            print("-" * 23)
            for prompt_type, prompt_content in llm_ready_data['llm_prompts'].items():
                print(f"\n📝 {prompt_type.upper()}:")
                print(prompt_content.strip())

            print("\n" * 3)

        except Exception as e:
            print(f"  ❌ Error processing {pdf_path.name}: {e}")
            import traceback; traceback.print_exc()
            # continue to next file instead of aborting
            continue


if __name__ == "__main__":
    start()