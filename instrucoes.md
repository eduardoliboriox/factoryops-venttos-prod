### Objetivo - (tarefas para você executar, aplicando com CLAUDE.md)

### 1. Notificação push - novos usuarios
* eu quero ser notificado quando alguem solicitar acesso ao sistema, quando solicitarem, vao está la aguardando aprovação, mas sem um alerta eu nem vou saber que alguem solicitou. configure uma notificação push, e quando o usuario é aprovado, notifique o solicitante da aprovação ou negação ao sistema.

### 2. Corrigir dados 2° turno coletados. 
* eu achei uma falha na organização dos dados coletados na pagina [produção coletada](https://web-production-457281.up.railway.app/pcp/producao-coletada), mas o erro é somente para dados do 2° turno e causa é o entendimento do horario de expediente do turno, o segundo turno trabalha de 16:48 às 02:35, vamos dar um exemplo ontem, era dia 25/03/2026 , o segundo turno começou nesse dia e terminou as 02:35 que já era 26/03/2026, até essa parte o sistema e organização de dados entende, porem no caso do segundo turno é ele está misturando na produção do dia 25/03/2026 a 26/03/2026 o que teve entre 00:00 as 02:35 que era da producao do dia anterior, 24/03/2026 a 25/03/2026, com esse problema os dados da produção do segundo turno estarão sempre erradas, com um valo a mais, porque tem incluido o que deverua ser considerado do dia anterior. No turno do 1° turno não acontece esse tipo de problema porque tudo inicia a acaba no mesmo dia, nao tem erro.

### 3. Bug do select de linha da pagina planejamento.
* Ao entrar na pagina https://web-production-457281.up.railway.app/pcp/planejamento, existe um botão chamado "novo", ele abre um modal para criarmos um novo planejamento. Infelizmente uma coisa não está funcionando, nesse modal tem um campo de turno, que abre normal, o select funciona, porem o outro campo "linha" não mostra as linhas correspondentes ao setor selecionado no select turno. Os dados devem vir da pagina https://web-production-457281.up.railway.app/config/linhas, onde eu peguei a lista com dados as linhas que existem e separei onde cada linha pertence em relação ao setor. Eu vou mandar um imagem para debug de como está na tela,  

