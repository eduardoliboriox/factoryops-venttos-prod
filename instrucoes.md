### Objetivo - (tarefas para você executar, aplicando com CLAUDE.md)

### 1. Como funciona o planejamento.
* na pagina, eu vou ver "Fila de produção" o que tem produzido e como está a quantidade, de acordo com o setor para onde eu for planejar vai fazer diferença. Por exemplo: tem 500 placas prontas em uma op de um modelo como o 79037313, o que eu preciso pegar é eu tenho que eu so tenho 500, se eu for planejar no 1 turno, desde qual horario ? digamos que seja 07:00 às 08:00 que é a primeira hora de produção, que vou rodar na linha IM-01 que percente a setor IM, e um ponto importante é saber a meta hora do modelo em questão, normalmente eu buscaria a informação na pagina em FUNCIONALIDADES/ e pagina IM/PA, porque é onde ficam os modelos cadastrados, lá teria a meta por hora, contudo, caso la não tem cadastro de modelo onde mostraria a meta hora, eu estando la na pagina planejamento eu tenho que prosseguir com o planejamento assim mesmo, ou seja, eu vou dizer qual a meta hora, que vamos dizer que é 80 por hora desse modelo.
* Eu digito que quero produzir os 500, agora isto vai ser distribuido no plnao de voo, de acordo com a hora e paradas de linhas, por exemplo. 
intervalo 1 é às 10:00 às 11:00
intervalo 2 é às 13:00 às 14:00
hoje é segunda feira, tem ginastica no 08:00 às 09:00. 

07:00 às 08:00 no primeiro horario, vamos considerar que eles não receber a linha já rodando, vai ser necessário fazer setup para o modelo, gastaram 30 minutos de setup padrao im/pa. nos outros 30 minutos restantes de produção fizeram 40 placas, exatamente a metade da meta hora. 
08:00 às 09:00  dia de ginastica, é está configurado na parada de linha para esta linha que é 10 minutos, 60 - 10 = 50 minutos de produção. considerando a meta hora é 66 placas para 50 minutos.
09:00 às 10:00  aqui é um horario cheio, normal de 80 placas no meta hora. até agora eu tenho 40+66+80=186, como sao 500 o objetivo, o sistema deve continuar.
10:00 às 11:00  aqui é o intervalo 1 deles. mais um horario onde o maximo para produzir é 50 minutos = 66 placas
11:00 às 12:00  aqui é um horario cheio, normal de 80 placas no meta hora.
12:00 às 13:00  aqui é um horario cheio, normal de 80 placas no meta hora.
13:00 às 14:00  aqui é o intervalo 2 deles. mais um horario onde o maximo para produzir é 50 minutos = 66 placas
14:00 às 15:00  até aqui eu estou com 478 placas, tenho que produzir somente mais 22 para completar 500 placas que tem disponivel. eu vou usar somente 17 minutos para produzir 22 placas. entao sobrou 43 minutos nesse horario, que eu vou obvio fazer setup para outro modelo, gastando mais 30 minutos, e vai ficar 13 minutos de produção, mas de outro modelo, onde vou ter que saber a meta hora para poder dizer quantas placas do outro modelo produzem em 13 minutos
15:00 às 16:00
16:00 às 16:48

