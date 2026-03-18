### Objetivo - (tarefas para você executar, aplicando com CLAUDE.md)

### 1. Adequação de documento real referente app/templates/producao
* na página app/templates/producao/limpeza_stencil.html, alguns pontos terão como base a página app/templates/producao/medicao_pasta_solda.html, como select "setor" conectado com select "linha". Os campos Cliente (Customer), deve ser em letra maiuscula obrigatorialmente. 
* no campo "modelo" que tem dentro Registros por Horário tbm deve ser obrigatorio ser mauisculo. no campo "fase" é um select com select "-", "TOP", "BOTTOM".
* no campo "status" select com OK ou NG
* no campo visto (pic) é um campo para assinatura, deve ser igual ocmo é na página app/templates/producao/medicao_pasta_solda.html, tbm precisa pegar o mesmo conceito de que o documento tem id, e que precisamos poder carregar o mesmo documento com o id, para continuar fazer o controle de limpeza de stencil até o final do turno. a assinatura do é da mesma forma, icone de caneta, aperta, digita matricula, e confirma, eu gosto que tem o titulo lider de Produção (production Leader) e pra supervisor tbm, a unica diferença de como fazem, é que vai ser assinatura digital, quando assinarem vai paracer o user_name   
