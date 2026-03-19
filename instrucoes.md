### Objetivo - (tarefas para você executar, aplicando com CLAUDE.md)

### 1. Adequação de documento real referente app/templates/producao
* na página app/templates/producao/limpeza_stencil.html, tem um botão "carregar" ao lado de "passo 1", quando abre o campo para digitar , se colocar 1 e carregar vai dar certo, porem, o id do documento é  LS-1-2026, e nem dar pra digitar isto tudo lá, quando verem id  LS-1-2026 , mas so precisa digitar 1, vao achar estranho, precisamos ajustar isto. No campo onde pede pra digitar, o campo já precisa saber que é obrigatorio o LS- depois o usuario digita o id, ai depois aparece automaticamente o -2026, que no caso referente o ano atual.
* o pessoal da produção faz um documento por modelo, então, na parte de Registros por Horário, quando ele digitar o modelo, já vamos saber qual modelo ele vai passar nos outros horários tbm, vamos poder repetir, mas essencial que seja feito com inteligencia porque não quero que apareça automaticamente o modelo quando nao foi feita a limpeza do stencil em determinado horario, portanto, vai aparecer o modelo automaticamente a partir do 2 horario se o operador começar a digitar o Horário Início (Start time), ai o campo modelo vai mostrar o modelo que foi colocado no campo no 1 horario.

### 2. Consulta com formato padrao. em app/templates/producao/limpeza_stencil.html
* tem uma parte que tem o botao consultar, fica ao lado de novo registro, a pagina consultar deve ser igual a pagina consultar da app/templates/producao/medicao_pasta_solda.html, com select do setor e linha 
