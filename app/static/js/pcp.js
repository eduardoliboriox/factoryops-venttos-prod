function limparPCP() {
  document.getElementById("totalOp").value = "";
  document.getElementById("produzido").value = "";
  document.getElementById("horaInicio").value = "";
  document.getElementById("metaHora").value = "";
  document.getElementById("blank").value = "";
  document.getElementById("resultadoPCP").innerHTML = "";
}

function calcularPCP() {
  const totalOp = Number(document.getElementById("totalOp").value || 0);
  const produzido = Number(document.getElementById("produzido").value || 0);
  const horaInicio = document.getElementById("horaInicio").value;
  const metaHora = Number(document.getElementById("metaHora").value || 0);
  const blank = Number(document.getElementById("blank").value || 1);
  const refeicao = document.getElementById("refeicao").value === "true";

  const turnos = Array.from(document.querySelectorAll("#pcpTurnos input[type='checkbox']:checked"))
    .map(cb => Number(cb.value));

  if (!totalOp || !metaHora || !horaInicio) {
    document.getElementById("resultadoPCP").innerHTML =
      `<div class="alert alert-warning mb-0">Preencha: Quantidade OP, Início e Meta/hora.</div>`;
    return;
  }

  const restante = Math.max(totalOp - produzido, 0);

  // meta em placas/hora -> por minuto
  const metaMin = metaHora / 60;
  const metaMinPlacasReais = metaMin; // já em placas
  const minutosNecessarios = metaMinPlacasReais > 0 ? (restante / metaMinPlacasReais) : 0;

  // turnos: cada turno = 8h como padrão (ajuste depois se quiser)
  const minutosDisponiveis = turnos.length * 8 * 60 - (refeicao ? (turnos.length * 30) : 0);

  const [h, m] = horaInicio.split(":").map(Number);
  const inicio = new Date();
  inicio.setHours(h, m, 0, 0);

  const fim = new Date(inicio.getTime() + minutosNecessarios * 60000);

  const fmt = (d) => d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

  document.getElementById("resultadoPCP").innerHTML = `
    <div class="alert alert-light border mb-0">
      <div><strong>Restante:</strong> ${restante} placas</div>
      <div><strong>Meta/hora:</strong> ${metaHora} placas (blank: ${blank})</div>
      <div><strong>Tempo estimado:</strong> ${Math.ceil(minutosNecessarios)} min</div>
      <div><strong>Previsão de término:</strong> ${fmt(fim)}</div>
      <hr class="my-2">
      <div class="text-muted" style="font-size: 13px;">
        Minutos disponíveis (estimado): ${minutosDisponiveis} min · Turnos selecionados: ${turnos.join(", ") || "—"}
      </div>
    </div>
  `;
}
