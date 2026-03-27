### Objetivo - (tarefas para você executar, aplicando com CLAUDE.md)

### 1. Documento Plano de voo
* Na pagina https://web-production-457281.up.railway.app/pcp/planejamento, quando se cria um plejamento, vamos está criado alem do planejamento o Plano de Voo, este documento ele tem um layout, um formato que as pessoas da empresa estão acostumados, mas ainda bem com alguns erros simples de calculo e organização que neste sistema não vai acontecer. Coloquei a imagem de debug de uma plano de voo deles  app/static/images/debug/modelo-plano-de-voo.jpeg.
* Em relação a erro no documento deles, o Cliente/Customer sempre vem como "DESCONHECIDO" que na verdade é o resumo do nosso dados FAMILIA, no exemplo de familia de um modelo como HARMAN DA AMAZONIA INDUSTRIA ELETRONICA E PARTICIPACOES LTDA, o Cliente é "HARMAN".
* eles sempre erram na parte tempo e meta/h, porque quando tem que calcular quando de placa meta/h é em x minutos as vezes ficam errado, eu tenho parte no sistema que tem calculadora pra isto https://web-production-457281.up.railway.app/smt/calcular .

### 2. Webscryping de Modelos / Produtos cadastrados do sistema INPUT.
* quero proveitar a base de informação de modelos que o sistema INPUT da empresa tem, vamos usar o webscryping para puxar os dados, estão http://192.168.1.35:3000/produtos, vamos organizar para não atrapalhar a estrutura que já existe para produção coletada, a pagina para pegar os produtos é igual, so muda o que vamos pegar de dados. 
