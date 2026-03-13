1. Refatoração do menu desktop - mantendo menu desktop na esquerda.
   Somente para desktop o menu passaria a ser Funcionalidades - Produção - Engenharia - PCP - `Suporte - Minha conta  e a parte de {% block page_title %} e {% endblock %} continuaria normal como e btn voltar e etc, user_name logado - btn icone (sair)`. Ao clicar no botão "Funcionalidades" abre um menu listado para abaixo  (mesmo layout do antigo menu sidebar) que vai conter, Cadastro (parte "Novo Modelo" que é conteudo que existe na página app/templates/cadastro.html), Cálculos, IM/PA, SMT, PTH, VTT. Ao clicar no botão "Engenharia" abre um menu listado para abaixo  (mesmo layout do antigo menu sidebar) que vai conter, Estudo de tempo, Folha de cronometragem (parte do conteudo que existe na página app/templates/cadastro.html). Ao clicar no botão "PCP" abre um menu listado para abaixo  (mesmo layout do antigo menu sidebar) que vai conter, Controle de OPs, Planejamento, Entregas. Perceba que alguns páginas já existe o conteudo e funcionalidade, estamos apenas refatorando de lugar, em relação às páginas que ainda não existe o conteudo, deixar a pagina e caminho pronto, dentro o conteudo "em construção". Eu esqueci de avisar que "Minha conta" é o que atualmente é meu perfil (myperfil.html). 

      quando expande fica assim
      Funcionalidades
       cadastro >
       cálculos >
       IM/PA >
       SMT >   
       PTH >
       VTT > 

      quando expande fica assim
      Produção 
       Controle de medição da altura da pasta de solda/adesivo >
       Checklist de verificação de linha >
       Controle de limpeza do stencil > 

      quando expande fica assim
      Engenharia
       Estudo de tempo >
       Folha de cronometragem >
      
      quando expande fica assim
      PCP
       Controle de OPs >
       Planejamento >
       Entregas >


NO {% block page_title %} e {% endblock %}, adicionar:
      quando expande fica assim
      Suporte 
       Centro de conhecimento >
       Ouvidoria > 
       Suporte Especializado > 
      
      quando expande fica assim
      Minha conta
       conteudo de myperfil.html 
 
1. Refatorar a estrutura mobile.
   Após a refatoração do menu desktop e suas consequencias de ajustes de páginas, quem estiver acessando o sistema através do celular também deve ter uma experiência de uso profissional e adequada.

2. No botão "Suporte", ao clicar no botão "Suporte" abre um menu listado para abaixo que vai conter, Centro de conhecimento (que é como um FAQ de perguntas e respostas de coisas possivelmente perguntadas por usuários), Ouvidoria, Suporte Especializado (abertura de chamado, como um chat, onde a chat destino é a pessoa responsavel como sistema (no caso vai ser o desenvolvedor).
   dentro de ouvidoria deve ter:
   Reclamação → problema
   Sugestão → melhoria
   Elogio → reconhecimento
   Denúncia → irregularidade
   Solicitação → pedido de ação

3. Faça uma análise em relação a segurança de dados, criptografia, brecha em códigos, quero manter uma boa segurança em meu sistema.
   
4. Caso um usuário já seja cadastrado no sistema, onde no momento em que ele se cadastrou usou as formas normais de cadastro que são as páginas app/templates/auth/register.html (desktop) e app/templates/auth/mobile/register_form.html (mobile), mas se ele já tem cadastro, seria legal ele poder se logar com google ou github já que temos os botões e funcionalidades para isto, porque ao logar com outra forma, o sistema vai reconhecer nome completo, email, telefone ou algum dado desse tipo, eu acredito. Mas infelizmente está dando erro:
   logs de erro no railway
   Starting Container
[2026-03-10 23:38:48 +0000] [1] [INFO] Starting gunicorn 22.0.0
[2026-03-10 23:38:48 +0000] [1] [INFO] Listening at: http://0.0.0.0:8080 (1)
[2026-03-10 23:38:48 +0000] [1] [INFO] Using worker: gthread
[2026-03-10 23:38:48 +0000] [2] [INFO] Booting worker with pid: 2
[2026-03-10 23:38:48 +0000] [3] [INFO] Booting worker with pid: 3
Traceback (most recent call last):
  File "/app/.venv/lib/python3.12/site-packages/flask/app.py", line 1473, in wsgi_app
    user = get_user_by_provider(provider, provider_id)
    response = self.full_dispatch_request()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/.venv/lib/python3.12/site-packages/flask/app.py", line 882, in full_dispatch_request
    rv = self.handle_user_exception(e)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/.venv/lib/python3.12/site-packages/flask/app.py", line 880, in full_dispatch_request
    rv = self.dispatch_request()
         ^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/.venv/lib/python3.12/site-packages/flask/app.py", line 865, in dispatch_request
    return self.ensure_sync(self.view_functions[rule.endpoint])(**view_args)  # type: ignore[no-any-return]
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/app/auth/routes.py", line 167, in github_callback
    user_data = get_or_create_user(profile, "github")
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/app/auth/service.py", line 39, in get_or_create_user
[2026-03-11 00:01:11,568] ERROR in app: Exception on /auth/github/callback [GET]
psycopg.errors.UndefinedFunction: operator does not exist: character varying = integer
LINE 3:                 WHERE provider=$1 AND provider_id=$2
                                                         ^
HINT:  No operator matches the given name and argument types. You might need to add explicit type casts.
  File "/app/app/auth/repository.py", line 44, in get_user_by_provider
    cur.execute(
  File "/app/.venv/lib/python3.12/site-packages/psycopg/cursor.py", line 117, in execute
    raise ex.with_traceback(None)
  File "/app/.venv/lib/python3.12/site-packages/flask/app.py", line 865, in dispatch_request
    return self.ensure_sync(self.view_functions[rule.endpoint])(**view_args)  # type: ignore[no-any-return]
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/app/auth/routes.py", line 167, in github_callback
    user_data = get_or_create_user(profile, "github")
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/.venv/lib/python3.12/site-packages/flask/app.py", line 880, in full_dispatch_request
  File "/app/.venv/lib/python3.12/site-packages/flask/app.py", line 882, in full_dispatch_request
    rv = self.dispatch_request()
         ^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/app/auth/service.py", line 39, in get_or_create_user
    rv = self.handle_user_exception(e)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
[2026-03-12 23:37:19,423] ERROR in app: Exception on /auth/github/callback [GET]
    user = get_user_by_provider(provider, provider_id)
Traceback (most recent call last):
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/.venv/lib/python3.12/site-packages/flask/app.py", line 1473, in wsgi_app
    response = self.full_dispatch_request()
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/app/auth/repository.py", line 44, in get_user_by_provider
    cur.execute(
  File "/app/.venv/lib/python3.12/site-packages/psycopg/cursor.py", line 117, in execute
    raise ex.with_traceback(None)
psycopg.errors.UndefinedFunction: operator does not exist: character varying = integer
LINE 3:                 WHERE provider=$1 AND provider_id=$2
                                                         ^
HINT:  No operator matches the given name and argument types. You might need to add explicit type casts.

e na tela da pagina aparece a seguinte mensagem: 
   Internal Server Error
   The server encountered an internal error and was unable to complete your request. Either the server is overloaded or there is an error in the application.
a mesma mensagem ao tentar logar com google e logar com github  

5. Refatoração dos tipos de usuários e suas regras.
   na página app/templates/auth/users_all.html e seus respectivos arquivos mostram que existe os tipos de usuários "sem alteração" que é usuário comum, "usuário bloqueado" que não pode ter acesso a nada, "Tornar Admin" que são os administradores e tem uma regra especial para o primeiro admin que é o dono e não pode ser rebaixado nem por outros admin. O que eu quero alterar é ter uma opção que exclua o usuário, delete até do banco, mas sem afetar dados antigos. E aplicar regras de exibição de conteudo/pagina. Não trata-se que o usúario não possa ver todas as páginas, ele até pode ver, mas não entra em páginas não autorizadas, porque dá um erro "Não autorizado ou fora da abrangência de perfil", com exceção das páginas de app/templates/auth/users_all.html e app/templates/auth/users_admin.html que somente são visiveis para usuários de perfil administrador. Vamos lá as regras, as regras serão de acordo com "setor" produção, engenharia e etc.
eu vou configurar essa parte depois, entao, permita que todos acessem todas as paginas no momento. 
   De acordo com os setores:
          <option>Administração</option>               
          <option>Direção</option>
          <option>Engenharia</option>              
          <option>Estoque</option>
          <option>Logística</option>
          <option>Manutenção</option> 
          <option>Recursos Humanos</option> 
          <option>Serviços Gerais</option>         Provavelmente não vai precisar usar o sistema, não tem acesso a nada no momento.
          <option>Qualidade</option>  
          <option>PCP</option>
          <option>Produção</option>
          <option>TI</option>                      
Existem itens e funcionalidades que não precisa dizer que tem acesso porque é direito de todo usuario, como minha conta, suporte.

7. Estruturação e politica de backup
   Assim como existe página app/templates/auth/users_all.html e app/templates/auth/users_admin.html, é necessário ter a página de backup, uma automação da realização de backup do banco de dados do sistema que atualmente é RAILWAY, a interface permite que o usuário administrador possa dizer qual banco, passo o caminho conect do postregres, escolher a frequencia de como o backup é realizado, diário, semanal, mensal, bimestral, anual, e escolher a hora. com tudo configurado ter uma interface mostrando logs de sucesso/erro, retenção automática de 30 dias, histórico completo. usando o psql, cmd, e com o codigo do banco é possivel. Caso o sistema ainda não tenha a funcionalidade, faz-se necessário refatorar e criar. 
   exemplo:
   PSQL Path: C:\Program Files\PostgreSQL\18\bin\psql.exe
   Public Network > Connection URL: postgresql://postgres:BBxAZvsZUNZDwUhMjUtNSsgDoqskKTwK@caboose.proxy.rlwy.net:11094/railway
   entao, eu sei que se eu fosse conectar no cmd psql seria  "C:\Program Files\PostgreSQL\18\bin\psql.exe" "postgresql://postgres:BBxAZvsZUNZDwUhMjUtNSsgDoqskKTwK@caboose.proxy.rlwy.net:11094/railway", agora, para fazer o backup é dump ou algo assim.

   Padrão Executação: select diário, semanal, mensal, bimestral, anual        Horário: relogio
