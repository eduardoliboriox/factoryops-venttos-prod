### Objetivo - (tarefas para você executar, aplicando com CLAUDE.md)

### 1. Adequação de documento real referente app/templates/producao
* na página app/templates/producao/medicao_pasta_solda.html, o documento que o sistema coloca para impressão está perfeitamente ajustado a "frente", contudo, existe o "verso" dessa mesma página, que deve seguir o mesmo padrão, justamente porque a escala, formato, a pagina da frente está perfeita.
* um pequeno ajuste, simples de ser resolvido é que na página de impressao abaixo do id do documento fica uma data, que é a mesma data que já existe no documento, portanto, uma duplicidade, temos que remover a data que fica abaixo do id.
* a pagina de "verso" da pagina de app/templates/producao/medicao_pasta_solda.html, é a pagina app/static/images/debug/controle-de-medicao-da-altura-da-pasta-de-pastas-adesivo-paisagem-verso.jpeg, porem eu não sei como vamos correlacionar o plano de ação com um determinado documento controle de medição, eu sei que o documento tem id, mas aqui na fabrica, quase não veja esssa parte de verso sendo usada, mas vamos fazer ter no verso.

### 2. Somente letra maiuscula para Cliente (customer) em app/templates/producao/medicao_pasta_solda.html
* na página app/templates/producao/medicao_pasta_solda.html, eu quero garantir que as pessoas não escrever o nome do cliente em letra maiuscula. 
