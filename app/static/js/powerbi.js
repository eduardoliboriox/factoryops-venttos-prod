document.getElementById("setorSelect").addEventListener("change", async e => {
  const setor = e.target.value;
  const linhaSelect = document.getElementById("linhaSelect");

  linhaSelect.innerHTML = "<option>Todas</option>";

  if (setor === "Todos") return;

  const resp = await fetch(`/api/linhas?setor=${setor}`);
  const linhas = await resp.json();

  linhas.forEach(l => {
    const opt = document.createElement("option");
    opt.textContent = l;
    linhaSelect.appendChild(opt);
  });
});

function toggleLinhasPowerBI() {
  const extras = document.querySelectorAll(".extra-linha-powerbi");
  if (!extras.length) return;

  const btn = document.getElementById("toggleLinhasPowerBIBtn");
  const isHidden = extras[0].classList.contains("d-none");

  extras.forEach(el => el.classList.toggle("d-none", !isHidden));
  btn.textContent = isHidden ? "Recolher" : "Ver mais";
}

async function refreshPowerBI() {
  try {
    const params = new URLSearchParams({
      data_inicial: document.getElementById("data_inicial").value,
      data_final: document.getElementById("data_final").value,
      turno: document.getElementById("turno")?.value || '',
      filial: document.getElementById("filial")?.value || ''
    });

    const resp = await fetch(`/api/dashboard/linhas/faltas?${params}`);
    const dados = await resp.json();

    const lista = document.getElementById("rankingLinhasPowerBI");
    lista.innerHTML = "";
    dados.forEach(l => {
      lista.innerHTML += `
        <li class="list-group-item d-flex justify-content-between"
            style="cursor:pointer"
            onclick="abrirModalLinhaPowerBI('${l.linha}')">
          <span>${l.linha}</span>
          <span class="badge bg-danger">${l.absenteismo}%</span>
        </li>`;
    });

  } catch (e) {
    console.error("Erro ao atualizar PowerBI:", e);
  }
}

setInterval(refreshPowerBI, 5000);
refreshPowerBI();
