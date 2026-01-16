const API_DEFAULT_PORT = "5000";
const isLocalHost =
  window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";
const API_BASE_URL =
  window.API_BASE_URL ||
  (isLocalHost
    ? `${window.location.protocol}//${window.location.hostname}:${window.API_PORT || API_DEFAULT_PORT}`
    : "");
const EMAIL_PATTERN =
  /^[a-zA-Z0-9._%+-]+@(online|pilani|hyderabad|goa|dubai)\.bits-pilani\.ac\.in$/i;
const REQUEST_BUTTON_TEXT = "Request OTP";

const selectors = {
  themeToggle: document.getElementById("theme-toggle"),
  usernameInput: document.getElementById("username-input"),
  submitBtn: document.getElementById("submit-btn"),
  step1: document.getElementById("step-1"),
  step2: document.getElementById("step-2"),
  step3: document.getElementById("step-3"),
  emailInput: document.getElementById("email-input"),
  emailSubmitBtn: document.getElementById("email-submit-btn"),
  otpInput: document.getElementById("otp-input"),
  otpSubmitBtn: document.getElementById("otp-submit-btn"),
  statusMessage: document.getElementById("status-message"),
  checkStatusBtn: document.getElementById("check-status-btn"),
  resendOtpBtn: document.getElementById("resend-otp-btn"),
  statusCard: document.getElementById("status-card"),
  statusLabel: document.getElementById("status-label"),
  statusDetail: document.getElementById("status-detail"),
  displayEmail: document.getElementById("display-email"),
  displayUsername: document.getElementById("display-username"),
  displayUid: document.getElementById("display-uid"),
  backBtn: document.getElementById("back-btn"),
};

const state = {
  username: localStorage.getItem("username") || "",
  email: localStorage.getItem("email") || "",
  status: localStorage.getItem("status") || "not_started",
  otpRequestedAt: Number(localStorage.getItem("otpRequestedAt")) || 0,
  otpCooldown: 60,
};

let cooldownTimer = null;
let cooldownActive = false;

function sanitizeEmail(email = "") {
  return email.trim();
}

function isValidBitsEmail(email = "") {
  return EMAIL_PATTERN.test(sanitizeEmail(email));
}

function initTheme() {
  const savedTheme = localStorage.getItem("theme");
  const prefersLight =
    window.matchMedia && window.matchMedia("(prefers-color-scheme: light)").matches;
  const initialTheme = savedTheme || (prefersLight ? "light" : "dark");
  document.documentElement.setAttribute("data-theme", initialTheme);
}

function toggleTheme() {
  const currentTheme = document.documentElement.getAttribute("data-theme");
  const newTheme = currentTheme === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", newTheme);
  localStorage.setItem("theme", newTheme);
}

function debounce(fn, wait = 300) {
  let timeout;
  return function (...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => fn.apply(this, args), wait);
  };
}

function setStatus(message, type = "info") {
  if (!selectors.statusMessage) return;
  selectors.statusMessage.textContent = message;
  selectors.statusMessage.dataset.type = type;
}

function updateDashboard(statusData) {
  if (!selectors.statusLabel) return;
  const { status, uid, verified_at, expiry } = statusData;
  selectors.statusLabel.textContent = status.replace(/_/g, " ");
  let detail = "No active request. Please start verification.";
  if (status === "verified") {
    detail = verified_at
      ? `Verified at ${new Date(verified_at).toLocaleString()}`
      : "Verified";
  } else if (status === "pending") {
    detail = expiry
      ? `OTP valid until ${new Date(expiry * 1000).toLocaleTimeString()}`
      : "OTP pending verification";
  }
  selectors.statusDetail.textContent = detail;
  selectors.displayUid.textContent = uid || "N/A";
  selectors.statusCard.classList.remove("success", "error", "pending");
  if (status === "verified") selectors.statusCard.classList.add("success");
  else if (status === "pending") selectors.statusCard.classList.add("pending");
  else selectors.statusCard.classList.add("error");
}

function persistState() {
  localStorage.setItem("username", state.username);
  localStorage.setItem("email", state.email);
  localStorage.setItem("status", state.status);
  localStorage.setItem("otpRequestedAt", state.otpRequestedAt.toString());
}

function updateActionButtons() {
  const typedEmail = selectors.emailInput ? sanitizeEmail(selectors.emailInput.value) : "";
  const effectiveEmail = typedEmail || state.email;
  const hasValidEmail = isValidBitsEmail(effectiveEmail);
  if (selectors.checkStatusBtn) {
    selectors.checkStatusBtn.disabled = !hasValidEmail;
  }
  if (selectors.resendOtpBtn) {
    selectors.resendOtpBtn.disabled = state.status !== "pending";
  }
}

function updateFormVisibility() {
  if (selectors.step1) selectors.step1.style.display = "block";
  if (selectors.step2) selectors.step2.style.display = state.username ? "block" : "none";
  if (selectors.step3) {
    const shouldShowOtp = state.status === "pending" && state.otpRequestedAt > 0;
    selectors.step3.style.display = shouldShowOtp ? "block" : "none";
  }
  if (selectors.displayEmail) selectors.displayEmail.textContent = state.email || "N/A";
  if (selectors.displayUsername) selectors.displayUsername.textContent = state.username || "N/A";
  updateActionButtons();
}

function validateUsername() {
  if (!selectors.usernameInput || !selectors.submitBtn) return;
  const value = selectors.usernameInput.value.trim();
  selectors.submitBtn.disabled = value.length < 2 || value.length > 32;
}

function validateEmail() {
  if (!selectors.emailInput || !selectors.emailSubmitBtn) return;
  const email = sanitizeEmail(selectors.emailInput.value);
  selectors.emailSubmitBtn.disabled = !isValidBitsEmail(email);
  updateActionButtons();
}

function validateOtp() {
  if (!selectors.otpInput || !selectors.otpSubmitBtn) return;
  const otp = selectors.otpInput.value.trim();
  selectors.otpSubmitBtn.disabled = !/^[0-9]{6}$/.test(otp);
}

function clearCooldownTimer() {
  if (cooldownTimer) {
    clearInterval(cooldownTimer);
    cooldownTimer = null;
  }
}

function setCooldown(seconds) {
  if (!selectors.emailSubmitBtn) return;
  clearCooldownTimer();
  cooldownActive = false;
  if (seconds <= 0) {
    selectors.emailSubmitBtn.disabled = false;
    selectors.emailSubmitBtn.textContent = REQUEST_BUTTON_TEXT;
    updateActionButtons();
    return;
  }
  cooldownActive = true;
  let remaining = seconds;
  selectors.emailSubmitBtn.disabled = true;
  selectors.emailSubmitBtn.textContent = `Please wait ${remaining}s`;
  if (selectors.resendOtpBtn) selectors.resendOtpBtn.disabled = true;
  cooldownTimer = setInterval(() => {
    remaining -= 1;
    if (remaining <= 0) {
      clearCooldownTimer();
      selectors.emailSubmitBtn.disabled = false;
      selectors.emailSubmitBtn.textContent = REQUEST_BUTTON_TEXT;
      cooldownActive = false;
      updateActionButtons();
    } else {
      selectors.emailSubmitBtn.textContent = `Please wait ${remaining}s`;
    }
  }, 1000);
}

function resumeCooldownIfNeeded() {
  if (!state.otpRequestedAt || !selectors.emailSubmitBtn) return;
  const elapsed = Math.floor((Date.now() - state.otpRequestedAt) / 1000);
  const remaining = state.otpCooldown - elapsed;
  if (remaining > 0) {
    setCooldown(remaining);
  } else {
    selectors.emailSubmitBtn.disabled = false;
    selectors.emailSubmitBtn.textContent = REQUEST_BUTTON_TEXT;
  }
}

async function requestOtp() {
  if (!state.username) {
    setStatus("Enter your Discord username first.", "error");
    return;
  }
  if (!isValidBitsEmail(state.email)) {
    setStatus("Use your @*.bits-pilani.ac.in email.", "error");
    return;
  }
  if (cooldownActive) {
    setStatus("Please wait before requesting another OTP.", "error");
    return;
  }

  const payload = new URLSearchParams({
    email: state.email,
    username: state.username,
  });

  try {
    setStatus("Requesting OTP...", "info");
    const response = await fetch(`${API_BASE_URL}/verify`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: payload.toString(),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || data.message || "Failed to request OTP");
    }
    state.status = "pending";
    state.otpRequestedAt = Date.now();
    persistState();
    updateFormVisibility();
    setCooldown(state.otpCooldown);
    if (selectors.otpInput) selectors.otpInput.value = "";
    if (selectors.otpSubmitBtn) selectors.otpSubmitBtn.disabled = false;
    setStatus(data.message || "OTP sent successfully.", "success");
  } catch (error) {
    const message = error.message || "Failed to request OTP";
    setStatus(message, "error");
    if (message.includes("1 minute")) {
      const elapsed = Math.floor((Date.now() - state.otpRequestedAt) / 1000);
      setCooldown(Math.max(5, state.otpCooldown - elapsed));
    }
  }
}

async function checkStatus(emailOverride) {
  const candidate = sanitizeEmail(
    emailOverride || selectors.emailInput?.value || state.email,
  );
  if (!isValidBitsEmail(candidate)) {
    setStatus("Enter a valid @*.bits-pilani.ac.in email.", "error");
    return;
  }

  state.email = candidate;
  persistState();
  if (selectors.emailInput) selectors.emailInput.value = candidate;

  try {
    setStatus("Checking status...", "info");
    const response = await fetch(
      `${API_BASE_URL}/verify/status/${encodeURIComponent(candidate)}`,
    );
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Failed to check status");
    }
    state.status = data.status;
    if (data.status !== "pending") {
      state.otpRequestedAt = 0;
    }
    persistState();
    updateFormVisibility();
    if (selectors.otpInput) selectors.otpInput.value = "";
    if (selectors.otpSubmitBtn) selectors.otpSubmitBtn.disabled = data.status !== "pending";
    if (selectors.resendOtpBtn) selectors.resendOtpBtn.disabled = data.status !== "pending";
    updateActionButtons();
    updateDashboard(data);
    setStatus(`Status: ${data.status}`, data.status === "verified" ? "success" : "info");
    if (data.status === "verified" && selectors.step3) {
      selectors.step3.style.display = "none";
    }
  } catch (error) {
    setStatus(error.message || "Failed to check status", "error");
  }
}

async function submitOtp() {
  if (!selectors.otpInput) return;
  const otp = selectors.otpInput.value.trim();
  if (!state.email || state.status !== "pending") {
    setStatus("Request an OTP before entering the code.", "error");
    return;
  }
  if (!/^[0-9]{6}$/.test(otp)) {
    setStatus("Enter a 6-digit OTP.", "error");
    return;
  }

  const payload = new URLSearchParams({
    email: state.email,
    username: state.username,
    otp,
  });

  try {
    setStatus("Verifying OTP...", "info");
    const response = await fetch(`${API_BASE_URL}/verify/otp`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: payload.toString(),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || data.message || "Failed to verify OTP");
    }
    selectors.otpInput.value = "";
    if (selectors.otpSubmitBtn) selectors.otpSubmitBtn.disabled = true;
    setStatus(data.message || "OTP verified.", "success");
    await checkStatus(state.email);
  } catch (error) {
    setStatus(error.message || "Failed to verify OTP", "error");
  }
}

function attachEventListeners() {
  selectors.themeToggle?.addEventListener("click", toggleTheme);

  if (selectors.usernameInput) {
    selectors.usernameInput.addEventListener("input", validateUsername);
    selectors.usernameInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter" && selectors.submitBtn && !selectors.submitBtn.disabled) {
        selectors.submitBtn.click();
      }
    });
  }

  selectors.submitBtn?.addEventListener("click", (e) => {
    e.preventDefault();
    if (!selectors.usernameInput) return;
    state.username = selectors.usernameInput.value.trim();
    persistState();
    updateFormVisibility();
    selectors.emailInput?.focus();
  });

  selectors.usernameInput?.addEventListener("blur", () => {
    if (!selectors.usernameInput) return;
    const value = selectors.usernameInput.value.trim();
    if (value !== state.username) {
      state.username = value;
      persistState();
      updateFormVisibility();
    }
  });

  if (selectors.emailInput) {
    selectors.emailInput.addEventListener("input", debounce(validateEmail));
    selectors.emailInput.addEventListener("keypress", (e) => {
      if (
        e.key === "Enter" &&
        selectors.emailSubmitBtn &&
        !selectors.emailSubmitBtn.disabled
      ) {
        selectors.emailSubmitBtn.click();
      }
    });
  }

  selectors.emailSubmitBtn?.addEventListener("click", async (e) => {
    e.preventDefault();
    if (!selectors.emailInput) return;
    const email = sanitizeEmail(selectors.emailInput.value);
    if (!isValidBitsEmail(email)) {
      setStatus("Use your @*.bits-pilani.ac.in email.", "error");
      return;
    }
    state.email = email;
    persistState();
    if (!cooldownActive) {
      await requestOtp();
    }
  });

  if (selectors.otpInput) {
    selectors.otpInput.addEventListener("input", validateOtp);
    selectors.otpInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter" && selectors.otpSubmitBtn && !selectors.otpSubmitBtn.disabled) {
        selectors.otpSubmitBtn.click();
      }
    });
  }

  selectors.otpSubmitBtn?.addEventListener("click", async (e) => {
    e.preventDefault();
    await submitOtp();
  });

  selectors.checkStatusBtn?.addEventListener("click", async () => {
    await checkStatus();
  });

  selectors.resendOtpBtn?.addEventListener("click", async () => {
    await requestOtp();
  });

  selectors.backBtn?.addEventListener("click", () => {
    window.location.href = "index.html";
  });
}

function hydrateFromStorage() {
  if (selectors.usernameInput) selectors.usernameInput.value = state.username;
  if (selectors.emailInput) selectors.emailInput.value = state.email;
  validateUsername();
  validateEmail();
  validateOtp();
}

function init() {
  initTheme();
  hydrateFromStorage();
  updateFormVisibility();
  attachEventListeners();
  resumeCooldownIfNeeded();
  if (state.status !== "not_started") {
    checkStatus(state.email);
  }
}

document.addEventListener("DOMContentLoaded", init);
