# products/views.py
import json
from decimal import Decimal
from django import forms

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth import logout
from django.core.mail import send_mail
from django.conf import settings
from configurations.models import ProductConfiguration
from products.models import Family, Part, PartAttribute, QuoteRequest
from configurations.forms import DutyForm, ConfigurationForm, ManufacturerForm, PowerForm, SeriesModelForm, AccessoriesForm


def home(request):
    return redirect("products:landing")

@login_required
def configure_product(request):
    section = request.GET.get("section", "duty")
    total_weight = Decimal("0")
    total_price = Decimal("0")

    # Load config from session
    config_uuid = request.session.get("config_uuid")
    config = ProductConfiguration.objects.filter(uuid=config_uuid).first()

    if not config:
        config = ProductConfiguration.objects.create()
        request.session["config_uuid"] = str(config.uuid)

    # Determine completed steps
    duty_done = bool(config.duty_cycle)
    config_done = bool(config.propulsion_type and config.transmission_config)
    manufacturer_done = bool(config.engine_manufacturer and config.power_factor and config.ratio)
    series_done = bool(config.selected_series and config.selected_model)
    summary_done = bool(config.selected_model_name)

    selected_accessories = []
    for field_name, label in AccessoriesForm.ACCESSORY_FIELDS.items():
        val = getattr(config, field_name, None)
        if val:
            selected_accessories.append({
                "label": label,
                "value": val,
            })

    accessories_done = bool(selected_accessories)

    # Enforce step order
    if section == "config" and not duty_done:
        return redirect(f"{request.path}?section=duty")

    if section == "manufacturer" and not config_done:
        return redirect(f"{request.path}?section=config")

    if section == "series" and not manufacturer_done:
        return redirect(f"{request.path}?section=manufacturer")

    if section == "accessories" and not series_done:
        return redirect(f"{request.path}?section=series")

    if section == "summary" and not series_done:
        return redirect(f"{request.path}?section=series")


    # Choose form for current section
    if section == "duty":
        FormClass = DutyForm
        form_kwargs = {"instance": config}

    elif section == "config":
        # Pass duty_cycle so ConfigurationForm can build dynamic transmission options
        FormClass = ConfigurationForm
        form_kwargs = {"instance": config, "duty_cycle": config.duty_cycle}

    elif section == "manufacturer":  # manufacturer
        FormClass = PowerForm
        posted_pf = request.POST.get("power_factor")
        form_kwargs = {
            "instance": config,
            "duty_cycle": config.duty_cycle,
            "propulsion_type": config.propulsion_type,
            "transmission_config": config.transmission_config,
            "power_factor": posted_pf
        }
    elif section == "series":
        FormClass = SeriesModelForm
        form_kwargs = {
            "instance": config,
            "duty_cycle": config.duty_cycle,
            "propulsion_type": config.propulsion_type,
            "transmission_config": config.transmission_config,
            "power_factor": config.power_factor,
            "ratio": config.ratio,
        }
    elif section == "accessories":
        FormClass = AccessoriesForm
        form_kwargs = {
            "instance": config,
            "selected_series": config.selected_series
        }
    elif section == "summary":
        # read-only summary, just a dummy form so code path stays simple
        FormClass = forms.Form
        form_kwargs = {}

    # Handle POST
    if request.method == "POST":
        form = FormClass(request.POST, **form_kwargs)
        if form.is_valid():
            if section == "series":
                selected_series_val = form.cleaned_data.get("series")   # e.g. "2000" (string)
                selected_model_text = form.cleaned_data.get("model")    # e.g. "ZF 2000"

                # Store as strings
                config.selected_series = str(selected_series_val) if selected_series_val else None
                config.selected_model = selected_model_text
                config.save()

                # Build final model name: Product/model + Duty + Config + Ratio
                duty = config.duty_cycle
                cfg = config.transmission_config
                ratio = config.ratio

                parts = []
                if selected_model_text:
                    parts.append(selected_model_text)
                if duty:
                    parts.append(duty.capitalize())
                if cfg:
                    parts.append(cfg)
                if ratio:
                    parts.append(str(ratio))

                if parts:
                    config.selected_model_name = " ".join(parts)
                    config.save()


            else:
                # Normal save for duty/config/manufacturer
                form.save()

            next_section = request.POST.get("next_section")
            return redirect(f"{request.path}?section={next_section}")


    else:
        form = FormClass(**form_kwargs)
        
        # Build specification rows for Summary section
    spec_rows = []

    # ---------- TRANSMISSION ROW ----------
    if config.selected_model:
        # 1) Find matching Part by Product/model == selected_model
        part_qs = PartAttribute.objects.filter(
            name__iexact="Product/model",
            value_text__iexact=config.selected_model
        ).values_list("part_id", flat=True)

        part = Part.objects.filter(id__in=part_qs).first()

        if part:
            attrs = PartAttribute.objects.filter(
                part=part,
                name__in=[
                    "Part/Drawing # Final",
                    "Weight (lb)",
                    "MRM 25% Profit",
                ]
            )

            def get_attr(attrs_list, name, numeric=False):
                a = next((x for x in attrs_list if x.name == name), None)
                if not a:
                    return "-"
                if numeric and a.value_number is not None:
                    return a.value_number
                return a.value_text or a.value_number or "-"

            spec_rows.append({
                "item": "Transmission",
                "description": config.selected_model_name or config.selected_model,
                "part_number": get_attr(attrs, "Part/Drawing # Final"),
                "weight": get_attr(attrs, "Weight (lb)", numeric=True),
                "price": get_attr(attrs, "MRM 25% Profit", numeric=True),
            })

    # ---------- ACCESSORY ROWS ----------
    # config.selected_series is something like "2000" or "2000.0"
    series_num = None
    if config.selected_series:
        try:
            series_num = int(float(config.selected_series))
        except Exception:
            series_num = None

    # Pre-resolve parts that belong to this series (for slightly better performance)
    series_part_ids = []
    if series_num is not None:
        series_part_ids = list(
            PartAttribute.objects.filter(
                name__iexact="Series",
                value_number=series_num
            ).values_list("part_id", flat=True)
        )

    for acc in selected_accessories:
        label = acc["label"]      # e.g. "Bellhousing"
        value = acc["value"]      # the chosen description text

        part = None

        # Try to find a Part in the same series with matching description
        if series_part_ids:
            part = Part.objects.filter(
                id__in=series_part_ids,
                description__iexact=value
            ).first()

        # Fallback: search globally by description
        if not part:
            part = Part.objects.filter(description__iexact=value).first()

        if not part:
            # If even that fails, append a row with unknown part number/weight/price
            spec_rows.append({
                "item": label,
                "description": value,
                "part_number": "-",
                "weight": "-",
                "price": "-",
            })
            continue

        # Fetch attributes for this accessory part
        attrs = PartAttribute.objects.filter(
            part=part,
            name__in=[
                "Drawing #",
                "Weight (lb)",
                "Price (Euros)",
            ]
        )

        def get_attr(attrs_list, name, numeric=False):
            a = next((x for x in attrs_list if x.name == name), None)
            if not a:
                return "-"
            if numeric and a.value_number is not None:
                return a.value_number
            return a.value_text or a.value_number or "-"

        spec_rows.append({
            "item": label,                     # e.g. "Bellhousing"
            "description": value,              # the dropdown selection text
            "part_number": get_attr(attrs, "Drawing #"),
            "weight": get_attr(attrs, "Weight (lb)", numeric=True),
            "price": get_attr(attrs, "Price (Euros)", numeric=True),
        })
        # total_weight = Decimal("0")
        # total_price = Decimal("0")

        for row in spec_rows:
            # weight may be numeric or "-" or None
            w = row.get("weight")

            if w is not None and w != "-":
                try:
                    # ensure Decimal-friendly string
                    total_weight += Decimal(w)
                except Exception:
                    # skip non-numeric values
                    pass

            # price may be numeric or "-" or None
            p = row.get("price")
            if p is not None and p != "-":
                try:
                    total_price += Decimal(p)
                except Exception:
                    pass

    return render(request, "products/configure.html", {
        "form": form,
        "section": section,
        "config": config,
        "duty_done": duty_done,
        "config_done": config_done,
        "manufacturer_done": manufacturer_done,
        "series_done": series_done,
        "accessories_done": accessories_done,
        "selected_accessories": selected_accessories,
        "spec_rows": spec_rows,
        "total_weight": total_weight,
        "total_price": total_price
    })


@login_required
def save_configuration(request):
    if request.method != "POST":
        return HttpResponseForbidden()
    data = json.loads(request.body.decode("utf-8"))
    config_uuid = request.session.get("config_uuid")
    config = None
    if config_uuid:
        config = ProductConfiguration.objects.filter(uuid=config_uuid).first()
    if not config:
        config = ProductConfiguration.objects.create()
        request.session["config_uuid"] = str(config.uuid)

    allowed_fields = {
        "vessel_use","duty_cycle","propulsion_type","hybrid_or_brake","transmission_config",
        "engine_manufacturer","measurement_units","power_factor","engine_rated_rpm",
        "ratio", "selected_series","selected_model"
    }

    for k, v in data.items():
        if k not in allowed_fields:
            continue
        # boolean convert
        if k == "hybrid_or_brake":
            if v in (True, "true", "True", "1", 1):
                setattr(config, k, True)
            else:
                setattr(config, k, False)
        elif k in ("power_factor", "engine_rated_rpm"):
            try:
                if v is None or v == "":
                    setattr(config, k, None)
                else:
                    setattr(config, k, float(v) if k == "power_factor" else int(v))
            except:
                pass
        else:
            setattr(config, k, v)
    config.save()
    return JsonResponse({"status":"ok"})

@login_required
@require_POST
def get_quote(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"status":"error","error":"Invalid payload"}, status=400)

    project = data.get("project_name","").strip()
    email = data.get("email","").strip()
    mobile = data.get("mobile","").strip()
    config_uuid = data.get("config_uuid")

    if not project:
        return JsonResponse({"status":"error","error":"Project name required"}, status=400)
    if not email:
        return JsonResponse({"status":"error","error":"Email required"}, status=400)

    cfg = None
    if config_uuid:
        cfg = ProductConfiguration.objects.filter(uuid=config_uuid).first()

    qr = QuoteRequest.objects.create(
        config=cfg,
        project_name=project,
        email=email,
        mobile=mobile or None,
        created_by=request.user if request.user.is_authenticated else None
    )

    # Optional notification email (wrap in try/except)
    try:
        
        sales_addr = getattr(settings, "SALES_EMAIL", None)
        if sales_addr:
            subject = f"New Quote Request #{qr.id}"
            body = f"Project: {project}\nEmail: {email}\nMobile: {mobile}\nConfig: {config_uuid or 'N/A'}\nID: {qr.id}"
            send_mail(subject, body, getattr(settings, "DEFAULT_FROM_EMAIL", None), [sales_addr], fail_silently=True)
    except Exception:
        pass

    return JsonResponse({"status":"ok","id":qr.id})

def api_transmission_by_duty(request):
    duty = request.GET.get("duty")
    if not duty:
        return JsonResponse({"configs": []})

    selected_decimal = Decimal(str(selected_pf))

    part_ids_pf = PartAttribute.objects.filter(
        part_id__in=part_ids,
        name__iexact="Power Factor (hp/rpm)",
        value_number=selected_decimal
    ).values_list("part_id", flat=True)

    configs = (
        PartAttribute.objects.filter(
            part_id__in=part_ids,
            name__in=["Transmission", "Configuration"]
        )
        .values_list("value_text", flat=True)
        .distinct()
    )

    # 3️⃣ Clean results (remove nulls and blanks)
    configs = sorted([c for c in configs if c and c.strip()])

    return JsonResponse({"configs": configs})


@login_required
def logout_view(request):
    logout(request)
    request.session.flush()
    return redirect("accounts:login")

@login_required
def landing(request):
    return render(request, "products/landing.html")
