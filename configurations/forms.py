# configurations/forms.py
from django import forms
from configurations.models import ProductConfiguration
from django.db.models import Q
from products.models import Family, Part, PartAttribute
from decimal import Decimal
from configurations.utils.model_flags import model_matches_flag

VESSEL_USE = [
    ("", "Select primary use"),
    ("recreational", "Recreational"),
    ("commercial", "Commercial"),
]

DUTY_CHOICES = [
    ("", "Select one"),
    ("pleasure", "Pleasure Duty"),
    ("light", "Light Duty"),
    ("medium", "Medium Duty"),
    ("continuous", "Continuous Duty"),
]

PROPULSION_CHOICES = [
    ("", "Select one"),
    ("shaft", "Shaft Drive"),
    ("water", "Waterjet"),
    ("surface", "Surface Drive"),
    ("thruster", "Thruster"),
]

ENGINE_MAKER_CHOICES = [
    ("", "Select one"),
    ("CAT","Caterpillar"),
    ("CUM","Cumins"),
    ("JOH","John Deere"),
    ("MAN","MAN"),
    ("MTU","MTU"),
    ("SCA","Scania"),
    ("VOL","Volvo Penta"),
    ("YAN","Yanmar"),
    ("OTH","Other"),
]

MEASUREMENT_CHOICES = [
    ("imperial", "hp / in / lb / US qt"),
    ("metric", "kW / mm / kg / L"),
]

HYBRID_CHOICES = [
    ("", "Select one"),
    ("True", "Yes"),
    ("False", "No"),
]

# ================================
# STEP 1 — DUTY FORM
# ================================

class DutyForm(forms.ModelForm):

    vessel_use = forms.ChoiceField(
        choices=VESSEL_USE,
        required=False,
        widget=forms.Select(attrs={"class": "form-input", "id": "vessel_use"})
    )

    duty_cycle = forms.ChoiceField(
        choices=DUTY_CHOICES,
        required=True,
        widget=forms.Select(attrs={"class": "form-input", "id": "duty_cycle"})
    )

    class Meta:
        model = ProductConfiguration
        fields = ["vessel_use", "duty_cycle"]


# ================================
# STEP 2 — CONFIGURATION FORM
# ================================

class ConfigurationForm(forms.ModelForm):
    transmission_config = forms.ChoiceField(
        choices=[],
        widget=forms.Select(attrs={"class": "form-input", "id": "transmission_config"}),
        required=True
    )

    class Meta:
        model = ProductConfiguration
        fields = ["propulsion_type", "hybrid_or_brake", "transmission_config"]
        widgets = {
            "propulsion_type": forms.Select(
                choices=PROPULSION_CHOICES,
                attrs={"class": "form-input", "id": "propulsion_type"}
            ),
            "hybrid_or_brake": forms.RadioSelect(
                choices=HYBRID_CHOICES,
                attrs={"class": "form-radio-inline", "id": "hybrid_or_brake"}
            ),
        }

    def __init__(self, *args, **kwargs):
        duty_cycle = kwargs.pop("duty_cycle", None)
        super().__init__(*args, **kwargs)

        # Default empty
        self.fields["transmission_config"].choices = [("", "Select one")]

        if duty_cycle:


            part_ids = PartAttribute.objects.filter(
                name__iexact="Duty Cycle",
                value_text__iexact=duty_cycle
            ).values_list("part_id", flat=True)

            configs = (
                PartAttribute.objects.filter(
                    part_id__in=part_ids,
                    name__in=["Transmission", "Configuration"]
                )
                .values_list("value_text", flat=True)
                .distinct()
            )

            cleaned = sorted([c for c in configs if c and c.strip()])

            # 3️⃣ Add them as dynamic choices
            self.fields["transmission_config"].choices += [
                (c, c) for c in cleaned
            ]



# ================================
# STEP 3 — MANUFACTURER FORM
# ================================

class ManufacturerForm(forms.ModelForm):

    engine_manufacturer = forms.ChoiceField(
        choices=ENGINE_MAKER_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "form-input", "id": "engine_manufacturer"})
    )

    measurement_units = forms.ChoiceField(
        choices=MEASUREMENT_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "form-input", "id": "measurement_units"})
    )

    power_factor = forms.FloatField(
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-input", "id": "power_factor", "step": "any"})
    )


    class Meta:
        model = ProductConfiguration
        fields = [
            "engine_manufacturer",
            "power_factor"            
        ]

class PowerForm(forms.ModelForm):
    engine_manufacturer = forms.ChoiceField(
        choices=ENGINE_MAKER_CHOICES,
        required=True,
        widget=forms.Select(attrs={"class": "form-input", "id": "engine_manufacturer"})
    )

    power_factor = forms.ChoiceField(
        choices=[],
        required=True,
        widget=forms.Select(attrs={"class": "form-input", "id": "power_factor"}),
    )

    ratio = forms.ChoiceField(
        choices=[],
        required=True,
        widget=forms.Select(attrs={"class": "form-input", "id": "ratio"}),
    )

    class Meta:
        model = ProductConfiguration
        fields = ["engine_manufacturer", "power_factor", "ratio"]

    def __init__(self, *args, **kwargs):
        duty = kwargs.pop("duty_cycle", None)
        propulsion = kwargs.pop("propulsion_type", None)
        config_type = kwargs.pop("transmission_config", None)
        selected_pf = kwargs.pop("power_factor", None)

        super().__init__(*args, **kwargs)

        # Restore PF from DB instance if not posted
        if selected_pf is None and self.instance.power_factor:
            selected_pf = str(self.instance.power_factor)

        self.fields["power_factor"].choices = [("", "Select power factor")]
        self.fields["ratio"].choices = [("", "Select ratio")]

        if not (duty and propulsion and config_type):
            return

        # Filter by duty
        part_ids = PartAttribute.objects.filter(
            name__iexact="Duty Cycle",
            value_text__iexact=duty
        ).values_list("part_id", flat=True)

        # Filter by configuration
        part_ids = PartAttribute.objects.filter(
            part_id__in=part_ids,
            name__in=["Configuration", "Transmission"],
            value_text__iexact=config_type
        ).values_list("part_id", flat=True)

        # Collect PFs
        pf_raw = PartAttribute.objects.filter(
            part_id__in=part_ids,
            name__iexact="Power Factor (hp/rpm)"
        ).values_list("value_number", flat=True).distinct()

        pf_values = [Decimal(str(v)) for v in pf_raw if v is not None]
        pf_values = sorted(pf_values)

        self.fields["power_factor"].choices += [
            (str(v), str(v)) for v in pf_values
        ]

        # No PF selected → stop here
        if not selected_pf:
            return

        selected_decimal = Decimal(str(selected_pf))

        # Get parts matching EXACT PF
        pf_part_ids = PartAttribute.objects.filter(
            part_id__in=part_ids,
            name__iexact="Power Factor (hp/rpm)",
            value_number=selected_decimal
        ).values_list("part_id", flat=True)

        # Pull ratios for those parts
        ratio_attrs = PartAttribute.objects.filter(
            part_id__in=pf_part_ids,
            name__iexact="Ratio"
        ).values("value_text", "value_number")

        cleaned = []

        for attr in ratio_attrs:
            txt = attr["value_text"]
            num = attr["value_number"]

            if txt:
                parts = [
                    p.strip().replace("*", "")
                    for p in txt.split(",")
                    if p.strip()
                ]
                cleaned.extend(parts)
            elif num is not None:
                cleaned.append(str(num))
        cleaned = sorted(set(cleaned), key=lambda x: float(x))

        self.fields["ratio"].choices += [(r, r) for r in cleaned]

class SeriesModelForm(forms.ModelForm):

    series = forms.ChoiceField(
        choices=[],
        required=True,
        widget=forms.Select(attrs={"class": "form-input", "id": "series"})
    )

    model = forms.ChoiceField(
        choices=[],
        required=True,
        widget=forms.Select(attrs={"class": "form-input", "id": "model"})
    )

    class Meta:
        model = ProductConfiguration
        fields = ["selected_series", "selected_model"]

    def __init__(self, *args, **kwargs):
        duty = kwargs.pop("duty_cycle", None)
        propulsion = kwargs.pop("propulsion_type", None)
        config_type = kwargs.pop("transmission_config", None)
        power_factor = kwargs.pop("power_factor", None)
        ratio = kwargs.pop("ratio", None)

        super().__init__(*args, **kwargs)

        # Default placeholder options
        self.fields["series"].choices = [("", "Select series")]
        self.fields["model"].choices = [("", "Select model")]

        # Stop if required values missing
        if not (duty and propulsion and config_type and power_factor and ratio):
            return

        # ---------------------------------------------------------
        # 1) Filter PARTS matching all previous conditions
        # ---------------------------------------------------------

        # Duty cycle filter
        part_ids = PartAttribute.objects.filter(
            name__iexact="Duty Cycle",
            value_text__iexact=duty
        ).values_list("part_id", flat=True)

        # Configuration filter
        part_ids = PartAttribute.objects.filter(
            part_id__in=part_ids,
            name__in=["Configuration", "Transmission"],
            value_text__iexact=config_type
        ).values_list("part_id", flat=True)

        # Power factor filter
        from decimal import Decimal
        part_ids = PartAttribute.objects.filter(
            part_id__in=part_ids,
            name__iexact="Power Factor (hp/rpm)",
            value_number=Decimal(str(power_factor))
        ).values_list("part_id", flat=True)

        # Ratio filter — substring search because ratios are comma-separated
        ratio_str = str(ratio)
        ratio_num = float(ratio)
        part_ids = (
            PartAttribute.objects.filter(
                part_id__in=part_ids,
                name__iexact="Ratio"
            )
            .filter(
                Q(value_text__icontains=ratio_str) |
                Q(value_number=ratio_num)
            )
            .values_list("part_id", flat=True)
        )

        matched_parts = Part.objects.filter(id__in=part_ids)

        # ---------------------------------------------------------
        # 2) Build SERIES dropdown using "Series" attribute or family code
        # ---------------------------------------------------------
        series_values = []
        for p in matched_parts:
            series_attr = p.attributes.filter(name__iexact="Series").first()
            if series_attr:
                val = str(series_attr.value_number).strip()
                if val:
                    series_values.append(val)

        # unique + sorted
        series_values = sorted(list(set(series_values)), key=lambda x: float(x))

        self.fields["series"].choices += [(s, s) for s in series_values]

        # Pre-select if only one
        if len(series_values) == 1:
            self.initial["series"] = series_values[0]

        # ---------------------------------------------------------
        # 3) Build MODEL dropdown using "Product/model" attribute
        # ---------------------------------------------------------
        model_names = []
        for p in matched_parts:
            model_attr = p.attributes.filter(name__iexact="Product/model").first()

            if model_attr and model_attr.value_text:
                cleaned = model_attr.value_text.strip()
            else:
                cleaned = p.part_number  # fallback

            if cleaned:
                model_names.append(cleaned)

        model_names = sorted(list(set(model_names)))

        self.fields["model"].choices += [(m, m) for m in model_names]

        # Auto-select single model
        if len(model_names) == 1:
            self.initial["model"] = model_names[0]

    def save(self, commit=True):
        obj = super().save(commit=False)

        # Pull chosen values from cleaned_data
        model_name = self.cleaned_data.get("selected_model")
        duty = self.instance.duty_cycle
        config = self.instance.transmission_config
        ratio = self.instance.ratio

        # Build final name (skip blanks gracefully)
        parts = []

        if model_name:
            parts.append(model_name)
        if duty:
            parts.append(duty)
        if config:
            parts.append(config)
        if ratio:
            parts.append(str(ratio))

        final_name = " ".join(parts).strip()

        obj.selected_model_name = final_name

        if commit:
            obj.save()

        return obj

# ================================
# STEP 5 — ACCESSORIES FORM
# ================================
class AccessoriesForm(forms.ModelForm):

    ACCESSORY_FIELDS = {
        "bellhousing": "Bellhousing",
        "actuation": "Actuation",
        "trolling": "Trolling",
        "mountings": "Mountings",
        "pto": "Pto",
        "ptishaftbrake": "PtiShaftBrake",
        "trailingpump": "TrailingPump",
        "propflange": "PropFlange",
        "inputflange": "InputFlange",
        "monitoring": "Monitoring",
    }

    bellhousing = forms.ChoiceField(required=False, choices=[], widget=forms.Select(attrs={"class": "form-input"}))
    actuation = forms.ChoiceField(required=False, choices=[], widget=forms.Select(attrs={"class": "form-input"}))
    trolling = forms.ChoiceField(required=False, choices=[], widget=forms.Select(attrs={"class": "form-input"}))
    mountings = forms.ChoiceField(required=False, choices=[], widget=forms.Select(attrs={"class": "form-input"}))
    pto = forms.ChoiceField(required=False, choices=[], widget=forms.Select(attrs={"class": "form-input"}))
    ptishaftbrake = forms.ChoiceField(required=False, choices=[], widget=forms.Select(attrs={"class": "form-input"}))
    trailingpump = forms.ChoiceField(required=False, choices=[], widget=forms.Select(attrs={"class": "form-input"}))
    propflange = forms.ChoiceField(required=False, choices=[], widget=forms.Select(attrs={"class": "form-input"}))
    inputflange = forms.ChoiceField(required=False, choices=[], widget=forms.Select(attrs={"class": "form-input"}))
    monitoring = forms.ChoiceField(required=False, choices=[], widget=forms.Select(attrs={"class": "form-input"}))

    class Meta:
        model = ProductConfiguration
        fields = [
            "bellhousing", "actuation", "trolling", "mountings",
            "pto", "ptishaftbrake", "trailingpump",
            "propflange", "inputflange", "monitoring"
        ]

    def __init__(self, *args, **kwargs):
        selected_series = kwargs.pop("selected_series", None)
        super().__init__(*args, **kwargs)

        selected_model = self.instance.selected_model

        # Normalize series (e.g. "2000.0" → 2000)
        if selected_series:
            try:
                selected_series = int(float(selected_series))
            except Exception:
                selected_series = None

        # Default blank option
        for f in self.ACCESSORY_FIELDS:
            self.fields[f].choices = [("", "Select")]

        if not selected_series or not selected_model:
            return

        for field_name, family_name in self.ACCESSORY_FIELDS.items():
            parts = (
                Part.objects
                .filter(
                    family__name__iexact=family_name,
                    attributes__name__iexact="Series",
                    attributes__value_number=selected_series
                )
                .distinct()
            )

            valid_options = set()

            for part in parts:
                flag_attrs = PartAttribute.objects.filter(
                    part=part,
                    value_text__iexact="X"
                ).exclude(
                    name__in=["Series", "Description", "MRM 25% Profit"]
                )

                for flag in flag_attrs:
                    if model_matches_flag(
                        selected_model=selected_model,
                        flag=flag.name,
                        selected_series=selected_series
                    ):
                        if part.description:
                            valid_options.add(part.description.strip())
                        break

            # ✅ If no valid options → remove field entirely
            if not valid_options:
                self.fields.pop(field_name, None)
                continue

            # ✅ Otherwise populate choices
            self.fields[field_name].choices += [
                (v, v) for v in sorted(valid_options)
            ]
