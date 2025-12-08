# products/management/commands/import_zf.py
from django.core.management.base import BaseCommand
from django.db import transaction
from products.models import Family, Part, PartAttribute
import pandas as pd
import uuid
import os

class Command(BaseCommand):
    help = "Import ZF Excel master sheet into families, parts and part attributes."

    def add_arguments(self, parser):
        parser.add_argument('excel_path', type=str, help='Path to the Excel file')

    def handle(self, *args, **options):
        path = options['excel_path']
        if not os.path.exists(path):
            self.stderr.write(self.style.ERROR(f"File not found: {path}"))
            return
        xl = pd.ExcelFile(path)
        for sheet_name in xl.sheet_names:
            if sheet_name.lower().startswith('export'):
                continue
            self.stdout.write(f"Processing sheet: {sheet_name}")
            df = xl.parse(sheet_name)
            # family extraction: code + formatted name (CamelCase)
            code = sheet_name.split('_')[0]
            name = self.format_family_name(sheet_name)
            family, created = Family.objects.get_or_create(code=code, defaults={'name': name})
            if not created and family.name != name:
                family.name = name
                family.save()

            # core columns mapping
            core_cols = {"Part Number", "Unit Of Measure", "Part Image", "Data Sheet File"}

            with transaction.atomic():
                for _, row in df.iterrows():
                    pn = row.get("Part Number")
                    if pd.isna(pn):
                        continue
                    pn = str(pn).strip()
                    # upsert part
                    part, pcreated = Part.objects.get_or_create(
                        part_number=pn,
                        family=family,
                        defaults={'uuid': uuid.uuid4(), 
                            'unit_of_measure': self.clean_val(row.get("Unit Of Measure")), 
                            'image_src': self.clean_val(row.get("Part Image")), 
                            'description': self.clean_val(row.get("Description"))
                        }
                    )
                    if not pcreated:
                        changed = False
                        um = self.clean_val(row.get("Unit Of Measure"))
                        img = self.clean_val(row.get("Part Image"))
                        if um and part.unit_of_measure != um:
                            part.unit_of_measure = um
                            changed = True
                        if img and part.image_src != img:
                            part.image_src = img
                            changed = True
                        if changed:
                            part.save()

                    # attributes
                    for col in df.columns:
                        if col in core_cols:
                            continue
                        val = row.get(col)
                        if pd.isna(val):
                            continue
                        val_clean = self.clean_val(val)
                        if val_clean is None:
                            continue
                        # try numeric
                        vnum = None
                        vtext = None
                        vtype = "text"
                        try:
                            vnum = float(val_clean)
                            vtype = "number"
                        except:
                            vtext = str(val_clean)
                        # upsert attribute
                        PartAttribute.objects.create(
                            part=part,
                            name=col,
                            value_text=vtext if vtext is not None else None,
                            value_number=vnum,
                            value_type=vtype
                        )
        self.stdout.write(self.style.SUCCESS("Import finished."))

    def clean_val(self, v):
        if pd.isna(v):
            return None
        if isinstance(v, float) and pd.isna(v):
            return None
        return str(v).strip()

    def format_family_name(self, sheet_name):
        parts = sheet_name.split("_")
        if len(parts) == 1:
            return sheet_name
        raw = parts[1:]
        cleaned = []
        for seg in raw:
            seg = seg.replace("-", " ").replace(" ", "")
            seg = ''.join(ch for ch in seg if ch.isalnum())
            if seg:
                cleaned.append(seg.capitalize())
        return "".join(cleaned)
