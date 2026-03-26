### Objetivo - (tarefas para você executar, aplicando com CLAUDE.md)

### 1. Corrigir dados 2° turno coletados. 
* eu achei uma falha na organização dos dados coletados na pagina [produção coletada](https://web-production-457281.up.railway.app/pcp/producao-coletada), mas o erro é somente para dados do 2° turno e causa é o entendimento do horario de expediente do turno, o segundo turno trabalha de 16:48 às 02:35, vamos dar um exemplo ontem, era dia 25/03/2026 , o segundo turno começou nesse dia e terminou as 02:35 que já era 26/03/2026, até essa parte o sistema e organização de dados entende, porem no caso do segundo turno é ele está misturando na produção do dia 25/03/2026 a 26/03/2026 o que teve entre 00:00 as 02:35 que era da producao do dia anterior, 24/03/2026 a 25/03/2026, com esse problema os dados da produção do segundo turno estarão sempre erradas, com um valo a mais, porque tem incluido o que deverua ser considerado do dia anterior. No turno do 1° turno não acontece esse tipo de problema porque tudo inicia a acaba no mesmo dia, nao tem erro.

eu selecione na pagina https://web-production-457281.up.railway.app/pcp/apontamento
Data inicial
25/03/2026
Data final
25/03/2026
Setor
SMD
Linha
SMD-02
Turno
2º Turno
Data	Turno	Setor	Linha	Modelo	Família	Produção	Vínculo / OP	Ação
2026-03-25	2º Turno	SMD	SMD-02	A13445103	ELECTROLUX DO BRASIL S/A	942	
TOP
—
BOTTOM
—
2026-03-25	2º Turno	SMD	SMD-02	A13445104	ELECTROLUX DO BRASIL S/A	1.524	
TOP
—
BOTTOM
—
2026-03-25	2º Turno	SMD	SMD-02	CONJUNTO RGB - PB 320	HARMAN DA AMAZONIA INDUSTRIA ELETRONICA E PARTICIPACOES LTDA	0	
TOP
—
BOTTOM
—

2026-03-25	2º Turno	SMD	SMD-02	A13445104	ELECTROLUX DO BRASIL S/A	1.524 está correto
2026-03-25	2º Turno	SMD	SMD-02	A13445103	ELECTROLUX DO BRASIL S/A	942 está errado 
2026-03-25	2º Turno	SMD	SMD-02	CONJUNTO RGB - PB 320	HARMAN DA AMAZONIA INDUSTRIA ELETRONICA E PARTICIPACOES LTDA	0 está errado 


agora se selecionar
Data inicial
25/03/2026
Data final
26/03/2026
Setor
SMD
Linha
SMD-02
Turno
2º Turno
Data	Turno	Setor	Linha	Modelo	Família	Produção	Vínculo / OP	Ação
2026-03-26	2º Turno	SMD	SMD-02	CONJUNTO RGB - PB 320	HARMAN DA AMAZONIA INDUSTRIA ELETRONICA E PARTICIPACOES LTDA	344	
TOP
—
BOTTOM
—
2026-03-25	2º Turno	SMD	SMD-02	A13445103	ELECTROLUX DO BRASIL S/A	942	
TOP
—
BOTTOM
—
2026-03-25	2º Turno	SMD	SMD-02	A13445104	ELECTROLUX DO BRASIL S/A	1.524	
TOP
—
BOTTOM
—
2026-03-25	2º Turno	SMD	SMD-02	CONJUNTO RGB - PB 320	HARMAN DA AMAZONIA INDUSTRIA ELETRONICA E PARTICIPACOES LTDA	0	
TOP
—
BOTTOM
—
4 registros

se escolher para filtrar o dia 25/03/2026 a 25/03/2026 eu quero que apareça somente os dois de baixo.
Data inicial
25/03/2026
Data final
25/03/2026
Setor
SMD
Linha
SMD-02
Turno
2º Turno
porque apesar da produção do segundo turno ter começado no dia 25/03/2026 e terminado no dia 26/03/2026 às 02h35, na pratica ela pertence ao dia 25/03/2026. 

2026-03-26	2º Turno	SMD	SMD-02	CONJUNTO RGB - PB 320	HARMAN DA AMAZONIA INDUSTRIA ELETRONICA E PARTICIPACOES LTDA	344  
2026-03-25	2º Turno	SMD	SMD-02	A13445104	ELECTROLUX DO BRASIL S/A	1.524  

e 2026-03-25	2º Turno	SMD	SMD-02	A13445103	ELECTROLUX DO BRASIL S/A	942 não deveria aparacer pq é o foi produzido as 00:00 as 02:35 no dia 25/03/2026, mas pertence ao dia 24/03/2026, é o complemento da produção do segundo turno do dia 24/03/2026. esse entendimento do horario do turno precisa ser ajustado. senao o time PCP vai se atrapalhar com a produção. 

e ajuste a data que está 2026-03-25 ou seja yyyy-mm-dd para dd-mm-yyyy.
