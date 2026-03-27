document.addEventListener("DOMContentLoaded", () => {

  const zipInput = document.getElementById("zip_code");

  if (!zipInput) return;

  zipInput.addEventListener("blur", async () => {

    const cep = zipInput.value.replace(/\D/g, "");

    if (cep.length !== 8) return;

    try {
      const response = await fetch(`https://viacep.com.br/ws/${cep}/json/`);
      const data = await response.json();

      if (data.erro) {
        alert("CEP não encontrado");
        return;
      }

      document.getElementById("street").value = data.logradouro || "";
      document.getElementById("neighborhood").value = data.bairro || "";
      document.getElementById("city").value = data.localidade || "";
      document.getElementById("state").value = data.uf || "";

    } catch (error) {
      console.error("Erro ao consultar CEP", error);
    }

  });

});
