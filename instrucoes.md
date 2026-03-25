### Objetivo - (tarefas para você executar, aplicando com CLAUDE.md)

### 1. Saldo Considerando fases no smt
* na pagina controle de ops, eu tenho somente uma op cadastrado, roteiro padrão:
EBRTP602003	1	SMD	AMBAS	CONJUNTO 9 - PB320	PLACA DE CIRCUITO IMPRESSO MONTADA DE USO EM INFORMÁTICA	5	5000	0	5000	—	Aberta	
EBRTP602002	1	IM	AMBAS	CONJUNTO 9 - PB320	PLACA DE CIRCUITO IMPRESSO MONTADA DE USO EM INFORMÁTICA	5	5000	0	5000	—	Aberta	
EBRTP602001	1	PTH	AMBAS	CONJUNTO 9 - PB320	PLACA DE CIRCUITO IMPRESSO MONTADA DE USO EM INFORMÁTICA	5	5000	0	5000	—	Aberta
* Agora vou na pagina de apontamento e busco uma produção do mesmo modelo:
  2026-03-25	1º Turno	SMD	SMD-05	CONJUNTO 9 - PB 320	HARMAN DA AMAZONIA INDUSTRIA ELETRONICA E PARTICIPACOES LTDA	348	btn vincular
  contudo, apesar de ter vindo como 348, o sistema de onde eu pego a informação não separa fase, então eu sei porque mandaram o quadro de produção que é 200 da fase top e 148 da fase bottom.
eu vou abrir com o botão "vincular" e vou lançar o vinculo de 200 na fase top, como a parte do SMD é especial em relação aos demais roteiros de setor, a op que é de 5000, considerando que nesse caso o modelo é top e bottom, como mostra la na pagina controle de ops, eu vou abrir o vincular, vou marcar top, vou escolher a op, e vou vincular, o saldo para top deve ser 4.800, mas quando eu abrir o vincular e selecionar BOTTOM, deve está com 5000 porque eu ainda não gastei nenhum saldo bottom. depois que eu vincular top, vou vincular bottom. mas não está pegando. 
