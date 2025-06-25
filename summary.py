import os
import json
from pathlib import Path

class Summary():
    def __init__(self, json_path: str):
        self.json_path = json_path

    def generate_summary(self):
        """Generate the executive summary from JSON data without any external dependencies"""

        # Load the JSON data
        with open(self.json_path, 'r') as file:
            data = json.load(file)

        # Extract required fields
        structured_data = data['structured_data']
        company = structured_data['company_information']
        auditor = structured_data['auditor_information']
        appointment = structured_data['appointment_details']
        compliance = structured_data['compliance_information']
        context = structured_data['summary_context']

        # Format the date (remove time if present)
        filing_date = compliance['form_filing_date'].split()[0]

        # Construct the summary
        summary = (
            f"{company['name']} (CIN: {company['cin']}) has appointed "
            f"{auditor['firm_name']} (PAN: {auditor['pan']}) as auditors to fill a "
            f"{context['appointment_nature'].lower()} . The appointment covers an audit period "
            f"from {appointment['audit_period_start']} to {appointment['audit_period_end']}, "
            f"spanning {appointment['financial_years_count']} financial years. This "
            f"{'joint ' if auditor['joint_appointment'] else ''}appointment was formalized under "
            f"{context['compliance_sections'][0]} of the Companies Act, 2013, with the form filed on "
            f"{filing_date} (Certificate Serial: {compliance['certificate_serial']})."
        )

        return summary

def start():
    structured_data_dir = Path("structured_data")
    summary_dir = Path("summary")
    summary_dir.mkdir(exist_ok=True)

    json_files = sorted(structured_data_dir.glob("*.json"))
    if not json_files:
        print("\n❌ No JSON files found in the structured_data folder. Please check and rerun the extractor first.")
        return

    for json_path in json_files:
        try:
            summary_object = Summary(json_path)
            summary = summary_object.generate_summary()

            # Save summary with same base name but .txt extension
            summary_file = json_path.with_suffix(".txt").name
            summary_path = summary_dir / summary_file

            with summary_path.open("w", encoding="utf-8") as f:
                f.write(summary)

            print(f"\n{"="*100}")
            print(f"📄 Summary for {json_path.name}:\n{"="*100} \n{summary}\n")
            print(f"✅ Summary saved to {summary_path}")
            print("\n" * 3)

        except Exception as e:
            print(f"❌ Error generating summary for {json_path.name}: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    start()