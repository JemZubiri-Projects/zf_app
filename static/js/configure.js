/********************************************/
/* 0. Utility: DOMContentLoaded wrapper     */
/*    (we still run some things immediately)*/
/********************************************/
/* We'll keep initial behavior but ensure some
   listeners run after DOM ready when helpful. */

/********************************************/
/* 1. LEFT SIDE NAV HIGHLIGHT ONLY          */
/********************************************/
document.querySelectorAll(".side-nav-item").forEach(btn => {
    btn.addEventListener("click", () => {
        document.querySelectorAll(".side-nav-item").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
    });
});


/********************************************/
/* 2. VALIDATION HELPERS (ModelForm IDs)    */
/********************************************/
function validateDuty() {
    const duty = document.getElementById("duty_cycle");
    return duty && duty.value.trim() !== "";
}

function validateConfig() {
    const prop = document.getElementById("propulsion_type");
    const trans = document.getElementById("transmission_config");

    return (
        prop && prop.value.trim() !== "" &&
        trans && trans.value.trim() !== ""
    );
}

function validateManufacturer() {
    const maker = document.getElementById("engine_manufacturer");
    const power = document.getElementById("engine_power");
    const rpm = document.getElementById("engine_rated_rpm");

    return (
        maker && maker.value.trim() !== "" &&
        power && power.value.trim() !== "" &&
        rpm && rpm.value.trim() !== ""
    );
}


/********************************************/
/* 3. ENABLING NEXT BUTTON PER SECTION      */
/********************************************/
function setupValidation() {
    const dutyNext = document.querySelector("button[data-next='config']");
    const configNext = document.querySelector("button[data-next='manufacturer']");
    const manufNext = document.querySelector("button[data-next='complete']");

    function updateButtons() {
        if (dutyNext) {
            dutyNext.disabled = !validateDuty();
            dutyNext.classList.toggle("active", validateDuty());
        }

        if (configNext) {
            configNext.disabled = !validateConfig();
            configNext.classList.toggle("active", validateConfig());
        }

        if (manufNext) {
            manufNext.disabled = !validateManufacturer();
            manufNext.classList.toggle("active", validateManufacturer());
        }
    }

    // validate whenever fields change
    document.querySelectorAll(".form-input, input[type='radio']").forEach(el => {
        el.addEventListener("change", updateButtons);
        el.addEventListener("keyup", updateButtons);
    });

    // run once for pre-populated fields
    updateButtons();
}

/********************************************/
/* 4. CSRF helper for AJAX                  */
/********************************************/
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + "=")) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
const csrftoken = getCookie("csrftoken");


/********************************************/
/* 5. DYNAMIC POWER UNIT SWITCHING          */
/********************************************/
function updatePowerUnit() {
    const unitSystem = document.getElementById("measurement_units");
    const powerLabel = document.getElementById("power-unit");

    if (!unitSystem || !powerLabel) return;

    if (unitSystem.value === "metric") {
        powerLabel.innerText = "kW";
    } else {
        powerLabel.innerText = "hp";
    }
}

// When Duty Cycle changes → fetch allowed Transmission configurations
document.getElementById("duty_cycle")?.addEventListener("change", function () {

    const duty = this.value;
    const transSelect = document.getElementById("transmission_config");

    if (!duty || !transSelect) return;

    fetch(`/products/api/transmission/?duty=${encodeURIComponent(duty)}`)
        .then(r => r.json())
        .then(data => {
            const options = data.configs;

            // Reset dropdown
            transSelect.innerHTML = `<option value="">Select one</option>`;

            // Add allowed configurations
            options.forEach(opt => {
                transSelect.innerHTML += `<option value="${opt}">${opt}</option>`;
            });

            // Clear any previous selection
            transSelect.value = "";
        });
});

document.addEventListener("DOMContentLoaded", function () {
    const pf = document.getElementById("power_factor");
    if (pf) {
        pf.addEventListener("change", function () {
            // submit the parent form only (safe because manufacturer form is the only one on the page when section == 'manufacturer')
            this.form.submit();
        });
    }

    document.getElementById("measurement_units")?.addEventListener("change", updatePowerUnit);
    updatePowerUnit(); // ensure correct on page load
});


/********************************************/
/* 6. INIT                                   */
/********************************************/
setupValidation();


/********************************************/
/* 7. GET QUOTE MODAL + AJAX SUBMIT         */
/*    REPLACEMENT (IDs fixed & robust)      */
/********************************************/
(function () {
    const openBtn = document.getElementById("open-quote-btn");
    const modal = document.getElementById("quote-modal");
    const closeBtn = document.getElementById("quote-modal-close");
    const backdrop = document.getElementById("quote-modal-backdrop");
    const cancelBtn = document.getElementById("quote-cancel");
    const form = document.getElementById("quote-form");
    const submitBtn = document.getElementById("quote-submit");
    const feedback = document.getElementById("quote-feedback");

    if (!openBtn || !modal || !form) {
        // Modal not present on this page — nothing to do.
        return;
    }

    function openModal() {
        modal.classList.add("show");
        modal.setAttribute("aria-hidden", "false");
        const first = modal.querySelector("input[name='project_name']") || document.getElementById("quote-project");
        if (first) first.focus();
    }

    function closeModal() {
        modal.classList.remove("show");
        modal.setAttribute("aria-hidden", "true");
        if (feedback) { feedback.style.display = "none"; feedback.className = "quote-feedback"; feedback.textContent = ""; }
        const errs = modal.querySelectorAll(".field-error");
        errs.forEach(e => { e.style.display = "none"; e.textContent = ""; });
        form.reset();
    }

    openBtn.addEventListener("click", openModal);
    if (closeBtn) closeBtn.addEventListener("click", closeModal);
    if (backdrop) backdrop.addEventListener("click", closeModal);
    if (cancelBtn) cancelBtn.addEventListener("click", closeModal);
    window.addEventListener("keydown", function (ev) {
        if (ev.key === "Escape" && modal.classList.contains("show")) closeModal();
    });

    // Field-level error helpers (target ids like "project" -> #error-project)
    function showFieldError(shortId, message) {
        const el = document.getElementById("error-" + shortId);
        if (!el) return;
        el.style.display = "block";
        el.textContent = message;
    }
    function clearFieldError(shortId) {
        const el = document.getElementById("error-" + shortId);
        if (!el) return;
        el.style.display = "none";
        el.textContent = "";
    }

    form.addEventListener("submit", function (e) {
        e.preventDefault();

        // clear previous feedback
        if (feedback) { feedback.style.display = "none"; feedback.className = "quote-feedback"; feedback.textContent = ""; }

        // Read correct elements by their template IDs
        const projectInput = document.getElementById("quote-project");
        const emailInput = document.getElementById("quote-email");
        const mobileInput = document.getElementById("quote-mobile");
        const configInput = document.getElementById("quote-config-uuid");

        const project_name = (projectInput && projectInput.value) ? projectInput.value.trim() : "";
        const email = (emailInput && emailInput.value) ? emailInput.value.trim() : "";
        const mobile = (mobileInput && mobileInput.value) ? mobileInput.value.trim() : "";
        const config_uuid = (configInput && configInput.value) ? configInput.value : "";


        let hasError = false;

        // Validate project name
        if (!project_name) {
            showFieldError("project", "Project name is required.");
            hasError = true;
        } else {
            clearFieldError("project");
        }

        // Validate email (presence + simple format)
        if (!email) {
            showFieldError("email", "Email address is required.");
            hasError = true;
        } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
            showFieldError("email", "Enter a valid email address.");
            hasError = true;
        } else {
            clearFieldError("email");
        }

        if (hasError) {
            // focus first invalid field
            if (!project_name && projectInput) projectInput.focus();
            else if (!email && emailInput) emailInput.focus();
            return;
        }

        // disable submit button for UX
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.textContent = "Sending…";
        }

        const payload = {
            project_name: project_name,
            email: email,
            mobile: mobile,
            config_uuid: config_uuid
        };

        // POST to the server. Using absolute path consistent with url conf added earlier.
        fetch("/products/get-quote/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrftoken,
                "Accept": "application/json"
            },
            body: JSON.stringify(payload)
        })
            .then(resp => resp.json().catch(() => ({})))
            .then(data => {
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.textContent = "Send Request";
                }

                if (data && data.status === "ok") {
                    if (feedback) {
                        feedback.className = "quote-feedback success";
                        feedback.textContent = "Thanks — your quote request has been sent. We will contact you soon.";
                        feedback.style.display = "block";
                    }
                    // auto-close after a short delay to show success
                    setTimeout(closeModal, 1400);
                } else {
                    if (feedback) {
                        feedback.className = "quote-feedback error";
                        feedback.textContent = data && data.error ? data.error : "An error occurred. Please try again later.";
                        feedback.style.display = "block";
                    }
                }
            })
            .catch(err => {
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.textContent = "Send Request";
                }
                if (feedback) {
                    feedback.className = "quote-feedback error";
                    feedback.textContent = "Network error. Please try again later.";
                    feedback.style.display = "block";
                }
                console.error("Quote submit error:", err);
            });
    });
})();
