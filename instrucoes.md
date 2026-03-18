### Objetivo - (tarefas para você executar, aplicando com CLAUDE.md)

### 1. Adequação de documento real referente app/templates/producao
* na página app/templates/producao/medicao_pasta_solda.html, o documento que o sistema coloca para impressão está perfeitamente ajustado a "frente" e o "verso" está quase perfeito.
* na pagina "verso", a coluna "DIA", foi preenchida com a data do documento, eu não quero seja preenchida nessa caso no verso, porque não houve problema e não teve plano de ação, mas quando houver, a data precisa ser formato para dd-mm-yyyy, no documento verso saiu 2026-03-18 então foi o padrão yyyy-mm-dd. Ainda falando em relação ao pagina verso do documento, precisa houver um conexão com o compo "Plano de ação", o usuario responsavel, digita o id do documento, ai este preenche os campos referente ao plano de voo, ai os dados vão servir para preencher o verso daquele determinado documento. Eu acredito que seja assim, não sei ao certo o sentido do plano de voo, mas vamos fazer desse jeito.
  
### 2. Letra maiuscula em Modelo (model) em app/templates/producao/medicao_pasta_solda.html
* o campo modelo (model) deve ser letra maiuscula, mesmo que o usuario tente colocar minuscula, porque existe modelos com letra e numero, então, melhor ter uma proteção.

### 3. 
