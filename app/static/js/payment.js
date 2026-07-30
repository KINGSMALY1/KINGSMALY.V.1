let selectedPlanId = null;

const overlay = document.getElementById("email-modal");
const emailInput = document.getElementById("email-input");
const emailError = document.getElementById("email-error");
const confirmBtn = document.getElementById("email-confirm");

function openEmailModal(planId) {
    selectedPlanId = planId;
    emailError.textContent = "";
    emailInput.value = "";
    overlay.classList.add("open");
    setTimeout(() => emailInput.focus(), 50);
}

function closeEmailModal() {
    overlay.classList.remove("open");
    selectedPlanId = null;
}

function isValidEmail(value) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
}

document.querySelectorAll(".buy-plan").forEach(button => {
    button.addEventListener("click", () => openEmailModal(button.dataset.plan));
});

document.getElementById("email-cancel").addEventListener("click", closeEmailModal);

overlay.addEventListener("click", (e) => {
    if (e.target === overlay) closeEmailModal();
});

emailInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") confirmBtn.click();
});

confirmBtn.addEventListener("click", async () => {
    const email = emailInput.value.trim();

    if (!isValidEmail(email)) {
        emailError.textContent = "Enter a valid email address.";
        return;
    }

    emailError.textContent = "";
    confirmBtn.disabled = true;
    confirmBtn.innerHTML = '<span class="spinner"></span>Processing…';

    try {
        const response = await fetch("/api/payment/initialize", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ plan_id: selectedPlanId, email: email }),
        });

        const data = await response.json();

        // Paystack nests this under data.data.authorization_url
        if (data && data.data && data.data.authorization_url) {
            window.location.href = data.data.authorization_url;
        } else {
            emailError.textContent = data.message || "Something went wrong starting your payment.";
            confirmBtn.disabled = false;
            confirmBtn.textContent = "Continue to Pay";
        }
    } catch (e) {
        emailError.textContent = "Couldn't reach the server. Check your connection and try again.";
        confirmBtn.disabled = false;
        confirmBtn.textContent = "Continue to Pay";
    }
});
