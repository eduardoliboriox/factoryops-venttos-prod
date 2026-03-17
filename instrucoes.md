### Objetivo - (tarefas para você executar, aplicando com CLAUDE.md)

### 1. Ajuste nas formas de login
* na página app/templates/auth/login.html (desktop) e app/templates/auth/mobile/login_choice.html (mobile), eu quero poder logar com google e github, a politica é a seguinte, o usuário vai se cadastrar no sistema através das páginas app/templates/auth/register.html (desktop) e app/templates/auth/mobile/register_form.html (mobile), ainda precisa ser aprovado por administrador o que é padrão, porém, depois está aprovado seu acesso no sistema, o usuário pode ser logar com google ou github normalmente, é dá pra resolver o usuario pelo nome completo, pelo email, então a forma de login é permitida. Atualmente, está dando "erro ao autenticar com google" e logar com github já está funcionando.

### 2. Ajuste do posicionamento da mensagem flash na página app/templates/auth/mobile/login_choice.html (mobile)
* quando um usuário tenta se logar na pagina app/templates/auth/mobile/login_form.html, caso algo dê erro ele volta para a pagina app/templates/auth/mobile/login_choice.html (mobile) e aparece uma mensagem flash que deu erro, porém, não importa qual seja mensagem, a posição onde ela aparece está incorreta, está aparecendo na esquerda onde tem os botões de "Cadastrar-se" e "Entrar" e tbm tbm os caminhos para as página privacy e cookies, quando a mensagem aparece flash na tela ela empurra os itens, quebra o visualmente, o que deveria acontecer é qualquer mensagem flash nesse caso, deve aparecer um pouco para cima do botão "Cadastrar-se", para evitar de quebrar o visual da tela.

### 3. Atualização padrão do sistema, de acordo com o CLAUDE.md
* eu tenho uma politica bem definida para senhas/segurança, caso ainda não esteja em funcionamento, deve ser aplicado ao sistema.

### 4. Adequação de documento reais referente app/templates/producao
* Os documentos que constam dentro da pasta/diretorio app/templates/producao, precisam ser adequados ao formato real dos documentos, eu coloquei os documentos reais, frente e verso em alguns caso, na pagina app/static/images/debug, eu ainda vou explicar detalhamente sobre cada um deles, mas primeira vamos esboçar e aplicar esse ajustes. 
