import json
import pandas as pd
import os

def save_outputs(invoice_data, verifiability_report, output_dir, base_name):
    with open(os.path.join(output_dir, f"extracted_data_{base_name}.json"), "w") as f:
        json.dump(invoice_data, f, indent=4)
    with open(os.path.join(output_dir, f"verifiability_report_{base_name}.json"), "w") as f:
        json.dump(verifiability_report, f, indent=4)
    df_general = pd.DataFrame([invoice_data]).drop("table_contents", axis=1)
    df_table = pd.DataFrame(invoice_data["table_contents"])
    with pd.ExcelWriter(os.path.join(output_dir, f"extracted_data_{base_name}.xlsx")) as writer:
        df_general.to_excel(writer, sheet_name="General", index=False)
        df_table.to_excel(writer, sheet_name="Table", index=False)