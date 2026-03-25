### Objetivo - (tarefas para você executar, aplicando com CLAUDE.md)

### 1. Melhoria na pagina producao coletada
* como pretendo usar os dados da pagina producao coletada, um dos dados que tem no historico

Data	Setor	Linha	Turno	Modelo	Família	Início	Fim	Produção	Perda	Defeitos	Parada	Observação	Coletado em
2026-03-24	IM	IM-03	1º Turno	A29659515	ELECTROLUX DO BRASIL S/A	07:00	08:00	180	70	0	—	—	25/03 00:36
2026-03-24	IM	IM-03	1º Turno	A29659515	ELECTROLUX DO BRASIL S/A	08:00	09:00	250	50	0	—	—	25/03 00:36
2026-03-24	IM	IM-03	1º Turno	A29659515	ELECTROLUX DO BRASIL S/A	09:00	10:00	204	38	0	—	—	25/03 00:36
2026-03-24	IM	IM-03	1º Turno	A29659515	ELECTROLUX DO BRASIL S/A	10:00	11:00	107	0	0	—	—	25/03 00:36
2026-03-24	IM	IM-03	1º Turno	A29659515	ELECTROLUX DO BRASIL S/A	11:00	12:00	48	0	0	—	—	25/03 00:36
2026-03-24	IM	IM-03	1º Turno	79037313	CLIMAZON INDUSTRIAL	13:00	14:00	250	250	4	—	—	25/03 00:36
2026-03-24	IM	IM-03	1º Turno	79037313	CLIMAZON INDUSTRIAL	14:00	15:00	500	0	0	—	—	25/03 00:36
2026-03-24	IM	IM-03	1º Turno	79037313	CLIMAZON INDUSTRIAL	15:00	16:00	417	0	0	—	—	25/03 00:36
2026-03-24	IM	IM-03	1º Turno	79037313	CLIMAZON INDUSTRIAL	16:00	16:48	415	0	0	—	—	25/03 00:36

* eu quero que crie a pagina Apontamento, pertence ao menu PCP, lá eu vou pegar o resumo da combinação de dia + turno + modelo + linha, passando pelo exemplo da linha 3 que eu coloquei acima, vai ser
  24-03-2026-1º Turno-A29659515-IM-03 = 789 (corresponde as quantidade de producao desse filtro em especifico)
  24-03-2026-1º Turno-79037313-IM-03 = 1.582
  vai que vai aparecer na pagina de apontamento, ai os PCPs da empresa vao ter ao lado disto alguns botões onde eles vao vincular um op existente aquela determinada producao, E QUANDO ELES fizerem isto, a na op tem um campo chamado PRODUZIDO que nao foi colocado no campo da pagina de op, a pessoa cadastra a op, tem quantidade e tem um campo chamado Produzido ESSE PRODUZIDO é a mesma coisa que quantidade da op, mas de acordo com o apontamente pcp vai diminuir até acabar o saldo
