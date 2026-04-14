document.addEventListener("DOMContentLoaded", () => {

  const zipInput = document.getElementById("zip_code");
  if (zipInput) {
    zipInput.addEventListener("blur", async () => {
      const cep = zipInput.value.replace(/\D/g, "");
      if (cep.length !== 8) return;
      try {
        const response = await fetch(`https://viacep.com.br/ws/${cep}/json/`);
        const data = await response.json();
        if (data.erro) { alert("CEP não encontrado"); return; }
        document.getElementById("street").value = data.logradouro || "";
        document.getElementById("neighborhood").value = data.bairro || "";
        document.getElementById("city").value = data.localidade || "";
        document.getElementById("state").value = data.uf || "";
      } catch (error) {
        console.error("Erro ao consultar CEP", error);
      }
    });
  }

  document.querySelectorAll(".btn-eye").forEach(btn => {
    btn.addEventListener("click", () => {
      const input = document.getElementById(btn.dataset.target);
      const icon = btn.querySelector("i");
      if (input.type === "password") {
        input.type = "text";
        icon.className = "bi bi-eye-slash";
      } else {
        input.type = "password";
        icon.className = "bi bi-eye";
      }
    });
  });

  const passwordInput  = document.getElementById("password");
  const confirmInput   = document.getElementById("password_confirm");
  const requirementsEl = document.getElementById("passwordRequirements");
  const confirmStatus  = document.getElementById("confirmStatus");

  if (passwordInput && requirementsEl) {
    const checks = {
      "req-length":  v => v.length >= 10,
      "req-upper":   v => /[A-Z]/.test(v),
      "req-lower":   v => /[a-z]/.test(v),
      "req-number":  v => /[0-9]/.test(v),
      "req-special": v => /[@$#!%&*]/.test(v),
    };

    function updateRequirements() {
      const val = passwordInput.value;
      Object.entries(checks).forEach(([id, test]) => {
        const li = document.getElementById(id);
        if (!li) return;
        const ok = test(val);
        li.classList.toggle("req-met", ok);
        li.classList.toggle("req-unmet", !ok && val.length > 0);
        li.querySelector("i").className = ok
          ? "bi bi-check-circle-fill"
          : "bi bi-x-circle";
      });
      if (confirmInput && confirmInput.value) updateConfirm();
    }

    function updateConfirm() {
      if (!confirmInput || !confirmStatus) return;
      if (!confirmInput.value) {
        confirmStatus.innerHTML = "";
        confirmStatus.className = "confirm-status";
        return;
      }
      const match = confirmInput.value === passwordInput.value;
      confirmStatus.innerHTML = match
        ? '<i class="bi bi-check-circle-fill"></i> Senhas coincidem'
        : '<i class="bi bi-x-circle"></i> Senhas não coincidem';
      confirmStatus.className = match ? "confirm-status match" : "confirm-status mismatch";
    }

    passwordInput.addEventListener("focus", () => {
      requirementsEl.classList.add("visible");
    });

    passwordInput.addEventListener("input", updateRequirements);

    if (confirmInput) {
      confirmInput.addEventListener("input", updateConfirm);
    }
  }

  const userType = document.getElementById("user_type");
  const matriculaField = document.getElementById("matricula_field");
  if (userType && matriculaField) {
    function toggleMatricula() {
      if (userType.value === "CLT") {
        matriculaField.setAttribute("required", "required");
        matriculaField.placeholder = "Matrícula real (obrigatória)";
      } else {
        matriculaField.removeAttribute("required");
        matriculaField.placeholder = "Matrícula (não obrigatória)";
        matriculaField.value = "";
      }
    }
    userType.addEventListener("change", toggleMatricula);
    toggleMatricula();
  }

});
