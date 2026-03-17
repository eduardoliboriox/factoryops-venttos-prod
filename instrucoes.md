### Objetivo - (tarefas para você executar, aplicando com CLAUDE.md)

### 1. Adequação de documento real referente app/templates/producao
* na página app/templates/producao/medicao_pasta_solda.html, vamos ajustar o documento controle de medição de altura de pasta de solda/adesivo. A primeira melhoria, é ter um botão select setor e outro conectado com select de linh, eu tenho as linhas que existe no app/repositories/production_lines_repository.py:
      defaults = {
        "IM": ["IM-01", "IM-02", "IM-03", "IM-04", "IM-05", "IM-06", "IM-07"],
        "PA": ["IP-COM", "PA-01", "PA-03", "PA-04", "PA-07", "PA-08", "PA-09", "PA-13", "WIFI"],
        "PTH": ["ADE-01", "AXI-01", "AXI-02", "AXI-03", "JUM-01", "JUM-02", "RAD-01", "RAD-02", "RAD-03", "ROU-01", "ROU-02", "ROU-03", "ROU-04"],
        "SMT": ["SMT-01", "SMT-02", "SMT-03", "SMT-04", "SMT-05", "SMT-06", "SMT-07", "SMT-08", "SMT-09"],
    }
com o select eu quero fazer com os usuarios não escrevam o nome da linha errado.
* coloque sp. Stencil (Thickness) e Tolerância (Tolerance) perto, são campos relativos, precisam fica perto um do outro.
* Este documento que ajustamos ajustando, pode acontecer de precisar imprimir, então temos que ter um botão para imprimir para os prontos, o botão dever ficar la entao aparece para consultar o controle de medição.
* está faltando um campo com visto do operador(a) abaixo "(Operator Signature)" e outro com campo Visto do(a) lider "(Leader Signature)" porque em cada horáior um dos operadores da linha vai fazer as medição e me assinaturia lá em baixo, no caso estamos melhorando a forma como eles trabalham na fabrica, de papel e caneta para algo digital, sistema, os operadores fazem as medições, e a campo de assinatura vai ser da seguinte forma, vai ficar um campo na tela para o usuario logado digitar a senha de acesso dela, ele digita no campo e apertar confirmar, se tiver correto, o botao de confirmar some e ficar somente o user_name do referido usuario, como exemplo eduardo.liborio. assim como o lider que é outro usuario tbm vai logar no sistema, vai procurar aquele controle de medicao, vai entrar no documento view com opções de alteração e vai assinatura tbm. O diferencial de ser sistema, é que eu quero poder saber a hora exato de cada usuario fez as medições, que ele assinou digitalmente as medições em cada horario. 
* um detalhe importante entre o que está na tela do sistema e como está no documento real é que a ordem das colunas que eu estou vendo aqui no documento real em uma parte está diferente da tela: no documento está
  FRONT E do lado direito "Menor valor" abaixo em ingles (smaller value) e abaixo disto  E do lado direito "Pico" abaixo em ingles (Peak)
  REAR E do lado direito "Menor valor" abaixo em ingles (smaller value) e abaixo disto  E do lado direito "Pico" abaixo em ingles (Peak)

mas no sistema está:
FRONT
FRONT
FRONT
FRONT
ai depois
REAR
REAR
REAR
REAR
eu acho que vao estranhar por está diferente.

  
